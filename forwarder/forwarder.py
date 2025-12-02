import os
import json
import boto3
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sns-forwarder")

app = Flask(__name__)

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
REGION = os.environ.get("AWS_REGION", "us-east-1")

try:
    sns = boto3.client("sns", region_name=REGION)
except Exception as e:
    logger.error(f"Failed to initialize SNS client: {e}")
    sns = None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/alert", methods=["POST"])
def receive_alert():
    """
    Receives the JSON payload from Alertmanager and publishes it to SNS.
    """
    if not SNS_TOPIC_ARN:
        logger.error("SNS_TOPIC_ARN is not set.")
        return jsonify({"error": "Configuration error: SNS_TOPIC_ARN missing"}), 500

    try:
        payload = request.json
        logger.info(f"Received alert payload: {json.dumps(payload)}")

        message_body = json.dumps(payload)

        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message_body,
            Subject="Prometheus Alert"
        )
        
        logger.info(f"Published to SNS: {response.get('MessageId')}")
        return jsonify({"status": "sent", "messageId": response.get("MessageId")}), 200

    except Exception as e:
        logger.error(f"Error publishing to SNS: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9087)