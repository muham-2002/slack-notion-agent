from notion_client import Client
from dotenv import load_dotenv
import os

load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

def get_all_pages_of_database(database_id):
    pages = []
    start_cursor = None

    while True:
        response = notion.databases.query(
            **{
                "database_id": database_id,
                "start_cursor": start_cursor,
                "page_size": 100
            }
        )
        pages.extend(response.get("results", []))

        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")

    return pages

# Usage example
database_id = "4542b3f7-39c3-47e0-9ecd-22c58437d812"
all_pages = get_all_pages_of_database(database_id)

for page in all_pages:
    page_id = page["id"]
    properties = page["properties"]
    # Example: extract a title property (adjust property name as needed)
    title_property = properties.get("Name") or properties.get("Title")
    title = ""
    if title_property and title_property.get("type") == "title":
        title = "".join([t.get("plain_text", "") for t in title_property["title"]])
    print(f"Page ID: {page_id}, Title: {title}")
