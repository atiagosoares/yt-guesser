import sys
sys.path.append('src/search_videos')

import pystest
from search_engines import MockSearch

#==================  Mock Interface ==================
engine = MockSearch()

# Function to check if a dict is a valid video object
def _is_valid_video_object(video: dict) -> bool:
    if not video.get('id'):
        return False
    if not video.get('channel_id'):
        return False
    if not video.get('published_at'):
        return False
    if not video.get('title'):
        return False
    
# The objective of these tests is defining a valid interface
def test_mock_engine():
    # Test that the engine is a valid object
    video = engine.get_latest_video('<channel_id>')
    assert (video is None) or _is_valid_video_object(video)