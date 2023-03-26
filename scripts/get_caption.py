from youtube_transcript_api import YouTubeTranscriptApi
import json

def main():
    video_id = "TJ2ifmkGGus"
    # Fetch transcript
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    # Save it to file
    with open('data/sample_transcript.py', 'w') as f:
        json.dump(transcript, f)

if __name__ == "__main__":
    main()
