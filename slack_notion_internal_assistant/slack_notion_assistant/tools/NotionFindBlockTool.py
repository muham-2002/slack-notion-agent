from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
import json

load_dotenv()

class NotionFindBlockTool(BaseTool):
    """
    Searches for blocks across Notion pages whose content contains the given query.
    Returns matching block snippets, page titles, and block IDs.
    """
    query: str = Field(..., description="Text to search for within block content")
    page_limit: int = Field(5, description="Number of top pages to search")
    block_limit: int = Field(50, description="Maximum number of blocks to inspect per page")
    format: str = Field("markdown", description="Output format: ""json"" or ""markdown""")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        # Search for pages related to query
        search_results = notion.search(query=self.query, filter={"property": "object", "value": "page"})
        pages = search_results.get("results", [])[: self.page_limit]
        matches = []
        for page in pages:
            page_id = page.get("id")
            # Extract page title if exists
            title = page.get("properties", {}).get("title", {}).get("title", [])
            page_title = title[0].get("plain_text") if title else page_id
            # Fetch child blocks
            children = notion.blocks.children.list(block_id=page_id, page_size=self.block_limit).get("results", [])
            for block in children:
                if block.get("type") == "paragraph":
                    text_entries = block["paragraph"].get("text", [])
                    content = "".join([t.get("plain_text", "") for t in text_entries])
                    if self.query.lower() in content.lower():
                        matches.append({
                            "page_title": page_title,
                            "page_id": page_id,
                            "block_id": block.get("id"),
                            "content": content.strip()
                        })
        if not matches:
            return f"No blocks found containing '{self.query}'."
        if self.format.lower() == "json":
            return json.dumps(matches, indent=2)
        # Markdown output
        lines = [f"- [{m['content']}] (Page: {m['page_title']}, Block ID: {m['block_id']})" for m in matches]
        return "\n".join(lines)

if __name__ == "__main__":
    tool = NotionFindBlockTool(query="your search text", page_limit=3, block_limit=20)
    print(tool.run()) 