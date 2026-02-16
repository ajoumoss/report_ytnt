import requests
import re

url = "https://www.youtube.com/@penn1TV"
print(f"Fetching {url}...")
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
ids = list(set(re.findall(r'(UC[\w-]{22})', res.text)))
print(f"Found {len(ids)} unique IDs.")

for i, cid in enumerate(ids):
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    try:
        r = requests.head(feed_url, timeout=3)
        if r.status_code == 200:
            print(f"✅ FOUND WORKING FEED ID: {cid}")
            break
        else:
            print(f"❌ {cid}: {r.status_code}")
    except:
        pass
