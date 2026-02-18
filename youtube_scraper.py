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

def get_recent_videos(channel_id, hours=24, limit=None):
    """
    Fetches videos uploaded in the last 'hours' from a YouTube channel using RSS feed.
    Falls back to HTML scraping if RSS fails.
    """
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    print(f"Fetching RSS: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    # Check if feed is broken/404
    # feedparser often returns status 200 even for 404 pages (parsing 404 html as valid feed sometimes?)
    # But usually 'bozo' is set or entries is 0.
    # If using feedparser on 404 page, entries might be 0.
    # We should detect if it's a valid feed. Valid feeds have 'title' and 'entries'.
    
    use_fallback = False
    if hasattr(feed, 'status') and feed.status == 404:
        use_fallback = True
    elif len(feed.entries) == 0:
        # Could be no videos OR broken feed.
        # For known active channels, broken feed is likely.
        # But we don't want to define 'active' here.
        # Let's check if 'feed.title' exists. 404 page usually parses to something weird or title 'YouTube'.
        if 'title' not in feed.feed or feed.feed.title == "YouTube": 
             use_fallback = True
    
    if use_fallback:
        videos = scrape_videos_fallback(channel_id, hours)
        if limit: videos = videos[:limit]
        return videos

    videos = []
    now = datetime.datetime.now(pytz.utc)
    
    # helper: fetch profile pic & stats once per channel
    profile_pic, sub_count = get_channel_profile_pic(channel_id)
    
    for entry in feed.entries:
        try:
            published = parser.parse(entry.published)
            # Ensure published is timezone-aware and set to UTC if not
            if published.tzinfo is None:
                published = published.replace(tzinfo=pytz.utc)
            
            # Check if video is within the last 'hours'
            time_diff = (now - published).total_seconds()
            if time_diff < hours * 3600:
                # Check if it is a Short
                if is_short(entry.yt_videoid):
                    print(f"  Skipping Short: {entry.title}")
                    continue

                # Try to get view count from media_statistics
                view_count = ""
                if hasattr(entry, 'media_statistics') and 'views' in entry.media_statistics:
                    view_count = entry.media_statistics['views']
                
                videos.append({
                    'video_id': entry.yt_videoid,
                    'title': entry.title,
                    'link': entry.link,
                    'published': published.isoformat(),
                    'channel_title': entry.author,
                    'channel_profile_pic': profile_pic,
                    'subscriber_count': sub_count,
                    'view_count': view_count
                })
            else:
                # Optional: print only if it's borderline or for debug
                # print(f"  Skipping video (too old): {entry.title} ({time_diff/3600:.1f} hours ago)")
                pass
        except Exception as e:
            print(f"Error parsing entry: {e}")
            continue
            
    # Apply limit if specified
    if limit:
        videos = videos[:limit]
            
    return videos

if __name__ == "__main__":
    # Test with a known channel ID (e.g., Google's channel)
    # REPLACE WITH A REAL CHANNEL ID FOR TESTING
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw" 
    videos = get_recent_videos(channel_id)
    print(f"Found {len(videos)} videos in the last 24 hours:")
    for v in videos:
        print(f"- {v['title']} ({v['link']})")
