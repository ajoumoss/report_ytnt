import json
import datetime
import pytz
from youtube_scraper import get_recent_videos

def debug_coverage():
    with open('channels.json', 'r') as f:
        channels = json.load(f)
        
    print(f"Loaded {len(channels)} channels.")
    
    now = datetime.datetime.now(pytz.utc)
    one_day_ago = now - datetime.timedelta(hours=24)
    
    results = []
    
    for channel in channels:
        name = channel['name']
        channel_id = channel['channel_id']
        print(f"\nChecking {name} ({channel_id})...")
        
        try:
            videos = get_recent_videos(channel_id, hours=24)
            found_videos = []
            if videos:
                for v in videos:
                    found_videos.append(f"{v['title']} ({v['published']})")
                status = f"✅ OK ({len(found_videos)} in 24h)"
            else:
                status = "⚠️  No videos in 24h"
        except Exception as e:
            status = f"❌ Error: {e}"
            
        results.append(f"{name:<30} | {status}")

    print("\n" + "="*80)
    print("COVERAGE REPORT")
    print("="*80)
    for res in results:
        print(res)

if __name__ == "__main__":
    debug_coverage()
