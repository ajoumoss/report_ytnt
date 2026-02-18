import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    print(f"notion methods: {dir(notion)}")
    
except Exception as e:
    print(f"Error: {e}")
