import boto3
import json
import cfnresponse

def lambda_handler(event, context):
    response_data = {"Status": "Finished"}
    try:
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            return

        workspace_id = event['ResourceProperties']['WorkspaceId']
        client = boto3.client('grafana')
        
        config = {
            "plugins": {
                "pluginAdminEnabled": True,
                "pluginIds": ["grafana-piechart-panel", "grafana-clock-panel"]
            }
        }
        
        client.update_workspace_configuration(
            workspaceId=workspace_id,
            configuration=json.dumps(config)
        )
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Failure par bhi signal bhejna zaroori hai taaki stack hang na ho
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
