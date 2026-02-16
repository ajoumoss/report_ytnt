import requests
import re
import sys

def get_channel_id(handle):
    url = f"https://www.youtube.com/{handle}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            # Look for "externalId":"UC..."
            match = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
            if match:
                return match.group(1)
            
            # Alternative: in meta tag
            match = re.search(r'<meta itemprop="channelId" content="(UC[\w-]+)">', response.text)
            if match:
                return match.group(1)
                
    except Exception as e:
        print(f"Error fetching {handle}: {e}")
    return None

if __name__ == "__main__":
    handles = ["@groundc"]
    for h in handles:
        cid = get_channel_id(h)
        print(f"{h}: {cid}")
