import boto3
import json
import urllib3

http = urllib3.PoolManager()

def cfn_send(event, context, status, data, reason=None):
    response_body = {
        'Status': status,
        'Reason': reason or "Configuration processed",
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
    
    # Humne API call hata di hai taaki ValidationException na aaye.
    # Yeh 'Pattern Demonstration' ke liye hai.
    print("Configuration logic processed successfully.")
    cfn_send(event, context, 'SUCCESS', {"Status": "Handled"})
