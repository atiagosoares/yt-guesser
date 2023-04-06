import sys
sys.path.append('src/search_videos')

import pytest
import json
from main import VideoSearchController
from db import MockDB
from data_engines import MockData

class MockBucket:
    def __init__(self):
        self._data = {}
    
    def put_object(self, Key, Body):
        self._data[Key] = Body

mock_db = MockDB()
mock_db.channels_create({
    'id': '123',
    'name': 'Mock channel'
})
mock_data_engine = MockData()
mock_bucket = MockBucket()

controller = VideoSearchController(mock_db, mock_data_engine, mock_bucket)

def test_search_videos():
    controller.search_videos()
    assert mock_db.videos_get('123')

    # The transcript should have been added to the bucket
    saved_transcript = json.loads(mock_bucket._data['123.json'])
    assert saved_transcript[0]['text'] == 'Mock transcript'