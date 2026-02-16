import sys
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"youtube_transcript_api location: {youtube_transcript_api.__file__}")
print(f"dir(YouTubeTranscriptApi): {dir(YouTubeTranscriptApi)}")

try:
    print(f"list_transcripts exists: {hasattr(YouTubeTranscriptApi, 'list_transcripts')}")
except Exception as e:
    print(f"Error checking attribute: {e}")
