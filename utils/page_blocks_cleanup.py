import json
from notion_client import Client
from notion_client.errors import APIResponseError
from dotenv import load_dotenv
import os

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

notion = Client(auth=NOTION_API_KEY)

def get_blocks_recursive_clean(block_id: str, depth: int) -> list:
    if depth <= 0:
        return []
    
    blocks_clean = []
    cursor = None
    
    while True:
        try:
            response = notion.blocks.children.list(
                block_id=block_id,
                start_cursor=cursor,
                page_size=100
            )
        except APIResponseError as e:
            # Return error message as a block
            blocks_clean.append({
                "error": f"Could not access blocks for block_id {block_id}: {str(e)}"
            })
            return blocks_clean
        
        for block in response.get("results", []):
            block_type = block["type"]
            try:
                # Extract combined text content for this block
                text_content = extract_text_from_block(block)
                
                # Recursively get children text blocks if any
                children = []
                if block.get("has_children"):
                    children = get_blocks_recursive_clean(block["id"], depth-1)
                
                # Handle child databases
                if block_type == "child_database":
                    try:
                        db_content = process_database_clean(block["id"])
                    except APIResponseError as e:
                        db_content = [{"error": f"Could not access database {block['id']}: {str(e)}"}]
                    block_data = {
                        "type": "child_database",
                        "content": db_content
                    }
                else:
                    block_data = {
                        block_type: text_content
                    }
                    if children:
                        block_data["children"] = children
                
                blocks_clean.append(block_data)
            
            except Exception as e:
                # Catch all to avoid breaking on unexpected block formats
                blocks_clean.append({
                    "error": f"Error processing block {block['id']}: {str(e)}"
                })
        
        if not response.get("has_more"):
            break
        
        cursor = response.get("next_cursor")
    
    return blocks_clean

def extract_text_from_block(block: dict) -> str:
    """Extract and combine all text content from a block"""
    block_type = block["type"]
    content = block.get(block_type, {})
    
    # For blocks with rich_text arrays (paragraph, heading, etc.)
    if "rich_text" in content:
        return "".join([t.get("plain_text", "") for t in content["rich_text"]])
    
    # For other types, try to extract text or URL if available
    if "text" in content:
        return "".join([t.get("plain_text", "") for t in content["text"]])
    
    if "title" in content:
        return "".join([t.get("plain_text", "") for t in content["title"]])
    
    if "url" in content:
        return content["url"]
    
    # Default fallback
    return str(content)

def process_database_clean(database_id: str) -> list:
    """Process database entries with cleaned page data"""
    entries = []
    cursor = None
    
    while True:
        try:
            response = notion.databases.query(
                database_id=database_id,
                start_cursor=cursor,
                page_size=100
            )
        except APIResponseError as e:
            return [{"error": f"Could not query database {database_id}: {str(e)}"}]
        
        for page in response.get("results", []):
            entries.append(process_page_clean(page))
        
        if not response.get("has_more"):
            break
        
        cursor = response.get("next_cursor")
    
    return entries

def process_page_clean(page: dict) -> dict:
    """Extract minimal page info with a cleaned title"""
    return {
        "id": page.get("id"),
        "title": extract_title(page),
        "url": page.get("url")
    }

def extract_title(page: dict) -> str:
    for key in ["Title", "Name"]:
        title_prop = page["properties"].get(key)
        if title_prop and title_prop.get("type") == "title":
            title_items = title_prop.get("title", [])
            if title_items:
                return "".join([t.get("plain_text", "") for t in title_items])
    return "Untitled"

def get_blocks_recursive_full(block_id: str, depth: int) -> list:
    """
    Get blocks with FULL structure preserved for UPDATE operations.
    This maintains all IDs, metadata, and formatting needed for Notion API updates.
    """
    if depth <= 0:
        return []
    
    blocks_full = []
    cursor = None
    
    while True:
        try:
            response = notion.blocks.children.list(
                block_id=block_id,
                start_cursor=cursor,
                page_size=100
            )
        except APIResponseError as e:
            # Return error message as a block
            blocks_full.append({
                "error": f"Could not access blocks for block_id {block_id}: {str(e)}"
            })
            return blocks_full
        
        for block in response.get("results", []):
            try:
                # Preserve FULL block structure for updates
                full_block = block.copy()
                
                # Recursively get children with full structure if any
                if block.get("has_children"):
                    # Store children in a separate key to avoid API conflicts
                    full_block["children_blocks"] = get_blocks_recursive_full(block["id"], depth-1)
                
                blocks_full.append(full_block)
            
            except Exception as e:
                # Catch all to avoid breaking on unexpected block formats
                blocks_full.append({
                    "error": f"Error processing block {block['id']}: {str(e)}"
                })
        
        if not response.get("has_more"):
            break
        
        cursor = response.get("next_cursor")
    
    return blocks_full

if __name__ == "__main__":
    # Get entire page hierarchy (3 levels deep)
    PROJECTS_PAGE_ID = "1f15bd4b-16a6-8070-a69d-e40cf4364dbb"

    clean_hierarchy = {
        "blocks": get_blocks_recursive_clean(PROJECTS_PAGE_ID, depth=10)
    }

    print(json.dumps(clean_hierarchy, indent=2))