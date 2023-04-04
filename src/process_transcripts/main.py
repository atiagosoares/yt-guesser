import boto3
import os
import json
from enricher import OpenAIChatEnricher
import db
import nltk

OPENAI_API_KEY_PARAMETER_NAME = os.environ.get('OPENAI_API_KEY_PARAMETER_NAME')

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

def get_enricher():
    api_key = _get_parameter_value(OPENAI_API_KEY_PARAMETER_NAME)
    enricher = OpenAIChatEnricher(api_key)
    return enricher

def handler(event, context):

    db = get_db()
    enricher = get_enricher()

    controller = Controller(enricher, db)

    for record in event['Records']:
        s3_event = record['s3']
        controller.process_event(s3_event)

class Controller():

    def __init__(self, enricher, db):
        self.enricher = enricher
        self.db = db

    def process_event(self, event):
        # Get the video id from the event
        video_id = event['object']['key'].split('.')[0]

        # Load the transcript
        transcript = self._load_transcript(event['bucket']['name'], event['object']['key'])

        # Enrich the transcript
        enriched_transcript = self.enricher.enrich(transcript)

        # Create transcript objects
        transcript_objects = self._create_transcript_objects_from_transcript(enriched_transcript, video_id)

        # Insert transcript objects into the transcripts table
        for transcript_object in transcript_objects:
            self.db.transcripts_create(transcript_object)

        return transcript_objects
    
    def _load_transcript(self, bucket_name, key):
        s3 = boto3.resource('s3')
        obj = s3.Object(bucket_name, key)
        transcript = json.loads(obj.get()['Body'].read().decode('utf-8'))
        return transcript

    def _create_transcript_objects_from_transcript(self, transcript, video_id):
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