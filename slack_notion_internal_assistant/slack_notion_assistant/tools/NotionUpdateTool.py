from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

class NotionUpdateTool(BaseTool):
    """
    Performs safe, targeted updates to Notion pages by appending a new paragraph block with the update instruction.
    """
    page_id: str = Field(..., description="The Notion page to update")
    update_instruction: str = Field(..., description="The user's modification request, appended as a new block")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "text": [
                    {"type": "text", "text": {"content": self.update_instruction}}
                ]
            }
        }
        notion.blocks.children.append(block_id=self.page_id, children=[block])
        return f"Added new content to Notion page {self.page_id}: '{self.update_instruction}'"

if __name__ == "__main__":
    tool = NotionUpdateTool(page_id="your-page-id", update_instruction="Add staging environment step")
    print(tool.run()) 