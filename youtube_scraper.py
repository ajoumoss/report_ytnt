import feedparser
import datetime
from dateutil import parser
import pytz

import requests
import re

def get_channel_profile_pic(channel_id):
    """
    Fetches the profile picture URL and Subscriber Count for a YouTube channel.
    Values are cached in a simple dict to avoid redundant requests.
    Returns: (pic_url, subscriber_count)
    """
    if not hasattr(get_channel_profile_pic, "cache"):
        get_channel_profile_pic.cache = {}
    
    if channel_id in get_channel_profile_pic.cache:
        return get_channel_profile_pic.cache[channel_id]

    url = f"https://www.youtube.com/channel/{channel_id}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            pic_url = "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png"
            sub_count = "구독자 비공개"

            # 1. Profile Pic
            match = re.search(r'<meta property="og:image" content="(https://yt3.googleusercontent.com/[^"]+)"', response.text)
            if match:
                pic_url = match.group(1)
            
            # 2. Subscriber Count
            # Try generic regex for simpleText first
            # Pattern: "subscriberCountText":{"simpleText":"1.23M subscribers"}
            # Pattern: "subscriberCountText":{"simpleText":"구독자 1.23만명"}
            match_sub = re.search(r'"subscriberCountText":\{"simpleText":"(.*?)"\}', response.text)
            if match_sub:
                raw_count = match_sub.group(1)
                # Clean up common suffixes/prefixes
                sub_count = raw_count.replace(" subscribers", "").replace(" subscriber", "")
                sub_count = sub_count.replace("구독자 ", "").replace("명", "")
                sub_count = sub_count.strip()
            else:
                # If simpleText fails, sometimes it's under accessibilityData? 
                # Or maybe inconsistent JSON structure.
                # Fallback to no change if not found
                pass

            get_channel_profile_pic.cache[channel_id] = (pic_url, sub_count)
            return pic_url, sub_count
            
    except Exception as e:
        print(f"Error fetching profile/subs for {channel_id}: {e}")
    
    return "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png", ""

import json

def parse_relative_time(text):
    """
    Parses '2 hours ago', '1 day ago', etc. into a datetime object.
    """
    now = datetime.datetime.now(pytz.utc)
    text = text.lower().strip()
    
    try:
        if "second" in text:
            val = int(text.split()[0])
            return now - datetime.timedelta(seconds=val)
        if "minute" in text:
            val = int(text.split()[0])
            return now - datetime.timedelta(minutes=val)
        if "hour" in text:
            val = int(text.split()[0])
            return now - datetime.timedelta(hours=val)
        if "day" in text:
            val = int(text.split()[0])
            return now - datetime.timedelta(days=val)
        if "week" in text:
            val = int(text.split()[0])
            return now - datetime.timedelta(weeks=val)
        # Month/Year are too vague, usually means > 24h anyway
        if "month" in text:
            return now - datetime.timedelta(days=30)
        if "year" in text:
            return now - datetime.timedelta(days=365)
    except:
        pass
    return now # Fallback

def is_short(video_id):
    """
    Checks if a video is a YouTube Short by sniffing the URL redirect.
    Shorts URL: https://www.youtube.com/shorts/{video_id} -> 200 OK
    Regular Video URL: https://www.youtube.com/shorts/{video_id} -> 303 Redirect to /watch
    """
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        # Use HEAD request to allow_redirects=False
        # If 200, it's a Short. If 303/302, it's a Video.
        response = requests.head(url, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0'})
        return response.status_code == 200
    except:
        return False

def scrape_videos_fallback(channel_id, hours=24):
    print(f"⚠️  RSS failed for {channel_id}, trying HTML scraping...")
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []

        # Extract ytInitialData
        match = re.search(r'var ytInitialData = ({.*?});', response.text)
        if not match:
            return []
            
        data = json.loads(match.group(1))
        
        # Traverse JSON to find videos
        videos = []
        now = datetime.datetime.now(pytz.utc)
        
        # Helper: Get profile pic & Stats
        profile_pic, sub_count = get_channel_profile_pic(channel_id)

        def find_video_renderers(obj):
            if isinstance(obj, dict):
                if 'videoRenderer' in obj:
                    yield obj['videoRenderer']
                for k, v in obj.items():
                    yield from find_video_renderers(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from find_video_renderers(item)

        # Get first few videos (usually sorted by new)
        count = 0
        for vid in find_video_renderers(data):
            if count > 10: break # Scan top 10
            
            try:
                videoId = vid['videoId']
                title = vid['title']['runs'][0]['text']
                
                # Published time
                published_text = ""
                if 'publishedTimeText' in vid:
                    published_text = vid['publishedTimeText']['simpleText']
                
                published = parse_relative_time(published_text)
                
                # View Count
                view_count = ""
                if 'viewCountText' in vid and 'simpleText' in vid['viewCountText']:
                     view_count = vid['viewCountText']['simpleText']
                     # Format: "1.2K views" -> "1.2K" (remove 'views')
                     view_count = view_count.replace(" views", "").replace(" view", "").replace("조회수 ", "").replace("회", "")
                
                # Check hours
                time_diff = (now - published).total_seconds()
                if time_diff < hours * 3600:
                    videos.append({
                        'video_id': videoId,
                        'title': title,
                        'link': f"https://www.youtube.com/watch?v={videoId}",
                        'published': published.isoformat(),
                        'channel_title': "Unknown", 
                        'channel_profile_pic': profile_pic,
                        'subscriber_count': sub_count,
                        'view_count': view_count
                    })
                else:
                    print(f"    Skipping video (too old): {title} ({time_diff/3600:.1f} hours ago)")
                count += 1
            except Exception as e:
                continue

        return videos

    except Exception as e:
        print(f"Error scraping HTML: {e}")
        return []

import yt_dlp

def scrape_ytdlp(channel_id, hours=24, limit=10):
    """
    Scrapes videos using yt-dlp (Robust against bot detection).
    Uses the 'UU' playlist hack (All Uploads) which is much more stable.
    """
    print(f"  Attempting yt-dlp UU-playlist scrape for {channel_id}...")
    
    # UU Playlist Hack: Replace 'UC' with 'UU' in channel ID
    # Valid for all channels. UU = All Uploads playlist.
    if channel_id.startswith('UC'):
        playlist_id = 'UU' + channel_id[2:]
    else:
        playlist_id = channel_id # Fallback
        
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    found_videos = []
    now = datetime.datetime.now(pytz.utc)
    cutoff = now - datetime.timedelta(hours=hours)
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'playlistend': limit * 2 if limit else 30, # Check enough to find recent ones
        'ignoreerrors': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if not info or 'entries' not in info:
                print(f"    No entries found for playlist {playlist_id}")
                return []
                
            for entry in info['entries']:
                if not entry: continue
                
                vid_id = entry.get('id')
                title = entry.get('title')
                
                # Date Handling
                upload_date_str = entry.get('upload_date')
                timestamp = entry.get('timestamp')
                
                video_date = None
                if timestamp:
                    video_date = datetime.datetime.fromtimestamp(timestamp, pytz.utc)
                elif upload_date_str:
                     try:
                         video_date = datetime.datetime.strptime(upload_date_str, "%Y%m%d").replace(tzinfo=pytz.utc)
                     except:
                         pass
                
                is_recent = False
                if video_date:
                    if timestamp:
                        if video_date >= cutoff:
                            is_recent = True
                    else:
                        # Date only - grant 2 days buffer for safety (timezone/rounding)
                        if video_date.date() >= cutoff.date() - datetime.timedelta(days=1):
                            is_recent = True
                else:
                    # If date is missing (common with flat extract), 
                    # check first few items since entries are sorted by new.
                    if len(found_videos) < 3:
                        is_recent = True
                        video_date = now # Placeholder

                if is_recent:
                    profile_pic, sub_count = get_channel_profile_pic(channel_id)
                    found_videos.append({
                        'video_id': vid_id,
                        'title': title,
                        'link': f"https://www.youtube.com/watch?v={vid_id}",
                        'published': video_date.isoformat() if video_date else now.isoformat(),
                        'channel_title': info.get('uploader') or "Unknown",
                        'channel_profile_pic': profile_pic,
                        'subscriber_count': sub_count,
                        'view_count': entry.get('view_count') or 0
                    })
                    
                    if limit and len(found_videos) >= limit:
                        break
                        
        except Exception as e:
            print(f"    yt-dlp UU-playlist error: {e}")
                
    return found_videos

def get_recent_videos(channel_id, hours=24, limit=None):
    """
    Fetches videos uploaded in the last 'hours' from a YouTube channel.
    Order of preference:
    1. RSS Feed (Fastest, but blocked by Github Actions)
    2. yt-dlp (Robust, uses Android API)
    3. HTML Scraping (Fallback)
    """
    # 1. Try RSS
    try:
        current_videos = []
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        print(f"Fetching RSS: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        rss_ok = True
        if hasattr(feed, 'status') and feed.status == 404:
            rss_ok = False
        elif len(feed.entries) == 0:
             # Check if truly empty or broken
             if 'title' not in feed.feed or feed.feed.title == "YouTube": 
                 rss_ok = False
                 
        if rss_ok:
            # ... (Existing RSS parsing logic) ...
            # Reuse the loop from before, but abstracted?
            # For minimal change, I'll copy the logic back or refactor slightly.
            # Let's keep existing logic but wrapped.
            
            now = datetime.datetime.now(pytz.utc)
            profile_pic, sub_count = get_channel_profile_pic(channel_id)
            
            for entry in feed.entries:
                try:
                    published = parser.parse(entry.published)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=pytz.utc)
                    
                    time_diff = (now - published).total_seconds()
                    if time_diff < hours * 3600:
                        if is_short(entry.yt_videoid):
                            print(f"  Skipping Short: {entry.title}")
                            continue

                        view_count = ""
                        if hasattr(entry, 'media_statistics') and 'views' in entry.media_statistics:
                            view_count = entry.media_statistics['views']
                        
                        current_videos.append({
                            'video_id': entry.yt_videoid,
                            'title': entry.title,
                            'link': entry.link,
                            'published': published.isoformat(),
                            'channel_title': entry.author,
                            'channel_profile_pic': profile_pic,
                            'subscriber_count': sub_count,
                            'view_count': view_count
                        })
                except:
                    continue
            
            # If we found videos, return them. 
            # If RSS was "ok" (200) but empty, it might be a valid channel with no recent videos.
            # But on GH Actions, RSS often returns 403 Forbidden or similar which feedparser might mask or show as empty.
            # So if empty, we MIGHT want to try fallback anyway just in case?
            if current_videos:
                if limit: current_videos = current_videos[:limit]
                return current_videos
            
            print("  RSS returned 0 videos. Trying fallback to be sure...")

    except Exception as e:
        print(f"  RSS failed: {e}")

    # 2. Try yt-dlp (Strong Fallback)
    try:
        dlp_videos = scrape_ytdlp(channel_id, hours, limit)
        if dlp_videos:
            print(f"  ✅ yt-dlp found {len(dlp_videos)} videos.")
            if limit: dlp_videos = dlp_videos[:limit]
            return dlp_videos
    except Exception as e:
        print(f"  yt-dlp fallback failed: {e}")

    # 3. HTML Scraping (Last Resort)
    videos = scrape_videos_fallback(channel_id, hours)
    if limit: videos = videos[:limit]
    return videos

if __name__ == "__main__":
    # Test with a known active channel ID (e.g., 고성국TV)
    channel_id = "UCM8BcGB6BWKq3utIMhGKnUA" 
    print(f"Testing get_recent_videos for {channel_id}...")
    videos = get_recent_videos(channel_id, hours=48) # Use 48h to be sure to find something
    print(f"Found {len(videos)} videos:")
    for v in videos:
        print(f"- {v['title']} ({v['published']})")
