import sys
sys.path.append('src/search_videos')

import pytest
from main import VideoSearchController
from db import MockDB
from data_engines import MockDataEngine

class MockBucket:
    def __init__(self):
        self._data = {}
    
    def put_object(self, Key, Body):
        self._data[Key] = Body

mock_db = MockDB()
mock_data_engine = MockDataEngine()
mock_bucket = MockBucket()

controller = VideoSearchController(mock_db, mock_data_engine, mock_bucket)

def test_search_videos():
    controller.search_videos()

    # The video should have been added to the database
    assert mock_db.videos_get('123')
    # The transcript should have been added to the bucket
    assert mock_bucket._data['123.json']