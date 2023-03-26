import os
import json

from chalice import Chalice, NotFoundError, ConflictError, BadRequestError
from chalicelib import db
import boto3

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import CouldNotRetrieveTranscript

GOOGLE_TOKEN_PARAMETER_NAME = os.environ.get('GOOGLE_TOKEN_PARAMETER_NAME')
TRANSCRIPTS_BUCKET = os.environ.get('TRANSCRIPTS_BUCKET')
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

        _YT = build('youtube', 'v3', credentials=creds)
    return _YT

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

# Fuction to pool for recently posted videos
@app.schedule('rate(1 hour)')
def search_videos(event):

    # List all channels in the channels table
    db = get_db()
    channels = db.channels_list()

    # Search recent videos for each channel in the list
    items = []
    for channel in channels:
        search_results = _search_recent_videos(channel['id'])
        # If the result is not null
        if search_results:
            for result in search_results:
                if result['id']['kind'] == 'youtube#video':
                    items.append(result)
    
    # Convert the search result items to expected video schema
    videos = [_construct_video_object_from_search_result(item) for item in items]

    # Download their transcripts
    for video in videos:
        result = _download_transcript(video['id'])
        video['transcript_available'] = result
    
    # Insert the videos into the videos table
    for video in videos:
        db.videos_create(video)

def _search_recent_videos(channel_id):
    youtube = get_yt()
    # This request fetches the 5 most recent videos
    request = youtube.search().list(
        part = 'id,snippet',
        channelId = channel_id,
        order = 'date'
    )
    search = request.execute()
    return search.get('items')

def _construct_video_object_from_search_result(sr):
    #sr = search result
    video = {
        'id' : sr['id']['videoId'],
        'channel_id': sr['snippet']['channelId'],
        'published_at': sr['snippet']['publishedAt'],
        'title': sr['snippet']['title']
    }
    return video

# Download the video transcript and save it to s3 as json
def _download_transcript(video_id):
    try:
        transcript_json = YouTubeTranscriptApi.get_transcript(video_id)
    except CouldNotRetrieveTranscript as e:
        print(e)
        return False

    try:
        s3 = boto3.resource('s3') 
        obj = s3.Object(TRANSCRIPTS_BUCKET, f'{video_id}.json')
        obj.put(Body = json.dumps(transcript_json))
        return True
    except Exception as e:
        print('Could not upload transcript to s3')
        print(e)
        return False

# Function to process and enrich recently downloaded transcripts
@app.on_s3_event(bucket=TRANSCRIPTS_BUCKET, events=['s3:ObjectCreated:*'])
def process_transcript(event):
    # Get the video id from the event
    video_id = event.key.split('.')[0]
    # Get the transcript from s3
    s3 = boto3.resource('s3')
    obj = s3.Object(TRANSCRIPTS_BUCKET, event.key)
    transcript = json.loads(obj.get()['Body'].read().decode('utf-8'))
    
    # process the transcript
    enriched_transcript = _enrich_transcript(transcript)

    # Create transcript objects
    transcript_objects = _create_transcript_objects_from_transcript(enriched_transcript, video_id)

    # Insert transcript objects into the transcripts table
    db = get_db()
    for transcript_object in transcript_objects:
        db.transcripts_create(transcript_object)

def _enrich_transcript(transcript):
    #TODO: implement
    pass

def _create_transcript_objects_from_transcript(transcript, video_id):
    transcript_objects = []
    for item in transcript:
        transcript_object = {
            'video_id': video_id,
            'start': item['start'],
            'text': item['text'],
            'speaker': item.get('speaker', None),
            'curated': None,
            'url': f'https://www.youtube.com/watch?v={video_id}&t={item["start"]//1000}'
        }
        transcript_objects.append(transcript_object)
    return transcript_objects