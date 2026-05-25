import boto3
import cfnresponse

def handler(event, context):
    grafana = boto3.client('grafana')
    try:
        if event['RequestType'] in ['Create', 'Update']:
            ws = event['ResourceProperties']['WS']
            plugins = event['ResourceProperties']['Plugins']
            for plugin in plugins:
                grafana.install_plugin(workspaceId=ws, pluginId=plugin)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
