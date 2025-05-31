from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
import json

load_dotenv()

class NotionRetrieveBlockChildrenTool(BaseTool):
    """
    Retrieves children blocks of a specific Notion block.
    Outputs JSON or Markdown paragraphs.
    """
    block_id: str = Field(..., description="The ID of the parent block.")
    page_size: int = Field(10, description="Number of child blocks to retrieve (max 100).")
    start_cursor: str = Field(None, description="Pagination cursor.")
    format: str = Field("markdown", description="Response format: \"json\" or \"markdown\".")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        params = {"block_id": self.block_id, "page_size": self.page_size}
        if self.start_cursor:
            params["start_cursor"] = self.start_cursor
        result = notion.blocks.children.list(**params)
        children = result.get("results", [])
        if self.format.lower() == "markdown":
            md = []
            for block in children:
                if block.get("type") == "paragraph":
                    texts = block["paragraph"].get("text", [])
                    md.append("".join([t.get("plain_text", "") for t in texts]))
            return "\n\n".join(md) or "No paragraph children found."
        return json.dumps(children, indent=2)

if __name__ == "__main__":
    tool = NotionRetrieveBlockChildrenTool(block_id="your-block-id")
    print(tool.run()) 