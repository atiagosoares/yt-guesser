from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi as YTT

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

    # List video categories
    categories = {}
    request = youtube.videoCategories().list(
        part="snippet",
        hl="en_US",
        regionCode="US"
    )
    response = request.execute()

    # Print results
    for category in response['items']:
        categories[category['id']] = category["snippet"]["title"]

    while response.get("nextPageToken"):
        page_token = response["nextPageToken"]
        request = youtube.videoCategories().list(
            part="snippet",
            hl="en_US",
            regionCode="US",
            pageToken = page_token
        )
    for category in response['items']:
        categories[category['id']] = category["snippet"]["title"]

    # List most popular videos
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="US",
        maxResults=20
    )
    response = request.execute()
    print_videos(response['items'])
    page_token = response.get('nextPageToken')
    while page_token:

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode="US",
            maxResults=20,
            pageToken = page_token
        )
        response = request.execute()
        print_videos(response['items'])
        page_token = response.get('nextPageToken')

        stop_signal = input('Stop? (S)')
        if stop_signal == 'S':
            break


def print_videos(videos: list):
    idx = 0
    for video in videos:
        idx += 1
        print(f'{idx}: {video["id"]} - {video["snippet"]["publishedAt"]} - {video["snippet"]["title"][:10]}... - {video["snippet"]["channelId"]} | {video["snippet"]["channelTitle"]} - ({video["snippet"]["categoryId"]})') 


if __name__ == '__main__':
    main()