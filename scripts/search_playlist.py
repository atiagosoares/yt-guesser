import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    youtube = build('youtube', 'v3', credentials=creds)


    # Get sample channels
    request = youtube.search().list(
        part='id,snippet',
        channelId = 'UCyUBW72KU30dfAYWLVNZO8Q',
        order = 'date'
    )
    search =  request.execute()

    # Saving results
    with open('data/search_sample.json', 'w') as f:
        json.dump(search, f, indent=4)


def print_videos(videos: list):
    idx = 0
    for video in videos:
        idx += 1
        print(f'{idx}: {video["id"]} - {video["snippet"]["publishedAt"]} - {video["snippet"]["title"][:20]}... - {video["snippet"]["channelId"]} | {video["snippet"]["channelTitle"]} - ({video["snippet"]["categoryId"]})') 


if __name__ == '__main__':
    main()
