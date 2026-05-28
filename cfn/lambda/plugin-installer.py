import boto3, cfnresponse, json

client = boto3.client('grafana')

def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
        
    try:
        # Define the plugins you want to ensure are installed
        plugins_to_install = ["grafana-piechart-panel", "grafana-clock-panel"]
        
        # Update the workspace configuration
        client.update_workspace_configuration(
            workspaceId=event['ResourceProperties']['WorkspaceId'],
            configuration=json.dumps({
                "plugins": {
                    "pluginIds": plugins_to_install
                }
            })
        )
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"Error installing plugins: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Reason": str(e)})
