import boto3
import os
import json
from enricher import OpenAIChatEnricher
import db

OPENAI_API_KEY_PARAMETER_NAME = os.environ.get('OPENAI_API_KEY_PARAMETER_NAME')

DB = None
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

    # Unpack s3 data
    s3_event = event['Records'][0]['s3']

    # Get the video id from the event
    video_id = s3_event['object']['key'].split('.')[0]
    # Get the transcript from s3
    s3 = boto3.resource('s3')
    obj = s3.Object(s3_event['bucket']['name'], event['key'])
    transcript = json.loads(obj.get()['Body'].read().decode('utf-8'))
    
    # Load openai api key
    api_key = _get_parameter_value(OPENAI_API_KEY_PARAMETER_NAME)
    # Build enricher object
    enricher = OpenAIChatEnricher(api_key)
    enriched_transcript = enricher.enrich(transcript)

    # Create transcript objects
    transcript_objects = _create_transcript_objects_from_transcript(enriched_transcript, video_id)

    # Insert transcript objects into the transcripts table
    db = get_db()
    for transcript_object in transcript_objects:
        db.transcripts_create(transcript_object)


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

def _get_parameter_value(parameter_name):
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']

