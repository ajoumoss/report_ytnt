import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    database_id = os.environ['NOTION_DATABASE_ID']
    print(f"Testing access to database: {database_id}")
    
    db = notion.databases.retrieve(database_id=database_id)
    print(f"Database Title: {db['title'][0]['plain_text']}")
    
    # Try query
    response = notion.databases.query(database_id=database_id, page_size=1)
    print(f"Query successful. Found {len(response['results'])} items.")
    
except Exception as e:
    print(f"Error: {e}")
