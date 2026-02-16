from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns the transcript as a single string.
    """
    try:
        # Instantiate the API
        yt_api = YouTubeTranscriptApi()
        
        # Use fetch method which handles list -> find -> fetch
        # It defaults to English, so we need to specify languages if we want Korean
        # The fetch method signature in this version: fetch(video_id, languages, preserve_formatting)
        transcript_list_of_dicts = yt_api.fetch(video_id, languages=['ko', 'en'])
        
        formatter = TextFormatter()
        text_transcript = formatter.format_transcript(transcript_list_of_dicts)
        return text_transcript
    except Exception as e:
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
