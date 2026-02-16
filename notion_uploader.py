import os
import re
from notion_client import Client
from datetime import datetime, timezone

def get_schema_and_map(notion, database_id):
    """
    Creates a dummy page to inspect the database schema.
    Returns a mapping of property names and the detected title property name.
    """
    try:
        # Create a dummy page to check schema
        dummy = notion.pages.create(
            parent={"database_id": database_id},
            properties={} 
        )
        
        # Get properties
        props = dummy['properties']
        schema = {}
        title_prop_name = "Name" # Default
        
        for name, prop in props.items():
            prop_type = prop['type']
            schema[name] = prop_type
            if prop['id'] == 'title':
                title_prop_name = name
                
        # Cleanup dummy page
        notion.pages.update(page_id=dummy['id'], archived=True)
        
        print(f"Detected Schema: {schema}")
        return schema, title_prop_name
        
    except Exception as e:
        print(f"Error detecting schema: {e}")
        # Default fallback
        return {}, "Name"

def parse_markdown_text(text):
    """
    Parses markdown text for bold (**text**) and returns a list of rich text objects.
    """
    parts = []
    # Regex to find **bold** text
    # This splits the text into: [normal, bold, normal, bold, ...]
    segments = re.split(r'(\*\*.*?\*\*)', text)
    
    for segment in segments:
        if segment.startswith('**') and segment.endswith('**'):
            content = segment[2:-2] # Remove **
            parts.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True, "color": "default"}
            })
        else:
            if segment: # Skip empty strings
                parts.append({
                    "type": "text",
                    "text": {"content": segment},
                    "annotations": {"bold": False, "color": "default"}
                })
    return parts

def create_heading_2(text):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": parse_markdown_text(text),
            "color": "default"
        }
    }

def create_heading_3(text):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": parse_markdown_text(text),
            "color": "default"
        }
    }

def create_paragraph(text):
    # Notion limit is 2000 chars per text object, simplified split
    if len(text) > 2000:
        text = text[:2000] + "..."
        
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": parse_markdown_text(text),
            "color": "default"
        }
    }

def create_callout(rich_text_objects, icon="👥"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich_text_objects,
            "icon": {"emoji": icon},
            "color": "gray_background"
        }
    }

def create_bullet_list_item(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": parse_markdown_text(text),
            "color": "default"
        }
    }

def create_embed(url):
    return {
        "object": "block",
        "type": "embed",
        "embed": {
            "url": url
        }
    }

def upload_to_notion(report_data):
    notion_api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_api_key or not database_id:
        print("Notion credentials missing. Skipping upload.")
        return

    notion = Client(auth=notion_api_key)
    
    # Auto-detect schema
    schema, title_prop = get_schema_and_map(notion, database_id)
    
    print(f"Uploading {len(report_data)} items to Notion...")
    
    for video in report_data:
        try:
             # Map Properties
            properties = {}
            
            # Title
            properties[title_prop] = {"title": [{"text": {"content": video.get('title', 'No Title')}}]}
            
            # URL / Link
            # FIX: Use 'link' first (from scraper), fallback to 'video_url', fallback to constructed
            video_link = video.get('link') or video.get('video_url')
            if not video_link and video.get('video_id'):
                video_link = f"https://www.youtube.com/watch?v={video.get('video_id')}"
            
            for key in schema:
                if key.lower() in ['url', 'link', 'video url']:
                    properties[key] = {"url": video_link}
                    break
                    
            # Date
            today_iso = datetime.now(timezone.utc).isoformat()
            for key in schema:
                if key.lower() in ['date', '날짜', 'published']:
                    video_date = video.get('published_at', today_iso)
                    if 'T' not in video_date:
                         video_date = today_iso 
                    properties[key] = {"date": {"start": video_date}}
                    break

            # Channel
            channel_name = video.get('channel_title', 'Unknown')
            for key, type in schema.items():
                if key.lower() in ['channel', '채널', '채널명']:
                    if type == 'select':
                        properties[key] = {"select": {"name": channel_name}}
                    elif type == 'multi_select':
                         properties[key] = {"multi_select": [{"name": channel_name}]}
                    break

            # Leaning
            leaning = video.get('political_leaning', 'Unknown')
            # FIX: Replace " - " with "/" as requested
            if isinstance(leaning, str):
                leaning = leaning.replace(" - ", "/")
                
            for key, type in schema.items():
                if key.lower() in ['classification', 'leaning', '성향', '분류']:
                    if type == 'select':
                        properties[key] = {"select": {"name": leaning}}
                    elif type == 'multi_select':
                        properties[key] = {"multi_select": [{"name": leaning}]}
                    break

            # Construct Block Content (Children)
            children = []
            
            # 1. Cast & Key Messages (Callout with nicely formatted text)
            cast_info = video.get('cast', [])
            cast_rich_text = [] # For the callout content
            
            # Header for Cast Section inside Callout
            cast_rich_text.append({
                "type": "text",
                "text": {"content": "출연진 및 핵심 메시지\n\n"},
                "annotations": {"bold": True}
            })

            if isinstance(cast_info, list):
                for person in cast_info:
                    if isinstance(person, dict):
                         name = person.get('name', 'Unknown')
                         message = person.get('key_message', '')
                         
                         # Format: "Name: Message" with Name in bold
                         cast_rich_text.append({
                             "type": "text",
                             "text": {"content": f"• {name}: "},
                             "annotations": {"bold": True}
                         })
                         cast_rich_text.append({
                             "type": "text",
                             "text": {"content": f"{message}\n"},
                             "annotations": {"bold": False}
                         })
                    elif isinstance(person, str):
                         cast_rich_text.append({
                             "type": "text",
                             "text": {"content": f"• {person}\n"}
                         })
            elif isinstance(cast_info, str):
                cast_rich_text.append({
                    "type": "text",
                    "text": {"content": cast_info}
                })
            
            # Create the Callout Block
            children.append(create_callout(cast_rich_text))
            
            # 2. Summary (Headings + Paragraphs)
            summary_text = video.get('summary', '')
            
            # Split sections by ###
            sections = summary_text.split('###')
            
            for section in sections:
                if not section.strip():
                    continue
                
                lines = section.strip().split('\n')
                header_line = lines[0].strip()
                
                # Identify header
                header_text = header_line.replace('[', '').replace(']', '').strip()
                
                # Add Heading Block (Using H3 for sleek look, or H2 if preferred)
                if header_text:
                    children.append(create_heading_3(header_text))
                
                # Process remaining lines as paragraphs or lists
                content_lines = lines[1:]
                current_paragraph = ""
                
                for line in content_lines:
                    stripped = line.strip()
                    if not stripped:
                        # Flush current paragraph on empty line to create spacing
                        if current_paragraph:
                            children.append(create_paragraph(current_paragraph))
                            current_paragraph = ""
                        continue
                        
                    # Detect bullet points in summary
                    if stripped.startswith('- ') or stripped.startswith('* ') or (stripped[0].isdigit() and stripped[1] == '.'):
                        # Flush previous paragraph
                        if current_paragraph:
                            children.append(create_paragraph(current_paragraph))
                            current_paragraph = ""
                        
                        # Add bullet item
                        clean_line = stripped[2:].strip() if stripped[1] == ' ' else stripped
                        children.append(create_bullet_list_item(clean_line))
                    else:
                        # Accumulate paragraph text. 
                        # If starting a new paragraph (current_paragraph is empty), just add.
                        # If appending, add a space.
                        if current_paragraph:
                            current_paragraph += " " + stripped
                        else:
                            current_paragraph = stripped
                
                # Flush remaining paragraph
                if current_paragraph:
                    children.append(create_paragraph(current_paragraph))
            
            # 3. Embed Video
            # Use fixed video_link
            if video_link:
                 children.append(create_embed(video_link))
            
            # Create Page
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=children
            )
            print(f"  Uploaded: {video.get('title')}")
            
        except Exception as e:
            print(f"Failed to upload {video.get('title')}: {e}")

    print(f"Notion Upload Complete: {len(report_data)} items.")
