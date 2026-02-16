import json
import os
import re
import requests
import sys

CHANNELS_FILE = 'channels.json'

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        # Use indent=4 for readability, ensure_ascii=False for Korean support
        json.dump(channels, f, indent=4, ensure_ascii=False)
    print("✅ Changes saved to channels.json")

def get_channel_info(url_or_handle):
    # If full URL, extract handle or ID
    handle = url_or_handle
    if "youtube.com/" in url_or_handle:
        parts = url_or_handle.split("youtube.com/")
        if len(parts) > 1:
            handle = parts[1].split('/')[0] # get @handle or channel/ID
    
    # Ensure handle starts with @ or is a channel ID
    # If it's a channel ID (starts with UC), we can use it directly? 
    # But usually we need to fetch the page to get the Name.
    
    # Construct URL to fetch
    target_url = f"https://www.youtube.com/{handle}" if not handle.startswith("http") else handle
    
    print(f"🔍 Fetching info from {target_url}...")
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
            # Remove " - YouTube" suffix if present
            channel_name = channel_name.replace(" - YouTube", "")
        else:
            # Fallback title regex
            match_name = re.search(r'"title":"([^"]+)"', response.text)
            if match_name:
                channel_name = match_name.group(1)

        return channel_id, channel_name

    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def add_channel(channels):
    print("\n➕ Add New Channel")
    url = input("Enter YouTube Channel URL or Handle (@...): ").strip()
    if not url: return

    channel_id, channel_name = get_channel_info(url)

    if not channel_id:
        print("❌ Could not find Channel ID. Please check the URL.")
        return

    print(f"✅ Found Channel: {channel_name} ({channel_id})")

    # Check for duplicates
    for c in channels:
        if c['channel_id'] == channel_id:
            print(f"⚠️  Channel already exists as '{c['name']}'")
            return

    # Metadata input
    print("\nSelect Political Leaning:")
    print("1. 진보 (Progressive)")
    print("2. 보수 (Conservative)")
    print("3. Custom")
    choice = input("Choice (1/2/3): ").strip()
    
    leaning = "진보 (Progressive)" # Default
    if choice == '2':
        leaning = "보수 (Conservative)"
    elif choice == '3':
        leaning = input("Enter Custom Leaning: ").strip()

    max_v = input("Max Videos to analyze (Default 3): ").strip()
    max_videos = int(max_v) if max_v.isdigit() else 3

    new_channel = {
        "name": channel_name,
        "channel_id": channel_id,
        "political_leaning": leaning,
        "max_videos": max_videos
    }

    channels.append(new_channel)
    save_channels(channels)
    print(f"🎉 Successfully added '{channel_name}'!")

def remove_channel(channels):
    print("\n🗑️  Remove Channel")
    list_channels(channels)
    try:
        idx = int(input("\nEnter number to remove (0 to cancel): "))
        if idx <= 0 or idx > len(channels):
            return
        
        removed = channels.pop(idx - 1)
        save_channels(channels)
        print(f"Unsubribed from '{removed['name']}'")
    except ValueError:
        pass

def list_channels(channels):
    print(f"\n📺 Current Channels ({len(channels)}):")
    print(f"{'No.':<4} {'Name':<30} {'Leaning':<20} {'ID'}")
    print("-" * 75)
    for i, c in enumerate(channels, 1):
        print(f"{i:<4} {c['name'][:28]:<30} {c.get('political_leaning', 'N/A')[:18]:<20} {c['channel_id']}")

def main():
    while True:
        channels = load_channels()
        print("\n" + "="*30)
        print("   YouTube Channel Manager")
        print("="*30)
        print("1. ➕ Add Channel")
        print("2. 🗑️  Remove Channel")
        print("3. 📋 List Channels")
        print("4. 🚪 Exit")
        
        choice = input("\nSelect option: ").strip()

        if choice == '1':
            add_channel(channels)
        elif choice == '2':
            remove_channel(channels)
        elif choice == '3':
            list_channels(channels)
        elif choice == '4':
            print("Bye!")
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
