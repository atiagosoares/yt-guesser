from chalice import Chalice


app = Chalice(app_name='yt_guesser_api')


@app.route('/channels/{channel_id}')
def channels(channel_id):

    if not channel_id:
        return {'action': 'You choose to list all channels'}
    else:
        return {'action': f'You choose to fetch the specific channel {channel_id}'}

@app.route('/videos/{video_id}')
def videos(video_id):
    if not video_id:
        return {'action': 'You choose to list all videos'}
    else:
        return {'action': f'You choose to fetch the specific video {video_id}'}


@app.route('/transcripts/{video_id}')
def transcript(video_id):
    if not video_id:
        return {'action': 'You choose to list all transcripts'}
    else:
        return {'action': f'You choose to fetch the specific transcript {video_id}'}



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