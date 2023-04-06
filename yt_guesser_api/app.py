import os
import json

from chalice import Chalice, NotFoundError, ConflictError, BadRequestError
from chalicelib import db
import boto3

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

GOOGLE_TOKEN_PARAMETER_NAME = os.environ.get('GOOGLE_TOKEN_PARAMETER_NAME')
TRANSCRIPTS_BUCKET = os.environ.get('TRANSCRIPTS_BUCKET')
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
_DB = None

# -------------- NECCESSARY BULLSHIT --------------
def get_db():
    global _DB
    if _DB is None:
        # Create the DynamoDB resources
        channels_table = boto3.resource('dynamodb').Table(os.environ['CHANNELS_TABLE_NAME'])
        videos_table = boto3.resource('dynamodb').Table(os.environ['VIDEOS_TABLE_NAME'])
        transcripts_table = boto3.resource('dynamodb').Table(os.environ['TRANSCRIPTS_TABLE_NAME'])
        _DB = db.DynamoDB(channels_table, videos_table, transcripts_table)
    return _DB

def get_yt():
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

# -------------- API --------------
app = Chalice(app_name='app')

@app.route('/channels', methods = ['GET'])
def channels_list():
    items = get_db().channels_list()
    return items

@app.route('/channels/{channel_id}', methods = ['GET'])
def channels_get(channel_id):
    item = get_db().channels_get(channel_id)
    if not item:
        raise NotFoundError('Channel not found')
        
    return item

@app.route('/channels', methods = ['POST'])
def channels_add():

    channel_id = app.current_request.json_body['id']
    # Check if channel aready exists
    if get_db().channels_get(channel_id):
        raise ConflictError('Channel already exists')

    # Search for this channel in the youtubde data api
    request = get_yt().channels().list(
        part='id,snippet,contentDetails',
        id = channel_id
    )
    channels = request.execute().get('items')

    # Validate reponse
    if not channels:
        return {'error': 'Channel not found'}
    
    # Check if any fo the founc channels are the one we are looking for
    target_channel = None
    for channel in channels:
        if channel['id'] == channel_id:
            target_channel = channel
            break

    # insert item into db
    result = get_db().channels_create(target_channel)

    return {'message': 'Channel added'}

@app.route('/channels/{channel_id}', methods = ['DELETE'])
def channels_remove(channel_id):
    result = get_db().channels_delete(channel_id)
    return {'message': 'Channel removed'}

@app.route('/videos', methods = ['GET'])
def videos_list():
    items = get_db().videos_list()
    return items

@app.route('/videos/{video_id}', methods = ['GET'])
def videos_get(video_id):
    item = get_db().videos_get(video_id)
    if not item:
        raise NotFoundError('Video not found')
    return item

@app.route('/transcripts', methods = ['GET'])
def transcripts_list():
    items = get_db().transcripts_list()
    return items 

@app.route('/transcripts/curate', methods = ['POST'])
def transcripts_curate():
    # Get the video id from the request body
    video_id = app.current_request.json_body['video_id']
    start = app.current_request.json_body['start']
    # Submit curration
    result = get_db().transcripts_curate(video_id, start)

    if not result:
        raise BadRequestError('Invalid request')

    return {'message': 'Transcript curration submitted'}