import boto3
import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from data_engines import YTData

TRANSCRIPTS_BUCKET_NAME = os.environ.get('TRANSCRIPTS_BUCKET_NAME')
GOOGLE_TOKEN_PARAMETER_NAME = os.environ.get('GOOGLE_TOKEN_PARAMETER_NAME')
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

_DB = None
def get_db():
    global _DB
    if _DB is None:
        # Create the DynamoDB resources
        channels_table = boto3.resource('dynamodb').Table(os.environ['CHANNELS_TABLE_NAME'])
        videos_table = boto3.resource('dynamodb').Table(os.environ['VIDEOS_TABLE_NAME'])
        transcripts_table = boto3.resource('dynamodb').Table(os.environ['TRANSCRIPTS_TABLE_NAME'])
        _DB = db.DynamoDB(channels_table, videos_table, transcripts_table)
    return _DB

def handler(event, context):

    # Create YT data Engine
    yt_service = get_yt_service()
    yt_data_engine = YTData(yt_service)
    # Get DB
    db = get_db()
    # Create bucket
    transcripts_bucket = boto3.resource('s3').Bucket(TRANSCRIPTS_BUCKET_NAME)

    # Create controller
    controller = VideoSearchController(db, yt_data_engine, transcripts_bucket)
    # Search videos
    controller.search_videos()

def get_yt_service():
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

class VideoSearchController:
    def __init__(self, db, data_engine, transcripts_bucket):
        self.db = db
        self.data_engine = data_engine
        self.bucket = transcripts_bucket

    def search_videos(self):
        # List all channels in the channels table
        channels = self.db.channels_list()

        # Search recent videos for each channel in the list
        videos = []
        for channel in channels:
            video = self.data_engine.get_latest_video(channel['id'])
            if video:
                videos.append(video)
        print(videos)
        
        # Filter out videos that already exist in the videos table
        videos = [video for video in videos if not self.db.videos_get(video['id'])]

        # Download their transcripts
        for video in videos:
            transcript = self.data_engine.get_transcript(video['id'])
            if transcript:
                # Save to S3
                self.bucket.put_object(
                    Key = f'{video["id"]}.json',
                    Body = json.dumps(transcript)
                )
        
        # Insert the videos into the videos table
        for video in videos:
            self.db.videos_create(video)
        
        return videos

