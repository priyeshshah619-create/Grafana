import json
import time
import traceback
import urllib.request

import boto3
from botocore.config import Config


AWS_CLIENT_CONFIG = Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 2, "mode": "standard"})
HTTP_TIMEOUT_SECONDS = 10
WORKSPACE_WAIT_SECONDS = 120
PERMISSION_WAIT_SECONDS = 120

grafana = boto3.client("grafana", config=AWS_CLIENT_CONFIG)


def handler(event, context):
    print(json.dumps({"message": "received custom resource event", "requestType": event.get("RequestType")}))
    props = event["ResourceProperties"]
    workspace_id = props["WorkspaceId"]
    physical_id = event.get("PhysicalResourceId") or f"grafana-sso-assignment-{workspace_id}"

    try:
        if event["RequestType"] == "Delete":
            send_response(event, context, "SUCCESS", {"Message": "No SSO revoke attempted during stack delete"}, physical_id)
            return

        wait_for_workspace(workspace_id)
        grant_permissions_with_retry(workspace_id, props)
        send_response(event, context, "SUCCESS", {"Message": "SSO permissions assigned"}, physical_id)
    except Exception as exc:
        print(traceback.format_exc())
        send_response(event, context, "FAILED", {"Error": str(exc)}, physical_id)


def grant_permissions_with_retry(workspace_id, props):
    deadline = time.monotonic() + PERMISSION_WAIT_SECONDS
    last_error = None
    while time.monotonic() < deadline:
        try:
            grant_permissions(workspace_id, props)
            return
        except grafana.exceptions.ValidationException as exc:
            last_error = exc
            if "UPDATING" not in str(exc):
                raise
            print(json.dumps({"message": "Workspace permissions not ready, retrying", "error": str(exc)}))
            time.sleep(10)
        except grafana.exceptions.AccessDeniedException as exc:
            raise PermissionError(
                "Unable to assign IAM Identity Center users/groups to the Managed Grafana workspace. "
                "The Lambda role needs AWSGrafanaWorkspacePermissionManagementV2 plus IAM Identity Center "
                "application assignment permissions such as sso:CreateApplicationAssignment."
            ) from exc
    raise TimeoutError(f"Workspace permissions were not ready within {PERMISSION_WAIT_SECONDS} seconds: {last_error}")


def grant_permissions(workspace_id, props):
    for user_id in normalize_list(props.get("AdminUserIds", [])):
        update_permission(
            workspace_id,
            {
                "action": "ADD",
                "role": "ADMIN",
                "users": [{"id": user_id, "type": "SSO_USER"}],
            },
        )
    for group_id in normalize_list(props.get("EditorGroupIds", [])):
        update_permission(
            workspace_id,
            {
                "action": "ADD",
                "role": "EDITOR",
                "users": [{"id": group_id, "type": "SSO_GROUP"}],
            },
        )


def revoke_permissions(workspace_id, props):
    for user_id in normalize_list(props.get("AdminUserIds", [])):
        update_permission(
            workspace_id,
            {
                "action": "REVOKE",
                "role": "ADMIN",
                "users": [{"id": user_id, "type": "SSO_USER"}],
            },
        )
    for group_id in normalize_list(props.get("EditorGroupIds", [])):
        update_permission(
            workspace_id,
            {
                "action": "REVOKE",
                "role": "EDITOR",
                "users": [{"id": group_id, "type": "SSO_GROUP"}],
            },
        )


def update_permission(workspace_id, instruction):
    for attempt in range(1, 4):
        try:
            grafana.update_permissions(workspaceId=workspace_id, updateInstructionBatch=[instruction])
            return
        except Exception as exc:
            if attempt == 3:
                raise
            print(json.dumps({"message": "Retrying Grafana permission update", "attempt": attempt, "error": str(exc)}))
            time.sleep(attempt * 5)


def wait_for_workspace(workspace_id):
    deadline = time.monotonic() + WORKSPACE_WAIT_SECONDS
    while time.monotonic() < deadline:
        response = grafana.describe_workspace(workspaceId=workspace_id)
        status = response["workspace"]["status"]
        if status == "ACTIVE":
            return
        if status in {"CREATION_FAILED", "DELETION_FAILED", "UPDATE_FAILED"}:
            raise RuntimeError(f"Workspace {workspace_id} is in terminal status {status}")
        time.sleep(10)
    raise TimeoutError(f"Workspace {workspace_id} did not become ACTIVE within {WORKSPACE_WAIT_SECONDS} seconds")


def normalize_list(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


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
    raise RuntimeError(f"Failed to send CloudFormation response after retries: {last_error}")
