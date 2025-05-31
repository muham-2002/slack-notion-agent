from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

class NotionQueryTool(BaseTool):
    """
    Retrieves specific information from Notion pages based on user queries.
    """
    query: str = Field(..., description="The user's question or information request")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        result = notion.search(query=self.query, filter={"property": "object", "value": "page"})
        pages = result.get("results", [])[:3]
        if not pages:
            return "No pages found in Notion matching your query."
        answers = []
        for page in pages:
            # Extract page title
            title = ""
            props = page.get("properties", {})
            for prop in props.values():
                if prop.get("type") == "title":
                    title = prop["title"][0]["plain_text"]
                    break
            # Fetch first paragraph block as a summary
            children = notion.blocks.children.list(block_id=page["id"]).get("results", [])
            summary = ""
            for child in children:
                if child.get("type") == "paragraph":
                    texts = child["paragraph"].get("text", [])
                    if texts:
                        summary = texts[0].get("plain_text", "")
                    break
            answers.append(f"- {title} (ID: {page['id']}): {summary}")
        return "Found pages with summaries:\n" + "\n".join(answers)

if __name__ == "__main__":
    tool = NotionQueryTool(query="What playbook can I watch to deploy agents on Railway?")
    print(tool.run()) 