import json
import traceback
import urllib.request

import boto3
from botocore.config import Config


AWS_CLIENT_CONFIG = Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 2, "mode": "standard"})
HTTP_TIMEOUT_SECONDS = 10

grafana = boto3.client("grafana", config=AWS_CLIENT_CONFIG)


def handler(event, context):
    print(json.dumps({"message": "received custom resource event", "requestType": event.get("RequestType")}))
    props = event["ResourceProperties"]
    workspace_id = props["WorkspaceId"]
    physical_id = event.get("PhysicalResourceId") or f"grafana-sso-assignment-{workspace_id}"

    try:
        if event["RequestType"] == "Delete":
            revoke_permissions(workspace_id, props)
            send_response(event, context, "SUCCESS", {"Message": "SSO permissions revoked"}, physical_id)
            return

        grant_permissions(workspace_id, props)
        send_response(event, context, "SUCCESS", {"Message": "SSO permissions assigned"}, physical_id)
    except Exception as exc:
        print(traceback.format_exc())
        send_response(event, context, "FAILED", {"Error": str(exc)}, physical_id)


def grant_permissions(workspace_id, props):
    updates = []
    for user_id in normalize_list(props.get("AdminUserIds", [])):
        updates.append(
            {
                "action": "ADD",
                "role": "ADMIN",
                "users": [{"id": user_id, "type": "SSO_USER"}],
            }
        )
    for group_id in normalize_list(props.get("EditorGroupIds", [])):
        updates.append(
            {
                "action": "ADD",
                "role": "EDITOR",
                "users": [{"id": group_id, "type": "SSO_GROUP"}],
            }
        )
    if updates:
        grafana.update_permissions(workspaceId=workspace_id, updateInstructionBatch=updates)


def revoke_permissions(workspace_id, props):
    updates = []
    for user_id in normalize_list(props.get("AdminUserIds", [])):
        updates.append(
            {
                "action": "REVOKE",
                "role": "ADMIN",
                "users": [{"id": user_id, "type": "SSO_USER"}],
            }
        )
    for group_id in normalize_list(props.get("EditorGroupIds", [])):
        updates.append(
            {
                "action": "REVOKE",
                "role": "EDITOR",
                "users": [{"id": group_id, "type": "SSO_GROUP"}],
            }
        )
    if updates:
        grafana.update_permissions(workspaceId=workspace_id, updateInstructionBatch=updates)


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
