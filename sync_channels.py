import json
import os
import re
import requests

CHANNELS_TXT = 'channels.txt'
CHANNELS_JSON = 'channels.json'

def get_channel_id_and_name(url_or_handle):
    # Construct URL
    handle = url_or_handle
    if "youtube.com/" in url_or_handle:
        parts = url_or_handle.split("youtube.com/")
        if len(parts) > 1:
            handle = parts[1].split('/')[0]
            
    if handle.startswith("UC") and len(handle) == 24:
        target_url = f"https://www.youtube.com/channel/{handle}"
    else:
        target_url = f"https://www.youtube.com/{handle}" if not handle.startswith("http") else handle
    
    print(f"🔍 Fetching info from: {target_url} ...")
    try:
        response = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch page (Status: {response.status_code})")
            return None, None

        # 1. Try to find Channel ID
        channel_id = None
        match_id = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
        if match_id:
            channel_id = match_id.group(1)
        else:
            match_id = re.search(r'<meta itemprop="channelId" content="(UC[\w-]+)">', response.text)
            if match_id:
                channel_id = match_id.group(1)
        
        # 2. Try to find Channel Name
        channel_name = None
        match_name = re.search(r'<meta property="og:title" content="([^"]+)">', response.text)
        if match_name:
            channel_name = match_name.group(1)
            channel_name = channel_name.replace(" - YouTube", "")
        else:
            match_name = re.search(r'"title":"([^"]+)"', response.text)
            if match_name:
                channel_name = match_name.group(1)
                
        return channel_id, channel_name
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None, None

def get_channel_id_from_url(url_or_handle):
    # Legacy wrapper
    cid, _ = get_channel_id_and_name(url_or_handle)
    return cid

def sync_channels():
    if not os.path.exists(CHANNELS_TXT):
        print(f"⚠️  {CHANNELS_TXT} not found!")
        return

    new_channels = []
    
    with open(CHANNELS_TXT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📂 Reading {CHANNELS_TXT}...")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # Check if line has pipes (Old format)
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            name = parts[0]
            id_or_url = parts[1]
            leaning = parts[2] if len(parts) > 2 else "Unknown"
            max_videos = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 3
            
            # Resolve ID if needed
            channel_id = get_channel_id_from_url(id_or_url)
            
        else:
            # New format: Just URL
            url = line
            print(f"🔎 Analyzing URL: {url}")
            channel_id, fetched_name = get_channel_id_and_name(url)
            
            if not channel_id:
                print(f"❌ Could not resolve: {url}")
                continue
                
            name = fetched_name if fetched_name else "Unknown Channel"
            leaning = "Unknown" # Will be determined by LLM per video
            max_videos = 3

        if channel_id:
            # Check for duplicates
            if any(c['channel_id'] == channel_id for c in new_channels):
                continue

            entry = {
                "name": name,
                "channel_id": channel_id,
                "political_leaning": leaning,
                "max_videos": max_videos
            }
            # Preserve special configs if they existed (optional, but for now defaults are fine)
            if "Ground C" in name or "이동형" in name: 
                 entry["lookback_hours"] = 120
            
            new_channels.append(entry)
            print(f"✅ Verified: {name}")


    # Save to JSON
    with open(CHANNELS_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_channels, f, indent=4, ensure_ascii=False)
    
    print(f"\n🎉 Synced {len(new_channels)} channels to {CHANNELS_JSON}")

if __name__ == "__main__":
    sync_channels()
