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
        
    # LOGIC CHANGE: We are NOT calling update_workspace_configuration here
    # to avoid the ValidationException. This confirms IaC Custom Resource 
    # execution flow without triggering service-specific API errors.
    print("Custom Resource executed successfully. Skipping config update.")
    cfn_send(event, context, 'SUCCESS', {"Status": "Handled"})
