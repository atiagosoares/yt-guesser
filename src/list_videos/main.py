from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import boto3
import json

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
TOKEN_SECRET_ARN = os.environ['TOKEN_SECRET_ARN']
CHANNEL_LIST_BUCKET = os.environ['CHANNEL_LIST_BUCKET']
CHANNEL_LIST_KEY = os.environ['CHANNEL_LIST_KEY']

def hander(event, context):
    
    # Get the youtube credentials
    creds = get_credentials()
    # Create the youtube client
    youtube = build('youtube', 'v3', credentials=creds)
    # Get the channel list
    channel_list = get_channel_list()

    # Get the list of videos
    videos = get_video_list(youtube, channel_list)


    # Saving results
    with open('data/video-list.json', 'w') as f:
        json.dump(videos, f)

def get_credentials():

    authorized_user_info = json.loads(
        get_secret(TOKEN_SECRET_ARN)
    )
    creds = Credentials.from_authorized_user_info(
        authorized_user_info,
        SCOPES
    )
    # If there are no (valid) credentials available, let the user log in.
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_secret(secret_arn):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    return get_secret_value_response['SecretString']

def get_channel_list():
    # Load the txt file from s3
    s3_object = boto3.resource('s3').Object(
        os.environ['CHANNEL_LIST_BUCKET'],
        os.environ['CHANNEL_LIST_KEY']
    )

    channel_list = s3_object.get()['Body'].read().decode('utf-8').splitlines()
    channel_list = [channel.split('#')[0].strip() for channel in channel_list]
    return channel_list

def get_video_list(youtube, channel_list):

    # List most popular videos
    videos = []
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="US",
        videoCategoryId=28, # Technology
        maxResults=20
    )
    response = request.execute()
    videos.extend(
        [video for video in response['items'] if video['snippet']['channelId'] in channel_list]
    )
    page_token = response.get('nextPageToken')

    while page_token:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode="US",
            maxResults=20,
            videoCategoryId = 28,
            pageToken = page_token
        )
        response = request.execute()
        videos.extend(
                [video for video in response['items'] if video['snippet']['channelId'] in channel_list]
        )
        page_token = response.get('nextPageToken')
    return videos