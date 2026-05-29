import boto3, json, urllib3

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
    try:
        client = boto3.client('grafana')
        workspace_id = event['ResourceProperties']['WorkspaceId']
        
        config = {
            "plugins": {
                "pluginAdminEnabled": True,
                "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]
            }
        }
        
        # Logging the config for debugging purposes
        config_json = json.dumps(config)
        print(f"DEBUG: Configuration being sent to Grafana: {config_json}")
        
        client.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=config_json
        )
        
        cfn_send(event, context, 'SUCCESS', {"Status": "Finished"})
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        cfn_send(event, context, 'FAILED', {"Error": error_msg}, reason=error_msg)
