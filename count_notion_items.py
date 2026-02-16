import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    db_id = os.environ['NOTION_DATABASE_ID']
    print(f"Querying DB: {db_id}")
    
    # Simple query to get all items
    response = notion.databases.query(database_id=db_id)
    results = response.get('results', [])
    
    print(f"Found {len(results)} items in database.")
    
    for page in results:
        props = page['properties']
        title = "No Title"
        # Find title property dynamically
        for key, val in props.items():
            if val['type'] == 'title':
                if val['title']:
                    title = val['title'][0]['text']['content']
                else:
                    title = "[Empty Title]"
                break
        
        # Get Date
        date_str = "No Date"
        for key, val in props.items():
            if val['type'] == 'date':
                if val['date']:
                    date_str = val['date']['start']
                break
                
        print(f"- {date_str} | {title}")

except Exception as e:
    print(f"Error: {e}")
