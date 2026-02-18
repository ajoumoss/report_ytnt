import video_loader
from llm_summarizer import summarize_video
import os

# Test with the video that failed with ffmpeg error 183
video_url = "https://www.youtube.com/watch?v=OioYJBTQp8Q" 
video_title = "Test Video: OioYJBTQp8Q"

print(f"Testing multimodal analysis for: {video_url}")

# 1. Download and Upload
video_file = video_loader.process_video(video_url)

if video_file:
    print(f"Video processed successfully: {video_file.name}")
    print(f"URI: {video_file.uri}")
    
    # 2. Summarize
    result = summarize_video(video_file, video_title)
    print("\nSummary Result:")
    print(result)
    
    # Clean up (optional, file stays in Gemini for 48h)
    # video_file.delete() 
else:
    print("Failed to process video.")
