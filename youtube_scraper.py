import feedparser
import datetime
from dateutil import parser
import pytz
import requests
import re
import os
import json
import googleapiclient.discovery
import yt_dlp

def get_channel_profile_pic(channel_id, api_key=None):
    """
    Fetches the profile picture and subscriber count for a channel.
    Prioritizes official API, falls back to requests/regex, then yt-dlp.
    """
    if not hasattr(get_channel_profile_pic, "cache"):
        get_channel_profile_pic.cache = {}
        
    if channel_id in get_channel_profile_pic.cache:
        return get_channel_profile_pic.cache[channel_id]

    # 1. Try API if available
    if api_key:
        try:
            youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
            request = youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            response = request.execute()
            
            if response.get('items'):
                item = response['items'][0]
                pic_url = item['snippet']['thumbnails']['default']['url']
                sub_count = item['statistics'].get('subscriberCount', 'N/A')
                
                get_channel_profile_pic.cache[channel_id] = (pic_url, sub_count)
                return pic_url, sub_count
        except Exception as e:
            print(f"  [API] Info Fetch Error: {e}")

    # 2. Try Simple Request (Fastest fallback)
    try:
        url = f"https://www.youtube.com/channel/{channel_id}"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 200:
            pic_match = re.search(r'<meta property="og:image" content="(https://yt3.googleusercontent.com/[^"]+)"', resp.text)
            sub_match = re.search(r'"subscriberCountText":\{"simpleText":"(.*?)"\}', resp.text)
            
            pic_url = pic_match.group(1) if pic_match else "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png"
            sub_count = sub_match.group(1) if sub_match else "N/A"
            
            get_channel_profile_pic.cache[channel_id] = (pic_url, sub_count)
            return pic_url, sub_count
    except:
        pass

    # 3. Fallback to yt-dlp (Last resort, prone to blocking)
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True, 'nocheckcertificate': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/channel/{channel_id}", download=False)
            pic_url = info.get('thumbnails', [{}])[-1].get('url', "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png")
            sub_count = str(info.get('subscriber_count', "N/A"))
            get_channel_profile_pic.cache[channel_id] = (pic_url, sub_count)
            return pic_url, sub_count
    except:
        pass
    
    return "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png", "N/A"

def parse_relative_time(text):
    now = datetime.datetime.now(pytz.utc)
    text = text.lower().strip()
    try:
        if "second" in text: return now - datetime.timedelta(seconds=int(text.split()[0]))
        if "minute" in text: return now - datetime.timedelta(minutes=int(text.split()[0]))
        if "hour" in text: return now - datetime.timedelta(hours=int(text.split()[0]))
        if "day" in text: return now - datetime.timedelta(days=int(text.split()[0]))
        if "week" in text: return now - datetime.timedelta(weeks=int(text.split()[0]))
        if "month" in text: return now - datetime.timedelta(days=30)
        if "year" in text: return now - datetime.timedelta(days=365)
    except: pass
    return now

def is_short(video_id):
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        resp = requests.head(url, allow_redirects=False, timeout=5)
        return resp.status_code == 200
    except: return False

def get_recent_videos_api(channel_id, api_key, hours=24, limit=10):
    print(f"  [API] Fetching videos via YouTube Data API for {channel_id}...")
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        now = datetime.datetime.now(pytz.utc)
        published_after = (now - datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"  [API] Published after: {published_after}")
        
        request = youtube.search().list(
            part="snippet", channelId=channel_id, order="date", publishedAfter=published_after, maxResults=limit, type="video"
        )
        response = request.execute()
        
        found_videos = []
        print(f"  [API] Raw response items count: {len(response.get('items', []))}")
        profile_pic, sub_count = get_channel_profile_pic(channel_id, api_key)
        
        for item in response.get('items', []):
            vid_id = item['id']['videoId']
            snippet = item['snippet']
            found_videos.append({
                'video_id': vid_id, 'title': snippet['title'], 'link': f"https://www.youtube.com/watch?v={vid_id}",
                'published': snippet['publishedAt'], 'channel_title': snippet['channelTitle'],
                'channel_profile_pic': profile_pic, 'subscriber_count': sub_count, 'view_count': 0
            })
        print(f"  [API] Successfully found {len(found_videos)} videos.")
        return found_videos
    except Exception as e:
        print(f"  [API] Error: {e}")
        return []

def scrape_videos_fallback(channel_id, hours=24):
    print(f"⚠️  RSS failed for {channel_id}, trying HTML scraping...")
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200: return []
        
        # Extract JSON data from page
        html = response.text
        json_data_match = re.search(r'var ytInitialData = (\{.*?\});', html)
        if not json_data_match: return []
        
        data = json.loads(json_data_match.group(1))
        videos = []
        now = datetime.datetime.now(pytz.utc)
        
        # Traverse deep JSON structure
        try:
            tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
            video_tab = next(tab for tab in tabs if 'videos' in tab.get('tabRenderer', {}).get('endpoint', {}).get('commandMetadata', {}).get('webCommandMetadata', {}).get('url', ''))
            contents = video_tab['tabRenderer']['content']['richGridRenderer']['contents']
        except: return []

        profile_pic, sub_count = get_channel_profile_pic(channel_id)

        for content in contents:
            try:
                video_data = content['richItemRenderer']['content']['videoRenderer']
                published_text = video_data.get('publishedTimeText', {}).get('simpleText', '')
                if not published_text: continue
                
                published_date = parse_relative_time(published_text)
                time_diff = (now - published_date).total_seconds()
                
                if time_diff < hours * 3600:
                    vid_id = video_data['videoId']
                    if is_short(vid_id): continue

                    videos.append({
                        'video_id': vid_id, 'title': video_data['title']['runs'][0]['text'],
                        'link': f"https://www.youtube.com/watch?v={vid_id}",
                        'published': published_date.isoformat(),
                        'channel_title': video_data['ownerText']['runs'][0]['text'],
                        'channel_profile_pic': profile_pic, 'subscriber_count': sub_count,
                        'view_count': video_data.get('viewCountText', {}).get('simpleText', '0')
                    })
            except: continue
            
        return videos
    except Exception as e:
        print(f"Fallback Error: {e}")
        return []

def scrape_ytdlp(channel_id, api_key=None, hours=24, limit=10):
    print(f"  [DEBUG] yt-dlp UU-playlist scrape start for {channel_id}")
    playlist_id = 'UU' + channel_id[2:] if channel_id.startswith('UC') else channel_id
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    found_videos = []
    now = datetime.datetime.now(pytz.utc)
    cutoff = now - datetime.timedelta(hours=hours)
    
    ydl_opts = {
        'quiet': True, 'extract_flat': 'in_playlist', 'playlistend': 50, 'ignoreerrors': True,
        'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if not info: return []
            entries = list(info.get('entries', []))
            print(f"    [DEBUG] Found {len(entries)} raw entries in playlist.")
            
            for entry in entries:
                if not entry: continue
                vid_id = entry.get('id')
                upload_date_str = entry.get('upload_date')
                timestamp = entry.get('timestamp')
                
                video_date = datetime.datetime.fromtimestamp(timestamp, pytz.utc) if timestamp else \
                             datetime.datetime.strptime(upload_date_str, "%Y%m%d").replace(tzinfo=pytz.utc) if upload_date_str else None
                
                is_recent = False
                if video_date:
                    if timestamp: is_recent = video_date >= cutoff
                    else: is_recent = video_date.date() >= cutoff.date() - datetime.timedelta(days=1)
                else: 
                    if len(found_videos) < 5: is_recent = True; video_date = now

                if is_recent:
                    profile_pic, sub_count = get_channel_profile_pic(channel_id, api_key)
                    found_videos.append({
                        'video_id': vid_id, 'title': entry.get('title'), 'link': f"https://www.youtube.com/watch?v={vid_id}",
                        'published': video_date.isoformat() if video_date else now.isoformat(),
                        'channel_title': info.get('uploader') or entry.get('uploader') or "Unknown",
                        'channel_profile_pic': profile_pic, 'subscriber_count': sub_count,
                        'view_count': entry.get('view_count') or 0
                    })
                    if limit and len(found_videos) >= limit: break
            print(f"    [DEBUG] Successfully filtered {len(found_videos)} recent videos.")
        except Exception as e: print(f"    [DEBUG] yt-dlp UU-playlist error: {e}")
            
    return found_videos

def get_recent_videos(channel_id, hours=24, limit=None, api_key=None):
    if api_key:
        api_videos = get_recent_videos_api(channel_id, api_key, hours, limit or 10)
        if api_videos: return api_videos

    try:
        current_videos = []
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        print(f"Fetching RSS: {rss_url}")
        feed = feedparser.parse(rss_url)
        if not (hasattr(feed, 'status') and feed.status == 404) and len(feed.entries) > 0:
            now = datetime.datetime.now(pytz.utc)
            profile_pic, sub_count = get_channel_profile_pic(channel_id, api_key)
            for entry in feed.entries:
                try:
                    published = parser.parse(entry.published).replace(tzinfo=pytz.utc) if parser.parse(entry.published).tzinfo is None else parser.parse(entry.published)
                    if (now - published).total_seconds() < hours * 3600:
                        if is_short(entry.yt_videoid): continue
                        current_videos.append({
                            'video_id': entry.yt_videoid, 'title': entry.title, 'link': entry.link,
                            'published': published.isoformat(), 'channel_title': entry.author,
                            'channel_profile_pic': profile_pic, 'subscriber_count': sub_count,
                            'view_count': entry.media_statistics['views'] if hasattr(entry, 'media_statistics') else ""
                        })
                except: continue
            if current_videos:
                if limit: current_videos = current_videos[:limit]
                return current_videos
        print("  RSS returned 0 videos. Trying fallback...")
    except Exception as e: print(f"  RSS failed: {e}")

    try:
        print(f"  Trying yt-dlp fallback for {channel_id}...")
        dlp_videos = scrape_ytdlp(channel_id, api_key, hours, limit)
        if dlp_videos:
            print(f"  ✅ yt-dlp found {len(dlp_videos)} videos.")
            if limit: dlp_videos = dlp_videos[:limit]
            return dlp_videos
        else: print(f"  yt-dlp found 0 videos.")
    except Exception as e: print(f"  yt-dlp fallback failed: {e}")

    videos = scrape_videos_fallback(channel_id, hours)
    if limit: videos = videos[:limit]
    return videos
