import boto3
import cfnresponse
import json

grafana = boto3.client('grafana')

def handler(event, context):
    try:
        # Log the event for debugging in CloudWatch
        print(f"Received event: {json.dumps(event)}")
        
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        # Defensive access
        props = event.get('ResourceProperties', {})
        workspace_id = props.get('WorkspaceId')
        plugins = props.get('Plugins', [])

        if not workspace_id:
            raise ValueError("WorkspaceId is missing")

        grafana.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps({"plugins": {"pluginIds": plugins}})
        )
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "Success"})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
