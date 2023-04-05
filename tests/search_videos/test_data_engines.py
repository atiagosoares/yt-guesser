import sys
sys.path.append('src/search_videos')

import pytest
from data_engines import MockData

#==================  Mock Interface ==================
engine = MockData()

# Function to check if a dict is a valid video object
def _is_valid_video_object(video: dict) -> bool:
    video_id = video.get('id')
    if not type(video_id) == str:
        return False
    channel_id = video.get('channel_id')
    if not type(channel_id) == str:
        return False
    published_at = video.get('published_at')
    if not type(published_at) == str:
        return False
    title = video.get('title')
    if not type(title) == str:
        return False
    return True

def _is_valid_transcript_object(transcript: dict) -> bool:
    video_id = transcript.get('video_id')
    if not type(video_id) == str:
        return False
    
    start = transcript.get('start')
    if not type(start) == float:
        return False
    return True
    
# ================== MOCK ENGINE ==================
def test_get_video():
    # Test that the engine is a valid object
    video = engine.get_latest_video('<channel_id>')
    assert (video is None) or _is_valid_video_object(video)\

def test_get_transcript():
    transcript = engine.get_transcript('<video_id>')
    assert type(transcript) == list
    for t in transcript:
        assert _is_valid_transcript_object(t)