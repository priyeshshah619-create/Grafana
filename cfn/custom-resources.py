import boto3
import cfnresponse

def lambda_handler(event, context):
    try:
        if event['RequestType'] == 'Create':
            client = boto3.client('grafana')
            client.update_workspace_configuration(
                workspaceId=event['ResourceProperties']['WorkspaceId'],
                configuration='{"plugins": {"pluginIds": ["grafana-piechart-panel"]}}'
            )
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
