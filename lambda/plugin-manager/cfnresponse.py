# Save this file as lambda/plugin-manager/cfnresponse.py
import json
import urllib3

SUCCESS = "SUCCESS"
FAILED = "FAILED"

def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    responseBody = {
        'Status': responseStatus,
        'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': physicalResourceId or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': responseData
    }
    json_responseBody = json.dumps(responseBody)
    http = urllib3.PoolManager()
    http.request('PUT', responseUrl, body=json_responseBody, headers={'content-type': '', 'content-length': str(len(json_responseBody))})
