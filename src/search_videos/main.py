import boto3
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os


GOOGLE_TOKEN_PARAMETER_NAME = os.environ.get('GOOGLE_TOKEN_PARAMETER_NAME')
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def _build_yt_service():
 
    authorized_user_info = json.loads(
        _get_parameter_value(GOOGLE_TOKEN_PARAMETER_NAME)
    )
    creds = Credentials.from_authorized_user_info(
        authorized_user_info,
        SCOPES
    )
    # If there are no (valid) credentials available, let the user log in.
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save the refreshed credentials to ssm
        _update_parameter_value(GOOGLE_TOKEN_PARAMETER_NAME, creds.to_json())

    youtube = build('youtube', 'v3', credentials=creds)
    return youtube

def _get_parameter_value(parameter_name):
    session = boto3.session.Session()
    ssm = session.client('ssm')
    parameter = ssm.get_parameter(Name = parameter_name, WithDecryption = True)
    return parameter['Parameter']['Value']

def _update_parameter_value(parameter_name, parameter_value):
    session = boto3.session.Session()
    ssm = session.client('ssm')
    ssm.put_parameter(
        Name = parameter_name,
        Value = parameter_value,
        Type = 'SecureString',
        Overwrite = True
    )