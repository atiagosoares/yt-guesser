from boto3.dynamodb.conditions import Key

class YTGuesserDB(object):

    # Channels
    def channels_list(self):
        pass

    def channels_create(self, channel_id):
        pass

    def channels_add(self, uid):
        pass

    def channels_remove(self, uid):
        pass

    def videos_list(self, uid, description=None, state=None, metadata=None):
        pass

    def videos_get(self, uid):
        pass

    def videos_create(self, video):
        pass

    def videos_update(self, video):
        pass

    def transcripts_list(video_id, start = None, end = None, curated = None):
        pass

    def transcripts_get(video_id, start):
        pass

    def transcripts_create(transcript):
        pass

    def transcripts_curate():
        pass

class MockDB(YTGuesserDB):
    def __init__(self):
        self._channels = []
        self._videos = []
        self._transcripts = []
    
    def channels_list(self):
        return self._channels
    
    def channels_get(self, channel_id):
        for channel in self._channels:
            if channel['id'] == channel_id:
                return channel
        return None
    
    def channels_create(self, channel_info):
        self._channels.append(channel_info)
        return True
    
    def channels_delete(self, channel_id):
        for channel in self._channels:
            if channel['id'] == channel_id:
                self._channels.remove(channel)
                return True
        return False
    
    def videos_list(self, channel_id = None):
        if channel_id is None:
            return self._videos
        else:
            return [video for video in self._videos if video['channel_id'] == channel_id]
        
    def videos_get(self, video_id):
        for video in self._videos:
            if video['id'] == video_id:
                return video
        return None 
    
    def videos_create(self, video_info):
        self._videos.append(video_info)
        return True
    
    def videos_update(self, video_info):
        for video in self._videos:
            if video['id'] == video_info['id']:
                video.update(video_info)
                return True
        return False
    
    def videos_delete(self, video_id):
        for video in self._videos:
            if video['id'] == video_id:
                self._videos.remove(video)
                return True
        return False
    
    def transcripts_list(self, video_id, start = None, end = None, curated = None):
        if start is None:
            start = 0
        if end is None:
            end = float('inf')
        
        response = []
        for transcript in self._transcripts:
            if transcript['video_id'] == video_id and transcript['start'] >= start and transcript['start'] <= end and transcript['curated'] == curated:
                response.append(transcript)
        return response
    
    def transcripts_get(self, video_id, start):
        for transcript in self._transcripts:
            if transcript['video_id'] == video_id and transcript['start'] == start:
                return transcript
        return None
    
    def transcripts_create(self, transcript_info):
        self._transcripts.append(transcript_info)


class DynamoDB(YTGuesserDB):
    def __init__(self, channels_table, videos_table, transcripts_table):
        self._channels = channels_table
        self._videos = videos_table
        self._transcripts = transcripts_table
        
    def channels_list(self):
        response = self._channels.scan()
        return response['Items']

    def channels_get(self, channel_id):
        response = self._channels.get_item(
            Key={'id': channel_id}
        )
        return response.get('Item', None)

    def channels_create(self, channel_info):
        response = self._channels.put_item(
            Item=channel_info
        )
        return True

    def channels_delete(self, channel_id):
        response = self._channels.delete_item(
            Key={'id': channel_id}
        )
        return True

    def videos_list(self, channel_id = None):
        if channel_id is None:
            response = self._videos.scan()
        else:
            response = self._videos.query(
                SecondaryIndexName='channel_id-index',
                KeyConditionExpression=Key('channel_id').eq(channel_id)
            )
        return response['Items']

    def videos_get(self, video_id):
        response = self._videos.get_item(
            Key={'id': video_id}
        )
        return response['Item']
    
    def videos_create(self, video):
        response = self._videos.put_item(
            Item=video
        )
        return True

    def transcripts_list(self, video_id, start = None, end = None, curated = None):

        key_condition_expression = Key('video_id').eq(video_id)
        if start:
            key_condition_expression = key_condition_expression & Key('start').gte(start)
        if end:
            key_condition_expression = key_condition_expression & Key('start').lt(end)
        if curated:
            key_condition_expression = key_condition_expression & Key('curated').eq(curated)
        response = self._transcripts.query(
            KeyConditionExpression=key_condition_expression
        )
        return response['Items']
    
    def transcripts_get(self, video_id, start):
        response = self._transcripts.get_item(
            Key={'video_id': video_id, 'start': start}
        )
        return response['Item']
    
    def transcripts_create(self, transcript):
        response = self._transcripts.put_item(
            Item=transcript
        )
        return True

    def transcripts_curate(self, video_id, start):
        response = self._transcripts.update_item(
            Key={'video_id': video_id, 'start': start},
            UpdateExpression='SET curated = :val1',
            ExpressionAttributeValues={
                ':val1': True
            }
        )
        return True