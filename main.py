import os
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from youtube_scraper import get_recent_videos
from transcript_fetcher import get_transcript
from llm_summarizer import summarize_transcript
from report_generator import generate_report
from notion_uploader import upload_to_notion
import json
import markdown

load_dotenv()

CSS = """
<style>
/* Apple-style CSS */
body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Apple SD Gothic Neo", "Helvetica Neue", Helvetica, Arial, sans-serif;
    line-height: 1.5; /* Apple uses tighter line-height usually around 1.4-1.5 */
    color: #1d1d1f; /* Apple's near-black */
    margin: 0;
    padding: 0;
    background-color: #ffffff;
    -webkit-font-smoothing: antialiased;
}
.container {
    max-width: 692px; /* Typical width for readable text column */
    margin: 0 auto;
    padding: 40px 20px;
}
h1 {
    font-size: 40px;
    line-height: 1.1;
    font-weight: 700;
    color: #1d1d1f;
    margin-bottom: 40px;
    letter-spacing: -0.02em;
    border-bottom: none; /* Apple style is clean, usually no border */
    text-align: left;
}
h2 {
    font-size: 24px;
    line-height: 1.3;
    font-weight: 600;
    color: #1d1d1f;
    margin-top: 50px;
    margin-bottom: 15px;
    border-bottom: none;
    letter-spacing: 0.01em;
}
h3 {
    font-size: 19px;
    line-height: 1.4;
    font-weight: 600;
    color: #1d1d1f; /* Keep headers black/dark grey */
    margin-top: 25px;
    margin-bottom: 10px;
    padding: 0;
    border: none;
    background: none;
}
p {
    font-size: 17px;
    line-height: 1.6; /* Body text needs breathing room */
    margin-bottom: 24px;
    color: #1d1d1f;
    font-weight: 400;
}
ul {
    padding-left: 20px;
    margin-bottom: 24px;
}
li {
    font-size: 17px;
    line-height: 1.6;
    margin-bottom: 10px;
    color: #1d1d1f;
}
a {
    color: #0066cc; /* Apple Blue */
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
.more-link {
    display: inline-block;
    margin-top: 8px;
    font-size: 14px;
    font-weight: 600;
}
.video-meta {
    margin-bottom: 15px; /* Space between meta and title */
    padding: 0;
    border: none;
    background: none;
    text-align: left;
}
h2 {
    margin-top: 0;
    margin-bottom: 25px;
    font-size: 24px;
    line-height: 1.3;
    font-weight: 700;
    color: #1d1d1f;
    letter-spacing: -0.015em;
    text-align: left;
}
.channel-info {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
    text-align: left;
}
.channel-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    margin-right: 8px;
    object-fit: cover;
    border: 1px solid #e5e5e5;
}
.classification-label {
    display: inline-block;
    margin-top: 4px;
    font-size: 12px;
    color: #6e6e73;
    font-weight: 500;
}
hr {
    border: 0;
    border-top: 1px solid #d2d2d7;
    margin: 50px 0;
}
.container {
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 20px;
    background-color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1d1d1f;
    text-align: left;
}
</style>
"""

def send_email(subject, body_md, recipient=None):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    if not recipient:
        recipient = os.getenv("EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print("Email credentials missing in .env. Skipping email.")
        return

    # Convert Markdown to HTML
    html_content = markdown.markdown(body_md)
    # Wrap in container for margins
    full_html = f"<html><head>{CSS}</head><body><div class='container'>{html_content}</div></body></html>"

    msg = MIMEMultipart('alternative') # Use alternative for both text and html if needed, but simple is fine.
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    # Attach HTML content
    msg.attach(MIMEText(full_html, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate YouTube Political Update Report")
    parser.add_argument("--hours", type=int, default=24, help="Time window in hours to fetch videos")
    parser.add_argument("--filter", type=str, help="Filter channels by name (partial match)")
    args = parser.parse_args()

    # Load channels
    with open('channels.json', 'r') as f:
        channels_data = json.load(f)

    # Filter channels if requested
    if args.filter:
        channels = [c for c in channels_data if args.filter in c['name']]
        print(f"Filtering channels by '{args.filter}': Found {len(channels)}")
    else:
        channels = channels_data

    print(f"Checking {len(channels)} channels...")

    processed_videos = []

    for channel in channels:
        # Determine lookback hours: use channel specific if exists, else argument default
        lookback = channel.get('lookback_hours', args.hours)
        limit = channel.get('max_videos', None)
        print(f"Checking channel: {channel['name']} ({channel.get('political_leaning', 'N/A')}) - Last {lookback} hours (Limit: {limit})...")
        
        videos = get_recent_videos(channel['channel_id'], hours=lookback, limit=limit)
        
        for video in videos:
            # Fix Unknown channel name if it occurs (e.g. fallback scraping)
            if not video.get('channel_title') or video['channel_title'] == "Unknown" or video['channel_title'] is None:
                video['channel_title'] = channel['name']
                
            print(f"  Found video: {video['title']}")
            print(f"  Fetching transcript...")
            transcript = get_transcript(video['video_id'])
            
            if not transcript:
                print(f"  No transcript found. Attempting summary based on title...")
                transcript = f"Transcript not available. Please assist by summarizing or classifying based on the Video Title: {video['title']}."

            print(f"  Summarizing and analyzing political relevance...")
            # Pass title to summarizer
            result = summarize_transcript(transcript, video['title'])
            
            # Check if it returns a dict (JSON) or string (error/legacy)
            if isinstance(result, dict):
                if result.get("is_political", True): # Default to True if uncertain, to avoid skipping
                    video['summary'] = result.get("summary", "No summary provided.")
                    
                    # Update Title to Korean if available
                    if result.get("korean_title"):
                        video['title'] = result.get("korean_title")
                        
                    # Update political leaning (classification) if the LLM provided it
                    if result.get("classification"):
                         video['political_leaning'] = result.get("classification")
                    # If not set by LLM, fallback to channel default
                    if not video.get('political_leaning') or video['political_leaning'] == 'Unknown':
                        video['political_leaning'] = channel.get('political_leaning', 'Unknown')
                        
                    # Update Cast
                    if result.get("cast"):
                        video['cast'] = result.get("cast")
                        
                    # Ensure stats are preserved (passed through from scraper)
                    # They are already in video dict
                        
                    processed_videos.append(video)
                else:
                    print(f"  Skipping non-political video: {video['title']}")
            else:
                # Fallback for errors or string response
                video['summary'] = result
                video['political_leaning'] = channel.get('political_leaning', 'Unknown')
                processed_videos.append(video)

    if processed_videos:
        print(f"Generating report for {len(processed_videos)} videos...")
        report_content = generate_report(processed_videos)
        
        with open("report.md", "w") as f:
            f.write(report_content)
        
        print("Report saved to report.md")
        
        # Send Email
        print("Sending email...")
        send_email(f"Political YouTube Report - {len(processed_videos)} Videos", report_content)
        
        # Upload to Notion
        print("Uploading to Notion...")
        upload_to_notion(processed_videos)
        
    else:
        print("No videos found to report.")

if __name__ == "__main__":
    main()
