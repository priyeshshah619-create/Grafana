import boto3, cfnresponse, json

client = boto3.client('grafana')

def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
        
    try:
        workspace_id = event['ResourceProperties']['WorkspaceId']
        
        # Define the complete configuration object
        config_payload = {
            "plugins": {
                "pluginAdminEnabled": True,
                "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]
            },
            "unifiedAlerting": {
                "enabled": True
            }
        }
        
        print(f"Applying full configuration: {json.dumps(config_payload)}")
        
        client.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps(config_payload)
        )
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Reason": str(e)})
