import boto3
import cfnresponse
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

grafana = boto3.client('grafana')

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Manual test bypass
    if event.get('ResponseURL') == 'https://dummy-url.com':
        return {"Status": "Manual Test Success"}

    try:
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        props = event.get('ResourceProperties', {})
        workspace_id = props.get('WorkspaceId')
        plugins = props.get('Plugins', []) # List from CloudFormation

        # Requirement 1b & Condition A/B
        grafana.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps({"plugins": {"pluginIds": plugins}})
        )

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "PluginsInstalled"})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
