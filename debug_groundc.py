from youtube_scraper import get_recent_videos
import feedparser

CHANNEL_ID = "UCQ5o6c_yY765O-iJj4SjZ4g" # 이동형TV
HOURS = 120

print(f"Fetching videos for {CHANNEL_ID} for last {HOURS} hours...")
videos = get_recent_videos(CHANNEL_ID, hours=HOURS)
print(f"Found {len(videos)} videos.")
for v in videos:
    print(f"- {v['title']} ({v['published']})")

# Debug RSS directly
print("\nDebugging RSS feed...")
rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
feed = feedparser.parse(rss_url)
print(f"Feed entries: {len(feed.entries)}")
if feed.entries:
    print(f"Most recent entry: {feed.entries[0].title} - {feed.entries[0].published}")
