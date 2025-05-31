from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError
import json
import re
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class NotionListPageBlocksTool(BaseTool):
    """
    Lists all top-level blocks on a given Notion page, with optional recursive child listing.
    """
    page_id: str = Field(None, description="The ID of the page to list blocks from. Either this or page_query must be provided.")
    page_query: str = Field(None, description="Search query to find page by title. Used if page_id is not provided.")
    page_limit: int = Field(1, description="Number of pages to search when using page_query. Defaults to 1.")
    recursive: bool = Field(False, description="Whether to recursively list all nested child blocks.")
    format: str = Field("json", description="Response format: 'json' or 'markdown'.")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        def fetch_children(block_id: str):
            all_children = []
            start_cursor = None
            while True:
                try:
                    if start_cursor:
                        result = notion.blocks.children.list(block_id=block_id, start_cursor=start_cursor, page_size=100)
                    else:
                        result = notion.blocks.children.list(block_id=block_id, page_size=100)
                except APIResponseError:
                    # Unsupported block type, stop fetching children
                    break
                children = result.get("results", [])
                all_children.extend(children)
                if not result.get("has_more"):
                    break
                start_cursor = result.get("next_cursor")
            return all_children

        # Determine which page to list: by ID or by search query
        if self.page_query:
            # search pages by title
            search_results = notion.search(query=self.page_query, filter={"property": "object", "value": "page"})
            pages = search_results.get("results", [])[: self.page_limit]
            if not pages:
                return f"No pages found matching '{self.page_query}'."
            page_id = pages[0].get("id")
        elif self.page_id:
            page_id = self.page_id
        else:
            return "Error: either `page_id` or `page_query` must be provided to list blocks."
        # Fetch top-level blocks for the selected page
        blocks = fetch_children(page_id)
        entries = []
        for block in blocks:
            btype = block.get("type")
            # Extract human-readable content for text-based blocks
            if btype == "paragraph":
                texts = block["paragraph"].get("rich_text", [])
                content = "".join([t.get("plain_text", "") for t in texts])
            elif btype in ("heading_1", "heading_2", "heading_3"): 
                texts = block[btype].get("rich_text", [])
                content = "".join([t.get("plain_text", "") for t in texts])
            elif btype == "to_do":
                texts = block["to_do"].get("rich_text", [])
                content = "".join([t.get("plain_text", "") for t in texts])
            elif btype in ("bulleted_list_item", "numbered_list_item"): 
                texts = block[btype].get("rich_text", [])
                content = "".join([t.get("plain_text", "") for t in texts])
            else:
                # Fallback to block type for unsupported or non-text blocks
                content = btype
            entries.append({"block_id": block.get("id"), "type": btype, "content": content})
            # Recursively include children if requested
            if self.recursive:
                children = fetch_children(block.get("id"))
                for child in children:
                    ctype = child.get("type")
                    # Extract content for text-based children
                    if ctype == "paragraph":
                        texts = child["paragraph"].get("rich_text", [])
                        ccontent = "".join([t.get("plain_text", "") for t in texts])
                    elif ctype in ("heading_1", "heading_2", "heading_3"): 
                        texts = child[ctype].get("rich_text", [])
                        ccontent = "".join([t.get("plain_text", "") for t in texts])
                    elif ctype == "to_do":
                        texts = child["to_do"].get("rich_text", [])
                        ccontent = "".join([t.get("plain_text", "") for t in texts])
                    elif ctype in ("bulleted_list_item", "numbered_list_item"): 
                        texts = child[ctype].get("rich_text", [])
                        ccontent = "".join([t.get("plain_text", "") for t in texts])
                    else:
                        ccontent = ctype
                    entries.append({"block_id": child.get("id"), "type": ctype, "content": ccontent, "parent_id": block.get("id")})
        if self.format.lower() == "json":
            return json.dumps(entries, indent=2)
        # Markdown output
        lines = [f"- [{e['type']}] {e['content']} (ID: {e['block_id']})" for e in entries]
        return "\n".join(lines)

if __name__ == "__main__":
    # Test by extracting the page ID from the provided Notion page URL
    page_url = "https://www.notion.so/vrsen-ai/Mission-Statement-b0b3425c70964318980c0ecee8d0a564"
    # Extract 32-character hex ID from URL
    match = re.search(r"([0-9a-f]{32})", page_url)
    if match:
        page_id = match.group(1)
    else:
        logger.error(f"Could not extract page ID from URL: {page_url}")
        raise ValueError(f"Could not extract page ID from URL: {page_url}")
    # List all top-level blocks of the specified page in Markdown
    tool = NotionListPageBlocksTool(page_id=page_id, recursive=False, format="markdown")
    print(tool.run()) 