import requests
import re

url = "https://www.youtube.com/@penn1TV"
print(f"Fetching {url}...")
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print(f"Status: {res.status_code}")

# Find all UC ids
ids = re.findall(r'(UC[\w-]{22})', res.text)
unique_ids = list(set(ids))
print(f"Found {len(unique_ids)} unique IDs starting with UC:")
for i in unique_ids:
    print(i)

# Check specifically for externalId
match = re.search(r'"externalId":"(UC[\w-]+)"', res.text)
if match:
    print(f"externalId: {match.group(1)}")

match = re.search(r'<meta itemprop="channelId" content="(UC[\w-]+)">', res.text)
if match:
    print(f"meta channelId: {match.group(1)}")

match = re.search(r'"browseId":"(UC[\w-]+)"', res.text)
if match:
    print(f"browseId: {match.group(1)}")
