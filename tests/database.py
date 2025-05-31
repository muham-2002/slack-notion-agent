from notion_client import Client
from dotenv import load_dotenv
import os

load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

def get_all_databases():
    databases = []
    start_cursor = None

    while True:
        response = notion.search(
            filter={"property": "object", "value": "database"},
            start_cursor=start_cursor,
            page_size=100
        )
        for result in response.get("results", []):
            # Confirm object type is database
            if result.get("object") == "database":
                databases.append({
                    "id": result["id"],
                    "title": "".join([t.get("plain_text", "") for t in result.get("title", [])])
                })

        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")

    return databases

# Usage
all_databases = get_all_databases()
for db in all_databases:
    print(f"Database ID: {db['id']}, Title: {db['title']}")
