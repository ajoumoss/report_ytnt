import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

NOTION_API_KEY = os.environ['NOTION_API_KEY']
NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

print(f"Querying URL: {url}")

try:
    response = requests.post(url, headers=headers, json={})
    data = response.json()
    
    if response.status_code != 200:
        print(f"Error {response.status_code}: {data}")
    else:
        results = data.get('results', [])
        print(f"Found {len(results)} items in database.")
        
        for page in results:
            props = page['properties']
            title = "[No Title]"
            for key, val in props.items():
                if val['type'] == 'title' and val['title']:
                    title = val['title'][0]['text']['content']
                    break
            
            date_str = "[No Date]"
            for key, val in props.items():
                if val['type'] == 'date' and val['date']:
                    date_str = val['date']['start']
                    break
            
            print(f"- {date_str} | {title}")

except Exception as e:
    print(f"Exception: {e}")
