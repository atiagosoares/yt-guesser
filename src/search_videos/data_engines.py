class DataEngine():
    def get_latest_video(self, channel_id: str) -> dict:
        pass
    def get_transcript(self, video_id: str) -> list:
        pass

# Mock engine
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