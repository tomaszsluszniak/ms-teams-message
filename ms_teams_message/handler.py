import json
import logging

import sentry_sdk

from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.serverless import serverless_function

from azure.identity import UsernamePasswordCredential
from msgraph.core import GraphClient


with open('/var/openfaas/secrets/ms-teams-message-az-client-id', 'r') as f:
    AZ_CLIENT_ID = f.readline()
with open('/var/openfaas/secrets/ms-teams-message-upn', 'r') as f:
    UPN = f.readline()
with open('/var/openfaas/secrets/ms-teams-message-password', 'r') as f:
    PASSWORD = f.readline()
with open('/var/openfaas/secrets/ms-teams-message-sentry-dsn', 'r') as f:
    SENTRY_DSN = f.readline()

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

sentry_sdk.init(
    SENTRY_DSN, 
    traces_sample_rate=1.0,
    integrations=[sentry_logging]
)


@serverless_function
def handle(event, context):
    if (event.method == "POST"):
        credential = UsernamePasswordCredential(
            client_id=AZ_CLIENT_ID, 
            username=UPN, 
            password=PASSWORD
        )
        graph_client = GraphClient(credential=credential)

        params = json.loads(event.body.decode('utf-8'))

        errors = []
        recipient = params.get('recipient')
        message = params.get('message')

        if recipient is None:
            errors.append('The "recipient" field is required.')
        if message is None:
            errors.append('The "message" field is required.')
            
        if len(errors) > 0:   
            return {
                "statusCode": 400,
                "body": {
                    "message": ' '.join(errors)
                }
            }

        create_chat_body = {
            "chatType": "oneOnOne",
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{UPN}')"
                },
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{recipient}')"
                }
            ]
        }
        chat_obj = graph_client.post(
            '/chats',
            data=json.dumps(create_chat_body),
            headers={'Content-Type': 'application/json'}
        )
        chat_obj = chat_obj.json()

        send_message_body = {
            "body": {
                "contentType": "html",
                "content": message
            }
        }
        message_obj = graph_client.post(
            f'/chats/{chat_obj.get("id")}/messages',
            data=json.dumps(send_message_body),
            headers={'Content-Type': 'application/json'}
        )
    else:
        return {
            "statusCode": 405,
            "body": "Method not allowed."
        }
