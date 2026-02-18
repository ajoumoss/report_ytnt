import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    database_id = os.environ['NOTION_DATABASE_ID']
    print(f"Checking database: {database_id}")
    
    # Use retrieve to check if DB exists
    db = notion.databases.retrieve(database_id=database_id)
    print(f"Database Title: {db['title'][0]['plain_text']}")
    
    # Query for last 5 items
    # In notion-client 3.0.0, it is notion.databases.query
    # If it failed before, maybe I should check the object
    print(f"Debug: notion.databases type: {type(notion.databases)}")
    
    response = notion.databases.query(
        database_id=database_id,
        page_size=10
    )
    
    results = response.get('results', [])
    print(f"Found {len(results)} recent items:")
    for page in results:
        props = page['properties']
        title = "No Title"
        for k, v in props.items():
            if v['type'] == 'title' and v['title']:
                title = v['title'][0]['text']['content']
        
        created_time = page.get('created_time')
        print(f"- [{created_time}] {title}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
