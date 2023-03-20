import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import boto3
import json
from youtube_transcript_api import YouTubeTranscriptApi
import gc

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
TOKEN_PARAMETER_NAME = os.environ['TOKEN_PARAMETER_NAME']
CHANNEL_LIST_BUCKET = os.environ['CHANNEL_LIST_BUCKET']
CHANNEL_LIST_KEY = os.environ['CHANNEL_LIST_KEY']
VIDEOS_TABLE_NAME = os.environ['VIDEOS_TABLE_NAME']
PHRASES_TABLE_NAME = os.environ['PHRASES_TABLE_NAME']
TRANSCRIPTS_BUCKET = os.environ['TRANSCRIPTS_BUCKET']

def hander(event, context):
    
    # Get the youtube credentials
    creds = get_credentials()
    # Create the youtube client
    youtube = build('youtube', 'v3', credentials=creds)
    # Get the channel list
    channel_list = get_channel_list()

    # Get the list of videos
    videos = get_video_list(youtube, channel_list)
    # Initialize the dynamodb client
    dynamodb = boto3.resource('dynamodb')
    videos_table = dynamodb.Table(VIDEOS_TABLE_NAME)
    # Save videos to DynamoDB
    create_video_records(videos, videos_table)

    # Initialize the s3 client
    transcript_bucket = boto3.resource('s3').Bucket(TRANSCRIPTS_BUCKET)
    # Download transcripts
    transcripts = download_transcripts(videos, transcript_bucket)

    # Coalesce transcripts
    coalesced_transcripts = coalesce_transcripts(transcripts)
    save_coalesced_transcripts(coalesced_transcripts, transcript_bucket)
    
    # Select candidate phrases
    candidate_phrases = gen_candidate_phrases(coalesced_transcripts)
    # Initialize the phrases table
    phrases_table = dynamodb.Table(PHRASES_TABLE_NAME)
    # Save records to DynamoDB
    create_phrase_records(candidate_phrases, phrases_table)

def get_credentials():

    authorized_user_info = json.loads(
        get_parameter_value(TOKEN_PARAMETER_NAME)
    )
    creds = Credentials.from_authorized_user_info(
        authorized_user_info,
        SCOPES
    )
    # If there are no (valid) credentials available, let the user log in.
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_parameter_value(parameter_name):
    session = boto3.session.Session()
    ssm = session.client('ssm')
    parameter = ssm.get_parameter(Name = parameter_name, WithDecryption = True)
    return parameter['Parameter']['Value']

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
        part="snippet",
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
            part="snippet",
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

def create_video_records(videos, table):
    for video in videos:
        table.put_item(
            Item={
                'video_id': video['id'],
                'channel_id': video['snippet']['channelId'],
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'published_at': video['snippet']['publishedAt'],
                'transcript': 's3://{}/{}.json'.format(TRANSCRIPTS_BUCKET, video['id'])
            }
        )

def download_transcripts(videos, bucket):
    objs = []
    for video in videos:
        try:
            # Get the transcipt
            transcript = YouTubeTranscriptApi.get_transcript(video['id'])
            # Save it to s3
            response = bucket.put_object(
                Key='transcripts/{}.json'.format(video['id']),
                Body=json.dumps(transcript)
            )
            objs.append(response)

        except Exception as e:
            print('No transcript found for {}'.format(video['id']))
    
    return objs

def coalesce_transcripts(transcripts): 
    new_buffer = {"text": "", "start": 0.0, "duration": 0.0}
    coalesced_transcripts = []
    for transcript in transcripts:
        # Get transcript content
        transcript_content = json.loads(transcript.get()['Body'].read().decode('utf-8'))
        c_transcript = {
            "video_id": transcript.key.split('/')[1].split('.')[0],
            "phrases": []
        }

        buffer = new_buffer.copy()
        for item in transcript_content:
            # If this item start with "-", start a new phrase
            if item['text'].startswith('-'):
                if len(buffer["text"]) > 0:
                    c_transcript['phrases'].append(buffer.copy())
                    buffer = new_buffer.copy()
                    buffer['start'] = item['start']
                    gc.collect()

            # Append content
            buffer['text'] += ' ' + item['text']
            buffer['duration'] += item['duration']

        # Save the last buffer to the list of phrases
        c_transcript['phrases'].append(buffer.copy())
        coalesced_transcripts.append(c_transcript)

    return coalesced_transcripts

def save_coalesced_transcripts(transcripts, bucket):
    for transcript in transcripts:
        response = bucket.put_object(
            Key='coalesced-transcripts/{}.json'.format(transcript['video_id']),
            Body = json.dumps(transcript['phrases'])
        )

def gen_candidate_phrases(transcripts):
    phrases = []
    for transcript in transcripts:
        for phrase in transcript['phrases']:
            
            text = phrase['text']
            # remove the initial '- '
            if text.startswith('- '):
                text = text[2:]
            
            # Check if the phrase specified who said it
            said_by = None
            if text.startswith('['):
                said_by = text.split(']')[0][1:]
                text = text.split(']')[1]
            
            # Generate the object
            phrases.append({
                'video_id': transcript['video_id'],
                'said_by': said_by,
                'start' : phrase['start'],
                'duration': phrase['duration'],
                'text': text
            })
    return phrases

def create_phrase_records(phrases, table):
    for phrase in phrases:
        table.put_item(
            Item=phrase
    )