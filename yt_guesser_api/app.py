from chalice import Chalice


app = Chalice(app_name='yt_guesser_api')


@app.route('/channels')
def channels_list():
    return {'action': 'You choose to list all channels'}

@app.route('/channels/{channel_id}')
def channels_get(channel_id):
    return {'action': f'You choose to fetch the specific channel {channel_id}'}

@app.route('/videos')
def videos_list():
    return {'action': 'You choose to list all videos'}

@app.route('/videos/{video_id}')
def videos_get(video_id):
    return {'action': f'You choose to fetch the specific video {video_id}'}

@app.route('/transcripts')
def transcript():
    return {'action': 'You choose to list transcripts'} 


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