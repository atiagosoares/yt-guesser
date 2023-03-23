from chalice import Chalice


app = Chalice(app_name='yt_guesser_api')



@app.route('/channels', methods = ['GET'])
def channels_list():
    return {'action': 'You choose to list all channels'}

@app.route('/channels/{channel_id}', methods = ['GET'])
def channels_get(channel_id):
    return {'action': f'You choose to fetch the specific channel {channel_id}'}

@app.route('/channels', methods = ['POST'])
def channels_create():
    body = app.current_request.json_body
    return {'action': f'{type(body)}'}

@app.route('/channels/{channel_id}', methods = ['DELETE'])
def channels_delete(channel_id):
    return {'action': f'You choose to delete the specific channel {channel_id}'}

@app.route('/videos', methods = ['GET'])
def videos_list():
    return {'action': 'You choose to list all videos'}

@app.route('/videos/{video_id}', methods = ['GET'])
def videos_get(video_id):
    return {'action': f'You choose to fetch the specific video {video_id}'}

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