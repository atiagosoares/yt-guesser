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

    def videos_list(self, uid, description=None, state=None,
                    metadata=None):
        pass

    def videos_get(self, uid):
        pass

    def videos_create(self, video):
        pass

    def transcripts_list():
        pass

    def transcripts_curate():
        pass


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

    def transcripts_list(self, video_id, curated = None):
        key_condition_expression = Key('video_id').eq(video_id)
        if curated:
            key_condition_expression = key_condition_expression & Key('curated').eq(curated)
        response = self._transcripts.query(
            KeyConditionExpression=key_condition_expression
        )
        return response['Items']

    def transcripts_curate(self, video_id, start):
        response = self._transcripts.update_item(
            Key={'video_id': video_id, 'start': start},
            UpdateExpression='SET curated = :val1',
            ExpressionAttributeValues={
                ':val1': True
            }
        )
        return True