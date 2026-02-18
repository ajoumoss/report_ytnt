from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import os
import requests
from http.cookiejar import MozillaCookieJar

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns the transcript as a single string.
    """
    try:
        cookies_path = 'cookies.txt'
        session = requests.Session()
        session.headers.update({
            'User-Agent': os.getenv("YOUTUBE_USER_AGENT", 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        })
        
        if os.path.exists(cookies_path):
            try:
                cj = MozillaCookieJar(cookies_path)
                cj.load(ignore_discard=True, ignore_expires=True)
                session.cookies.update(cj)
            except Exception:
                pass
        
        # Instantiate the API with the session
        yt_api = YouTubeTranscriptApi(http_client=session)
        
        # Use fetch method
        transcript_list_of_dicts = yt_api.fetch(video_id, languages=['ko', 'en'])
        
        formatter = TextFormatter()
        return formatter.format_transcript(transcript_list_of_dicts)
    except Exception as e:
        # Just return None to trigger "Subtitle Unavailable"
        return None

if __name__ == "__main__":
    # Test with a video ID
    video_id = "dQw4w9WgXcQ" 
    transcript = get_transcript(video_id)
    if transcript:
        print(f"Transcript preview: {transcript[:500]}...")
    else:
        print("Could not fetch transcript.")
