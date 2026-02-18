import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    print(f"notion.databases methods: {dir(notion.databases)}")
    
    # Try search instead of query just to see
    # results = notion.search(query="").execute() # Legacy?
    
except Exception as e:
    print(f"Error: {e}")
