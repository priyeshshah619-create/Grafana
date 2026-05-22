import boto3
import cfnresponse
import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # --- MANUAL TEST BYPASS ---
    # This prevents the SSLError when testing in the Lambda Console
    if event.get('ResponseURL') == 'https://dummy-url.com':
        logger.info("Manual test detected: bypassing cfnresponse.send")
        return {"Status": "Manual Test Success"}

    # --- CLOUDFORMATION CUSTOM RESOURCE LOGIC ---
    try:
        request_type = event.get('RequestType')

        if request_type == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        # Add your actual plugin management logic here
        logger.info(f"Handling {request_type} event")

        # Example logic placeholder:
        response_data = {'Message': 'Plugin operation successful'}

        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
