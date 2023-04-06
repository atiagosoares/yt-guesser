from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import CouldNotRetrieveTranscript
import os

class DataEngine():
    def get_latest_video(self, channel_id: str) -> dict:
        pass
    def get_transcript(self, video_id: str) -> list:
        pass

# ================== MOCK ENGINE ==================
class MockData(DataEngine):
    def get_latest_video(self, channel_id: str) -> dict:
        return {
            'id': '123',
            'channel_id': '123',
            'published_at': '2020-01-01',
            'title': 'Mock video'
        }
    def get_transcript(self, video_id: str) -> list:
        return [
            {
                'video_id': '123',
                'start': 0.0,
                'duration': 1.0,
                'text': 'Mock transcript'
            }
        ]

# ================== YT ENGINE ==================


class YTData(DataEngine):

    def __init__(self, youtube_service):
        self.youtube = youtube_service

    def get_latest_video(self, channel_id: str) -> dict:
        search = self._search_recent_videos(channel_id)
        if len(search) == 0:
            return None
        
        video = self._construct_video_object_from_search_result(search[0])
        return video

    def _search_recent_videos(self, channel_id):
        # This request fetches the 5 most recent videos
        request = self.youtube.search().list(
            part = 'id,snippet',
            channelId = channel_id,
            order = 'date',
            maxResults = 1
        )
        search = request.execute()
        return search.get('items')

    def _construct_video_object_from_search_result(self, search_result):
        video = {
            'id' : search_result['id']['videoId'],
            'channel_id': search_result['snippet']['channelId'],
            'published_at': search_result['snippet']['publishedAt'],
            'title': search_result['snippet']['title']
        }
        return video 

    # Download the video transcript and save it to s3 as json
    def get_transcript(video_id):
        try:
            transcript_json = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript_json
        except CouldNotRetrieveTranscript as e:
            print(e)
            return False