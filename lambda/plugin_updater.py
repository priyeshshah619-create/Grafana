import boto3
import json
import urllib3
import traceback

http = urllib3.PoolManager()

def cfn_send(event, context, response_status, response_data, reason=None):
    response_body = {
        'Status': response_status,
        'Reason': reason or "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    }
    json_response_body = json.dumps(response_body)
    headers = {'content-type': '', 'content-length': str(len(json_response_body))}
    try:
        http.request('PUT', event['ResponseURL'], body=json_response_body, headers=headers)
    except Exception as e:
        print(f"Failed to send cfnresponse: {str(e)}")

def lambda_handler(event, context):
    try:
        if event['RequestType'] == 'Delete':
            cfn_send(event, context, 'SUCCESS', {})
            return
        
        workspace_id = event['ResourceProperties']['WorkspaceId']
        client = boto3.client('grafana')
        config = {"plugins": {"pluginAdminEnabled": True, "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"] } }
        
        client.update_workspace_configuration(workspaceId=workspace_id, configuration=json.dumps(config))
        
        cfn_send(event, context, 'SUCCESS', {"Status": "Finished"})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfn_send(event, context, 'FAILED', {"Error": str(e)}, reason=str(e))
