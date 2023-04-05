import sys
# Add the parent directory to the path so we can import the Enricher class
sys.path.append('src/process_transcripts')

import pytest
import json
from main import Controller
from enricher.enricher import MockEnricher
from db import MockDB

# Create controller
enricher = MockEnricher()
db = MockDB()
controller = Controller(enricher, db)

# Load test data
with open('tests/test_events/brain_waves.json') as f:
    brain_waves_event = json.load(f)


def test_load_transcript():
    transcript = controller._load_transcript(
        brain_waves_event['Records'][0]['s3']['bucket']['name'],
        brain_waves_event['Records'][0]['s3']['object']['key']
        )
    assert transcript[0]['text'] == "today I'm going to put this weird thing"

def test_create_transcript_objects():
    transcripts = [{
        "text": "foo",
        "start": 1999
    }]
    video_id = '123'
    t_objects = controller._create_transcript_objects_from_transcript(transcripts, 'video-id')
    assert t_objects == [{
        "text": "foo",
        "start": 1999,
        "speaker": None,
        "curated": None,
        "url": "https://www.youtube.com/watch?v=video-id&t=1",
        "video_id": "video-id"
    }]

def test_basic_event():
    transcripts = controller.process_event(brain_waves_event['Records'][0]['s3'])
    want = [
        {
            "video_id": "-HYbFm67Gs8",
            "text": "today I'm going to put this weird thing",
            "start": 0,
            "speaker": None,
            "curated": None,
            "url": "https://www.youtube.com/watch?v=-HYbFm67Gs8&t=0"
        },
        {   
            "video_id": "-HYbFm67Gs8",
            "text": "on my head and communicate with gpt4",
            "start": 1800,
            "speaker": None,
            "curated": None,
            "url": "https://www.youtube.com/watch?v=-HYbFm67Gs8&t=1",
        }
    ]

    assert transcripts == want
    assert db.transcripts_list("-HYbFm67Gs8") == want

def test_large_file():
    '''
    Tests whether the controller ignores large files.
    '''
    with open('tests/test_events/large-file.json') as f:
        # This is a large file. Controller should ignore it.
        event = json.load(f)

    transcripts = controller.process_event(event['Records'][0]['s3'])
    assert transcripts == None
