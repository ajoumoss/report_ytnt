import os
import time
import glob
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# Configure GenAI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def download_video(video_url, output_path="temp_video"):
    """
    Downloads the video from the given URL using yt-dlp.
    Downloads the worst quality to save bandwidth/time (since we need audio/visual context, not 4k).
    Returns the path to the downloaded file.
    """
    # Clean up previous temp files
    for f in glob.glob(f"{output_path}*"):
        try:
            os.remove(f)
        except:
            pass

    ydl_opts = {
        'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best', # More robust format selection
        'outtmpl': f'{output_path}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    }

    # Add cookies if cookies.txt exists
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("  [DEBUG] Using cookies.txt for authentication.")

    print(f"  Downloading video for multimodal analysis: {video_url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Find the downloaded file (extension might vary)
        files = glob.glob(f"{output_path}*")
        if files:
            return files[0]
        return None
    except Exception as e:
        print(f"  Download failed: {e}")
        return None

def download_audio(video_url, output_path="temp_audio"):
    """
    Downloads ONLY audio (m4a/mp3) to save tokens for long videos.
    Audio tokens are significantly fewer than Video tokens.
    """
    # Clean up previous
    for f in glob.glob(f"{output_path}*"):
        try:
            os.remove(f)
        except:
            pass
            
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    print(f"  Downloading AUDIO only (token optimization): {video_url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        files = glob.glob(f"{output_path}*")
        if files:
            return files[0]
        return None
    except Exception as e:
        print(f"  Audio download failed: {e}")
        return None

def upload_to_gemini(file_path, mime_type=None):
    """
    Uploads the file to Gemini File API and waits for processing to complete.
    """
    print(f"  Uploading {file_path} to Gemini...")
    try:
        file = genai.upload_file(file_path, mime_type=mime_type)
        print(f"  Upload complete: {file.name}")
        
        # Wait for processing
        while file.state.name == "PROCESSING":
            print("  Waiting for video processing...", end="\r")
            time.sleep(2)
            file = genai.get_file(file.name)
            
        if file.state.name == "FAILED":
            print(f"  Video processing failed.")
            return None
            
        print(f"  Video ready for analysis.")
        return file
    except Exception as e:
        print(f"  Upload failed: {e}")
        return None

def process_video(video_url):
    """
    Orchestrates downloading and uploading.
    Returns the Gemini File object or None.
    """
    file_path = download_video(video_url)
    if not file_path:
        return None
        
    try:
        # Determine mime type based on extension
        mime_type = "video/mp4" # Default/Common
        if file_path.endswith(".webm"):
            mime_type = "video/webm"
            
        gemini_file = upload_to_gemini(file_path, mime_type)
        return gemini_file
    finally:
        # Cleanup local file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

def process_audio(video_url):
    """
    Orchestrates downloading audio and uploading.
    """
    file_path = download_audio(video_url)
    if not file_path:
        return None
        
    try:
        gemini_file = upload_to_gemini(file_path, "audio/mp3")
        return gemini_file
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    # ... (previous code)

def get_video_info(video_url):
    """
    Returns metadata about the video, specifically duration in seconds.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
    except Exception as e:
        print(f"  Failed to fetch video info: {e}")
        return None

def download_subtitles_text(video_url):
    """
    Downloads subtitles (manual or auto) using yt-dlp and converts them to plain text.
    Returns the transcript text or None.
    """
    import glob
    
    # Use a separate temp dir for subs to avoid confusion
    output_prefix = "temp_sub"
    
    # Clean up previous
    for f in glob.glob(f"{output_prefix}*"):
        try:
            os.remove(f)
        except:
            pass
            
    ydl_opts = {
        'skip_download': True,
        'writeautomaticsub': True,
        'writesubtitles': True,
        'subtitleslangs': ['ko', 'en'],
        'outtmpl': output_prefix,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    print(f"  Attempting to download subtitles via yt-dlp: {video_url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        # Find the .vtt file
        files = glob.glob(f"{output_prefix}*.vtt")
        if not files:
            # Try finding generic sub file if vtt not explicit
            files = glob.glob(f"{output_prefix}*")
            
        if not files:
            print("  No subtitles downloaded.")
            return None
            
        # Simple VTT to Text parsing
        vtt_file = files[0]
        text_content = []
        with open(vtt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Basic parsing: skip headers, skip timestamps (arrow -->), keep text
            for line in lines:
                line = line.strip()
                if "-->" in line:
                    continue
                if line == "" or line == "WEBVTT" or line.startswith("NOTE"):
                    continue
                # Remove tags like <c.colorE5E5E5>
                import re
                clean_line = re.sub(r'<[^>]+>', '', line)
                if clean_line and clean_line not in text_content[-1:]: # Avoid immediate dupes
                     text_content.append(clean_line)
                     
        full_text = " ".join(text_content)
        
        # Cleanup
        for f in glob.glob(f"{output_prefix}*"):
            try:
                os.remove(f)
            except:
                pass
                
        return full_text
        
    except Exception as e:
        print(f"  Subtitle download failed: {e}")
        return None

if __name__ == "__main__":
    # Test
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Roll
    # info = get_video_info(url)
    # print(f"Duration: {info.get('duration')}")
    # print(download_subtitles_text(url)[:100])
    pass
