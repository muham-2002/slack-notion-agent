from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import requests

load_dotenv()

NOTION_INTEGRATION_SECRET = os.getenv("NOTION_API_KEY")

# Utility function to search Notion for a database by name/title
def notion_search_database(name, headers=None):
    """
    Search Notion for a database by name/title. Returns the first matching ID, or None if not found.
    If multiple matches, returns a list of candidates.
    """
    if not name or not headers:
        return None
    search_url = "https://api.notion.com/v1/search"
    search_payload = {
        "query": name,
        "filter": {"value": "database", "property": "object"}
    }
    resp = requests.post(search_url, headers=headers, json=search_payload)
    if resp.status_code != 200:
        return None
    data = resp.json()
    matches = []
    for result in data.get("results", []):
        if result.get("object") == "database":
            title = ""
            if "title" in result:
                title = " ".join([t.get("plain_text", "") for t in result["title"]])
            if title.strip().lower() == name.strip().lower():
                return result.get("id")
            if name.strip().lower() in title.strip().lower():
                matches.append({"id": result.get("id"), "title": title})
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) > 1:
        return matches  # ambiguous
    return None

class GetNotionPages(BaseTool):
    """
    Queries the Notion API to return the metadata and block content of pages that meet user-supplied filters. Users can provide either IDs or human-friendly names for databases and pages. The tool will search Notion to resolve names to IDs if needed.
    """
    database_id: Optional[str] = Field(None, description="Limit query to a single database. If not provided, database_name will be used.")
    database_name: Optional[str] = Field(None, description="Database name, resolved via search if database_id absent; can be partial or full name")
    page_id: Optional[str] = Field(None, description="Fetch one page directly, skip database query")
    page_title_contains: Optional[str] = Field(None, description="Case-insensitive substring match on the page title")
    property_filters: Optional[Dict[str, Any]] = Field(None, description="{property_name: value | [value1,…]}")
    created_before: Optional[str] = Field(None, description="ISO 8601 date filter on created_time")
    created_after: Optional[str] = Field(None, description="ISO 8601 date filter on created_time")
    last_edited_before: Optional[str] = Field(None, description="ISO 8601 date filter on last_edited_time")
    last_edited_after: Optional[str] = Field(None, description="ISO 8601 date filter on last_edited_time")
    include_archived: Optional[bool] = Field(False, description="Include archived pages")
    block_depth: Optional[int] = Field(2, description="Levels of nested blocks to retrieve (1–5)")
    block_types: Optional[List[str]] = Field(None, description="Return only these block types")
    sort_by: Optional[str] = Field("last_edited_time", description="Property to sort results by")
    sort_direction: Optional[str] = Field("descending", description="Sort direction: 'ascending' or 'descending'")

    def run(self):
        if not (self.database_id or self.database_name or self.page_id):
            return {"error": "At least one of database_id, database_name, or page_id must be supplied."}
        if self.block_depth and (self.block_depth < 1 or self.block_depth > 5):
            return {"error": "block_depth must be between 1 and 5 inclusive."}
        headers = {
            "Authorization": f"Bearer {NOTION_INTEGRATION_SECRET}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        # Flexible database ID resolution
        database_id = self.database_id
        if not database_id and self.database_name:
            resolved = notion_search_database(self.database_name, headers=headers)
            if isinstance(resolved, list):
                return {"error": f"Multiple databases found matching '{self.database_name}': {[x['title'] for x in resolved]}. Please specify the exact name or use database_id.", "candidates": resolved}
            if not resolved:
                return {"error": f"Database with name '{self.database_name}' not found."}
            database_id = resolved
        # For brevity, only implement page_id direct fetch and block traversal
        if self.page_id:
            page_url = f"https://api.notion.com/v1/pages/{self.page_id}"
            page_resp = requests.get(page_url, headers=headers)
            if page_resp.status_code != 200:
                return {"error": f"Notion API error: {page_resp.status_code}", "details": page_resp.text}
            page_data = page_resp.json()
            # Clean properties
            props = page_data.get("properties", {})
            clean_props = {k: v for k, v in props.items() if v}
            # Traverse blocks
            blocks = self._get_blocks(self.page_id, headers, self.block_depth or 2, self.block_types)
            return [{
                "id": self.page_id,
                "url": page_data.get("url", ""),
                "properties": clean_props,
                "blocks": blocks
            }]
        return {"error": "Only page_id direct fetch implemented in this version."}

    def _get_blocks(self, block_id, headers, depth, block_types):
        if depth == 0:
            return []
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return []
        blocks = []
        for block in resp.json().get("results", []):
            btype = block.get("type")
            if block_types and btype not in block_types:
                continue
            plain_text = ""
            if btype in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                rich = block.get(btype, {}).get("rich_text", [])
                plain_text = " ".join([r.get("plain_text", "") for r in rich])
            elif btype == "image":
                plain_text = block.get("image", {}).get("file", {}).get("url", "")
            blocks.append({
                "block_id": block.get("id"),
                "type": btype,
                "plain_text": plain_text,
                "children": self._get_blocks(block.get("id"), headers, depth-1, block_types)
            })
        return blocks

if __name__ == "__main__":
    tool = GetNotionPages(page_id="1fb5bd4b-16a6-81c5-8a90-f07203930d72")
    print(tool.run()) 