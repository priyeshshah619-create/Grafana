import boto3, cfnresponse, json

client = boto3.client('grafana')

def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
        
    try:
        # Explicitly include both the Admin setting and the list of plugin IDs
        config = {
            "plugins": {
                "pluginAdminEnabled": True,
                "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]
            }
        }
        
        client.update_workspace_configuration(
            workspaceId=event['ResourceProperties']['WorkspaceId'],
            configuration=json.dumps(config)
        )
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Reason": str(e)})
