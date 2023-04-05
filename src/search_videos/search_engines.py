class VideoSearchEngine():
    def get_latest_video(self, channel_id: str) -> dict:
        pass

# Mock engine
class MockSearch(VideoSearchEngine):
    def get_latest_video(self, channel_id: str) -> dict:
        return {
            'id': '123',
            'channel_id': '123',
            'published_at': '2020-01-01',
            'title': 'Mock video'
        }