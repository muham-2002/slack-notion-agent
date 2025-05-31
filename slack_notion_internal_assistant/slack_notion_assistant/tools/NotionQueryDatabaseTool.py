from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from notion_client import Client
import json

load_dotenv()

class NotionQueryDatabaseTool(BaseTool):
    """
    Queries a Notion database with optional filters, sorts, and pagination.
    Returns entries in JSON or a simple Markdown list.
    """
    database_id: str = Field(..., description="The ID of the database to query.")
    filter: dict = Field(None, description="Optional filter conditions as a Notion filter object.")
    sorts: list = Field(None, description="Optional sorting conditions as a list of Notion sort objects.")
    page_size: int = Field(10, description="Number of results per page (max 100).")
    start_cursor: str = Field(None, description="Cursor for pagination.")
    format: str = Field("json", description="Response format: \"json\" or \"markdown\".")

    def run(self) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        params = {"database_id": self.database_id, "page_size": self.page_size}
        if self.filter:
            params["filter"] = self.filter
        if self.sorts:
            params["sorts"] = self.sorts
        if self.start_cursor:
            params["start_cursor"] = self.start_cursor

        result = notion.databases.query(**params)
        results = result.get("results", [])
        if self.format.lower() == "markdown":
            md = []
            for page in results:
                props = page.get("properties", {})
                title = "Untitled"
                for prop in props.values():
                    if prop.get("type") == "title":
                        title = prop["title"][0].get("plain_text", "")
                        break
                md.append(f"- {title}")
            return "\n".join(md) or "No entries found in the database."
        return json.dumps(results, indent=2)

if __name__ == "__main__":
    tool = NotionQueryDatabaseTool(database_id="your-database-id", format="markdown")
    print(tool.run()) 