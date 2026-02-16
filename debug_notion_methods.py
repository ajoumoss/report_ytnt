import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
try:
    notion = Client(auth=os.environ['NOTION_API_KEY'])
    print(f"Type of notion.databases: {type(notion.databases)}")
    print(f"Methods of notion.databases: {dir(notion.databases)}")
except Exception as e:
    print(e)
