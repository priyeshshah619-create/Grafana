import boto3
import cfnresponse
import json

def handler(event, context):
    # Condition A & B: Custom Resource to install plugins
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
    
    try:
        workspace_id = event['ResourceProperties']['WorkspaceId']
        grafana = boto3.client('grafana')
        
        # Configuration payload for plugins
        config = {
            "plugins": [
                {"pluginId": "grafana-clock-panel", "pluginVersion": "1.0.0"}
            ]
        }
        
        grafana.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps(config)
        )
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Status': 'Plugins Installed'})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
