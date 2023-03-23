import os
import json

from chalice import Chalice, NotFoundError
from chalicelib import db
import boto3

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GOOGLE_TOKEN_PARAMETER_NAME = os.environ.get('GOOGLE_TOKEN_PARAMETER_NAME')
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

_DB = None
_YT = None

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
    global _YT
    if not _YT:
        authorized_user_info = json.loads(
            get_parameter_value(GOOGLE_TOKEN_PARAMETER_NAME)
        )
        creds = Credentials.from_authorized_user_info(
            authorized_user_info,
            SCOPES
        )
        # If there are no (valid) credentials available, let the user log in.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        _YT = build('youtube', 'v3', credentials=creds)
    return _YT

def get_parameter_value(parameter_name):
    session = boto3.session.Session()
    ssm = session.client('ssm')
    parameter = ssm.get_parameter(Name = parameter_name, WithDecryption = True)
    return parameter['Parameter']['Value']


# -------------- API --------------
app = Chalice(app_name='yt_guesser_api')

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
        return {'error': 'Channel already exists'}

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
    item = None
    for channel in channels:
        if channel['id'] == channel_id:
            item = channel
            break

    # insert item into db
    result = get_db().channels_create(item)

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
    return item

@app.route('/transcripts', methods = ['GET'])
def transcripts_list():
    return {'action': 'You choose to list transcripts'} 

@app.route('/transcripts/curate', methods = ['POST'])
def transcripts_curate():
    request = app.current_request
    body = request.json_body

    return {'action': f'{type(body)}'}


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.