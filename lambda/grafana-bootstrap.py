import json
import os
import time
import traceback
import urllib.error
import urllib.request

import boto3
from botocore.config import Config


AWS_CLIENT_CONFIG = Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 2, "mode": "standard"})

grafana = boto3.client("grafana", config=AWS_CLIENT_CONFIG)
secrets = boto3.client("secretsmanager", config=AWS_CLIENT_CONFIG)

MIN_RESPONSE_TIME_MS = 15000
WORKSPACE_WAIT_SECONDS = 120
PLUGIN_INSTALL_SECONDS = 75
HTTP_TIMEOUT_SECONDS = 10


def handler(event, context):
    print(json.dumps({"message": "received custom resource event", "requestType": event.get("RequestType")}))
    physical_id = event.get("PhysicalResourceId") or f"grafana-bootstrap-{event['ResourceProperties']['WorkspaceId']}"
    response_sent = False

    try:
        request_type = event["RequestType"]
        props = event["ResourceProperties"]

        if request_type == "Delete":
            send_response(event, context, "SUCCESS", {"Message": "No plugin uninstall on stack delete"}, physical_id)
            response_sent = True
            return

        workspace_id = props["WorkspaceId"]
        workspace_endpoint = normalize_endpoint(props["WorkspaceEndpoint"])
        token_secret_arn = props.get("TokenSecretArn") or os.environ["TOKEN_SECRET_ARN"]
        plugin_ids = normalize_list(props.get("PluginIds", []))
        allowed_plugin_ids = set(normalize_list(props.get("AllowedPluginIds", [])))
        validate_managed_grafana_plugins(plugin_ids, allowed_plugin_ids)

        ensure_time(context, "before waiting for Grafana workspace")
        wait_for_workspace(workspace_id, context)
        ensure_time(context, "before enabling Grafana workspace features")
        enable_workspace_features(workspace_id)
        ensure_time(context, "before creating Grafana service account token")
        token = create_or_rotate_service_account_token(
            workspace_id=workspace_id,
            name=props.get("ServiceAccountName", "automation-deployer"),
            role=props.get("ServiceAccountRole", "ADMIN"),
        )
        secrets.put_secret_value(SecretId=token_secret_arn, SecretString=token)

        installed = []
        for plugin_id in plugin_ids:
            ensure_time(context, f"before installing plugin {plugin_id}")
            install_plugin(workspace_endpoint, token, plugin_id, context)
            installed.append(plugin_id)

        send_response(
            event,
            context,
            "SUCCESS",
            {
                "WorkspaceId": workspace_id,
                "Endpoint": workspace_endpoint,
                "InstalledPlugins": ",".join(installed),
            },
            physical_id,
        )
        response_sent = True
    except Exception as exc:
        print(traceback.format_exc())
        send_response(event, context, "FAILED", {"Error": str(exc)}, physical_id)
        response_sent = True
    finally:
        if not response_sent and context.get_remaining_time_in_millis() > MIN_RESPONSE_TIME_MS:
            send_response(
                event,
                context,
                "FAILED",
                {"Error": "Custom resource exited without sending a response."},
                physical_id,
            )


def wait_for_workspace(workspace_id, context):
    deadline = time.monotonic() + WORKSPACE_WAIT_SECONDS
    while time.monotonic() < deadline:
        ensure_time(context, "while waiting for Grafana workspace")
        response = grafana.describe_workspace(workspaceId=workspace_id)
        status = response["workspace"]["status"]
        if status == "ACTIVE":
            return
        if status in {"CREATION_FAILED", "DELETION_FAILED", "UPDATE_FAILED"}:
            raise RuntimeError(f"Workspace {workspace_id} is in terminal status {status}")
        time.sleep(10)
    raise TimeoutError(f"Workspace {workspace_id} did not become ACTIVE within {WORKSPACE_WAIT_SECONDS} seconds")


def enable_workspace_features(workspace_id):
    configuration = {
        "plugins": {"pluginAdminEnabled": True},
        "unifiedAlerting": {"enabled": True},
    }
    grafana.update_workspace_configuration(
        workspaceId=workspace_id,
        configuration=json.dumps(configuration),
    )


def create_or_rotate_service_account_token(workspace_id, name, role):
    account_id = find_service_account(workspace_id, name)
    if not account_id:
        response = grafana.create_workspace_service_account(
            workspaceId=workspace_id,
            name=name,
            grafanaRole=role,
        )
        account_id = response["id"]

    token_name = f"gha-{int(time.time())}"
    response = grafana.create_workspace_service_account_token(
        workspaceId=workspace_id,
        serviceAccountId=account_id,
        name=token_name,
        secondsToLive=60 * 60 * 24 * 30,
    )
    return response["serviceAccountToken"]["key"]


def find_service_account(workspace_id, name):
    paginator = grafana.get_paginator("list_workspace_service_accounts")
    for page in paginator.paginate(workspaceId=workspace_id):
        for account in page.get("serviceAccounts", []):
            if account.get("name") == name:
                return account["id"]
    return None


def install_plugin(base_url, token, plugin_id, context):
    try:
        get_response = grafana_api("GET", f"{base_url}/api/plugins/{plugin_id}", token)
        if get_response.get("enabled") or get_response.get("state") == "installed":
            print(json.dumps({"message": "plugin already installed", "pluginId": plugin_id}))
            return
    except RuntimeError as exc:
        print(json.dumps({"message": "plugin not installed yet or catalog lookup deferred", "pluginId": plugin_id, "detail": str(exc)}))

    grafana_api("POST", f"{base_url}/api/plugins/{plugin_id}/install", token, body={})
    deadline = time.monotonic() + PLUGIN_INSTALL_SECONDS
    while time.monotonic() < deadline:
        ensure_time(context, f"while verifying plugin {plugin_id}")
        time.sleep(10)
        response = grafana_api("GET", f"{base_url}/api/plugins/{plugin_id}", token)
        if response.get("enabled") or response.get("state") == "installed":
            print(json.dumps({"message": "plugin installed", "pluginId": plugin_id}))
            return
    raise TimeoutError(f"Plugin {plugin_id} did not become installed within {PLUGIN_INSTALL_SECONDS} seconds")


def grafana_api(method, url, token, body=None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=payload,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            data = response.read().decode("utf-8")
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"Grafana API {method} {url} failed: {exc.code} {detail}") from exc


def normalize_endpoint(endpoint):
    return endpoint if endpoint.startswith("https://") else f"https://{endpoint}"


def normalize_list(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def validate_managed_grafana_plugins(plugin_ids, allowed_plugin_ids):
    if not allowed_plugin_ids:
        raise ValueError("AllowedPluginIds must not be empty. Managed Grafana cannot install arbitrary custom plugins.")
    unsupported = sorted(set(plugin_ids) - allowed_plugin_ids)
    if unsupported:
        raise ValueError(
            "Unsupported plugin IDs requested: "
            + ",".join(unsupported)
            + ". Use only vetted plugin IDs from the Amazon Managed Grafana plugin catalog and the CloudFormation allowlist."
        )


def ensure_time(context, action):
    remaining = context.get_remaining_time_in_millis()
    if remaining < MIN_RESPONSE_TIME_MS:
        raise TimeoutError(f"Not enough Lambda time remaining {action}; failing fast so CloudFormation receives a response.")


def send_response(event, context, status, data, physical_id):
    body = json.dumps(
        {
            "Status": status,
            "Reason": f"See CloudWatch Log Stream: {context.log_stream_name}",
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "NoEcho": False,
            "Data": data,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        event["ResponseURL"],
        data=body,
        method="PUT",
        headers={"Content-Type": "", "Content-Length": str(len(body))},
    )
    last_error = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS):
                print(json.dumps({"message": "sent CloudFormation response", "status": status, "attempt": attempt}))
                return
        except Exception as exc:
            last_error = exc
            print(json.dumps({"message": "CloudFormation response send failed", "attempt": attempt, "error": str(exc)}))
            time.sleep(min(attempt * 2, 5))
    raise RuntimeError(f"Failed to send CloudFormation response after retries: {last_error}")
