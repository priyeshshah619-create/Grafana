import boto3
import cfnresponse
import json

grafana = boto3.client('grafana')

def lambda_handler(event, context):
    try:
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        props = event['ResourceProperties']
        workspace_id = props['WorkspaceId']
        plugins = props['Plugins']

        # Logic for Requirement 1b & Condition A
        grafana.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps({"plugins": {"pluginIds": plugins}})
        )

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "PluginsInstalled"})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
