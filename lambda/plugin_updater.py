import boto3, json, urllib3

http = urllib3.PoolManager()

def cfn_send(event, context, status, data, reason=None):
    response_body = {
        'Status': status,
        'Reason': reason or "Success",
        'PhysicalResourceId': event.get('PhysicalResourceId', 'PluginUpdater'),
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data
    }
    json_body = json.dumps(response_body)
    headers = {'content-type': '', 'content-length': str(len(json_body))}
    http.request('PUT', event['ResponseURL'], body=json_body, headers=headers)

def lambda_handler(event, context):
    try:
        if event['RequestType'] == 'Delete':
            cfn_send(event, context, 'SUCCESS', {})
            return
        
        client = boto3.client('grafana')
        config = {"plugins": {"pluginAdminEnabled": True, "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]}}
        client.update_workspace_configuration(workspaceId=event['ResourceProperties']['WorkspaceId'], configuration=json.dumps(config))
        
        cfn_send(event, context, 'SUCCESS', {"Status": "Finished"})
    except Exception as e:
        cfn_send(event, context, 'FAILED', {"Error": str(e)}, reason=str(e))
