from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
import json

load_dotenv()

class NotionRetrieveBlockTool(BaseTool):
    """
    Retrieves detailed information about a specific Notion block.
    Returns JSON or the text content for paragraph blocks.
    """
    block_id: str = Field(..., description="The ID of the block to retrieve.")
    format: str = Field("json", description="Response format: \"json\" or \"markdown\".")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        block = notion.blocks.retrieve(block_id=self.block_id)
        if self.format.lower() == "markdown" and block.get("type") == "paragraph":
            texts = block["paragraph"].get("text", [])
            return "".join([t.get("plain_text", "") for t in texts]) or ""
        return json.dumps(block, indent=2)

if __name__ == "__main__":
    tool = NotionRetrieveBlockTool(block_id="your-block-id", format="markdown")
    print(tool.run()) 