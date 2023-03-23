from chalice import Chalice
from chalicelib import db
import os
import boto3

app = Chalice(app_name='yt_guesser_api')

_DB = None
def get_db():
    global _DB
    if _DB is None:
        # Create the DynamoDB resources
        channels_table = boto3.resource('dynamodb').Table(os.environ['CHANNELS_TABLE_NAME'])
        videos_table = boto3.resource('dynamodb').Table(os.environ['VIDEOS_TABLE_NAME'])
        transcripts_table = boto3.resource('dynamodb').Table(os.environ['TRANSCRIPTS_TABLE_NAME'])
        _DB = db.DynamoDB(channels_table, videos_table, transcripts_table)
    return _DB

def get_app_db():
    global _DB
    if _DB is None:
        _DB = InMemoryTodoDB()
    return _DB

@app.route('/channels', methods = ['GET'])
def channels_list():
    items = get_db().channels_list()
    return items

@app.route('/channels/{channel_id}', methods = ['GET'])
def channels_get(channel_id):
    item = get_db().channels_get(channel_id)
    return item

@app.route('/channels', methods = ['POST'])
def channels_add():
    request = app.current_request
    channel = {
        'id': request.json_body['id'] 
    }
    result = get_db().channels_create(channel)
    return result

@app.route('/channels/{channel_id}', methods = ['DELETE'])
def channels_remove(channel_id):
    result = get_db().channels_delete(channel_id)
    return result

@app.route('/videos', methods = ['GET'])
def videos_list():
    items = get_db().videos_list()
    return items

@app.route('/videos/{video_id}', methods = ['GET'])
def videos_get(video_id):
    item = get_db().videos_get(video_id)
    return item

@app.route('/transcripts', methods = ['GET'])
def transcripts_list():
    return {'action': 'You choose to list transcripts'} 

@app.route('/transcripts/curate', methods = ['POST'])
def transcripts_curate():
    request = app.current_request
    body = request.json_body

    return {'action': f'{type(body)}'}


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.