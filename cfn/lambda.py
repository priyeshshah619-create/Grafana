import boto3
import json
import cfnresponse

grafana = boto3.client('managedgrafana')

def handler(event, context):
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            workspace_id = event['ResourceProperties']['WorkspaceId']
            plugins = event['ResourceProperties']['Plugins']
            
            config = {"plugins": [{"pluginId": p} for p in plugins]}
            
            grafana.update_workspace_configuration(
                workspaceId=workspace_id,
                configuration=json.dumps(config)
            )
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"Error: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
