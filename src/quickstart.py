# -*- coding: utf-8 -*-

# Sample Python code for youtube.channels.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

from youtube_transcript_api import YouTubeTranscriptApi


def main():
    transcript = YouTubeTranscriptApi.get_transcript('WKbWOZAnfXM')
    print(transcript)

if __name__ == "__main__":
    main()
