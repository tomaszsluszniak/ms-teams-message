import json
import os
import logging

import sentry_sdk

from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.serverless import serverless_function

from azure.identity import UsernamePasswordCredential
from msgraph.core import GraphClient


AZ_CLIENT_ID_FILE = '/var/openfaas/secrets/bpsod-az-client-id'
LOGIN_FILE = '/var/openfaas/secrets/bpsod-teams-connector-login'
PASSWORD_FILE = '/var/openfaas/secrets/bpsod-teams-connector-password'
SENTRY_DSN_FILE = '/var/openfaas/secrets/bpsod-teams-connector-sentry-dsn'

_f_client_id = open(AZ_CLIENT_ID_FILE, 'r')
AZ_CLIENT_ID = _f_client_id.readline()

_f_login = open(LOGIN_FILE, 'r')
LOGIN = _f_login.readline()

_f_password = open(PASSWORD_FILE, 'r')
PASSWORD = _f_password.readline()

_f_sentry = open(SENTRY_DSN_FILE, 'r')
SENTRY_DSN = _f_sentry.readline()

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
            username=LOGIN, 
            password=PASSWORD
        )
        client = GraphClient(credential=credential)

        params = json.loads(event.body.decode('utf-8'))

        errors = []
        owner = params.get('owner')
        message = params.get('message')

        if owner is None:
            errors.append('The "owner" field is required.')
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
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{LOGIN}')"
                },
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{owner}')"
                }
            ]
        }
        chat_obj = client.post(
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
        message_obj = client.post(
            f'/chats/{chat_obj.get("id")}/messages',
            data=json.dumps(send_message_body),
            headers={'Content-Type': 'application/json'}
        )
    else:
        return {
            "statusCode": 405,
            "body": "Method not allowed."
        }
