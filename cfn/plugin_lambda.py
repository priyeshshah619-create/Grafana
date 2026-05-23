import boto3
import cfnresponse

def handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
    
    try:
        grafana = boto3.client('grafana')
        # Condition A: Install Plugins
        config = '{"plugins": [{"pluginId": "grafana-clock-panel", "pluginVersion": "1.0.0"}]}'
        grafana.update_workspace_configuration(
            workspaceId=event['ResourceProperties']['WorkspaceId'],
            configuration=config
        )
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
