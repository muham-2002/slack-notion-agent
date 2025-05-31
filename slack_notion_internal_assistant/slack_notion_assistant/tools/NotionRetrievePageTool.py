from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
import json

load_dotenv()

class NotionRetrievePageTool(BaseTool):
    """
    Retrieves detailed information about a specific Notion page.
    Returns its properties in JSON or the page content as Markdown.
    """
    page_id: str = Field(..., description="The ID of the Notion page to retrieve.")
    format: str = Field("json", description="Response format: \"json\" or \"markdown\".")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        # Retrieve page metadata
        page = notion.pages.retrieve(page_id=self.page_id)
        if self.format.lower() == "markdown":
            # Retrieve page content blocks
            blocks = notion.blocks.children.list(block_id=self.page_id).get("results", [])
            md = []
            for block in blocks:
                if block.get("type") == "paragraph":
                    texts = block["paragraph"].get("text", [])
                    md.append("".join([t.get("plain_text", "") for t in texts]))
                # You can add other block types (e.g., headings) here
            return "\n\n".join(md) or "No markdown content found on this page."
        # Default to JSON output
        return json.dumps(page, indent=2)

if __name__ == "__main__":
    tool = NotionRetrievePageTool(page_id="your-page-id", format="markdown")
    print(tool.run()) 