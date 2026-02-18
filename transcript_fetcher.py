from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns the transcript as a single string.
    """
    import os
    import requests
    from http.cookiejar import MozillaCookieJar
    
    try:
        cookies_path = 'cookies.txt'
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        if os.path.exists(cookies_path):
            print(f"  [DEBUG] cookies.txt found. Path: {os.path.abspath(cookies_path)}, Size: {os.path.getsize(cookies_path)} bytes")
            try:
                cj = MozillaCookieJar(cookies_path)
                cj.load(ignore_discard=True, ignore_expires=True)
                session.cookies.update(cj)
                print(f"  [DEBUG] Successfully loaded {len(session.cookies)} cookies from {cookies_path}")
            except Exception as cookie_err:
                print(f"  [DEBUG] Error loading cookies.txt: {cookie_err}")
                # Fallback to plain file check if MozillaCookieJar fails
                with open(cookies_path, 'r') as f:
                    content_preview = f.read(100).replace('\n', '\\n')
                    print(f"  [DEBUG] cookies.txt content preview: {content_preview}")
        else:
            print(f"  [DEBUG] cookies.txt NOT found at {os.path.abspath(cookies_path)}")
        
        # Instantiate the API with the session
        yt_api = YouTubeTranscriptApi(http_client=session)
        
        # Use fetch method
        transcript_list_of_dicts = yt_api.fetch(video_id, languages=['ko', 'en'])
        
        formatter = TextFormatter()
        text_transcript = formatter.format_transcript(transcript_list_of_dicts)
        return text_transcript
    except Exception as e:
        err_msg = str(e)
        if "TooManyRequests" in type(e).__name__ or "429" in err_msg or "Sign in to confirm you’re not a bot" in err_msg:
            print(f"  [CRITICAL] YouTube transcript rate limit detected: {err_msg}")
            return "RATE_LIMITED"
        print(f"Error fetching transcript for {video_id}: {e}")
        return None

if __name__ == "__main__":
    # Test with a video ID
    # REPLACE WITH A REAL VIDEO ID FOR TESTING
    video_id = "dQw4w9WgXcQ" # Rick Roll (might not have captions allowed for API, need to check)
    transcript = get_transcript(video_id)
    if transcript:
        print(f"Transcript preview: {transcript[:500]}...")
    else:
        print("Could not fetch transcript.")
