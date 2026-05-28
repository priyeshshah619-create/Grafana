import boto3, cfnresponse, json
client = boto3.client('grafana')

def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
    try:
        client.update_workspace_configuration(
            workspaceId=event['ResourceProperties']['WorkspaceId'],
            configuration=json.dumps({"plugins": {"pluginIds": ["grafana-clock-panel", "grafana-piechart-panel"]}})
        )
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Reason": str(e)})
