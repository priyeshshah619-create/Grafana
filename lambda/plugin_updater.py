import boto3
import json
import urllib3

http = urllib3.PoolManager()

def cfn_send(event, context, status, data, reason=None):
    response_body = {
        'Status': status,
        'Reason': reason or "Success",
        'PhysicalResourceId': event.get('PhysicalResourceId', 'GrafanaPluginConfig'),
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data
    }
    json_body = json.dumps(response_body)
    headers = {'content-type': '', 'content-length': str(len(json_body))}
    http.request('PUT', event['ResponseURL'], body=json_body, headers=headers)

def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        cfn_send(event, context, 'SUCCESS', {})
        return
        
    try:
        client = boto3.client('grafana')
        workspace_id = event['ResourceProperties']['WorkspaceId']
        
        # 10.4 Schema (Strict)
        payload = {
            "plugins": {
                "pluginAdminEnabled": True,
                "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]
            }
        }
        
        # API Call
        client.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps(payload)
        )
        cfn_send(event, context, 'SUCCESS', {"Status": "Finished"})
    except Exception as e:
        # Rollback se pehle reason return karo
        cfn_send(event, context, 'FAILED', {"Error": str(e)}, reason=str(e))
