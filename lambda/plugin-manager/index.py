import boto3
import cfnresponse
import json

grafana = boto3.client('grafana')

def handler(event, context):
    try:
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        workspace_id = event['ResourceProperties']['WorkspaceId']
        plugins = event['ResourceProperties']['Plugins']
        
        # In AWS Managed Grafana, plugin installation is managed via 
        # UpdateWorkspaceConfiguration or direct API calls depending on version
        # Here we use the standard SDK approach:
        grafana.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps({"plugins": {"pluginIds": plugins}})
        )
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "PluginsInstalled"})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
