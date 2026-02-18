import os
import video_loader

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID using yt-dlp (via video_loader).
    Returns the transcript as a single string or "RATE_LIMITED" / None.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"  [transcript_fetcher] Delegating to yt-dlp for {video_id}...")
    
    # Use the robust yt-dlp implementation in video_loader
    transcript = video_loader.download_subtitles_text(video_url)
    
    if transcript == "RATE_LIMITED":
        return "RATE_LIMITED"
    
    if not transcript:
        return None
        
    return transcript

if __name__ == "__main__":
    # Test with a video ID
    video_id = "dQw4w9WgXcQ" 
    transcript = get_transcript(video_id)
    if transcript:
        print(f"Transcript preview: {transcript[:500]}...")
    else:
        print("Could not fetch transcript.")
