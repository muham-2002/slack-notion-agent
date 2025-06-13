import json
import os
import sys
from dotenv import load_dotenv
from notion_client import Client
from agency_swarm.tools import BaseTool
from pydantic import Field, model_validator
from typing import Any, Dict, Optional

# Add parent directory to path for utils imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.page_blocks_cleanup import get_blocks_recursive_full
from utils.db_response_cleanup import clean_notion_database_response, clean_notion_search_response
from utils.helpers import limit_response_length

load_dotenv()

NOTION_CLIENT = Client(auth=os.getenv("NOTION_API_KEY"))


class NotionReadTool(BaseTool):
    """
    A tool to perform various Notion read operations: search, retrieve_full_page, retrieve_block,
    retrieve_block_children, and query_database. Each action has specific required parameters
    that are validated automatically.
    """
    action: str = Field(
        ..., 
        description="The read action to perform",
        enum=["search", "retrieve_full_page", "retrieve_block", "retrieve_block_children", "query_database"]
    )
    
    # Search parameters
    query: Optional[str] = Field(None, description="Search query text (required for search action)")
    
    # Page/Block identifiers
    page_id: Optional[str] = Field(None, description="Page ID (required for retrieve_page action)")
    block_id: Optional[str] = Field(None, description="Block ID (required for retrieve_block and retrieve_block_children actions)")
    database_id: Optional[str] = Field(None, description="Database ID (required for query_database action)")
    
    # Common optional parameters
    depth: Optional[int] = Field(10, description="Depth for recursive block retrieval (default: 10)")
    page_size: Optional[int] = Field(50, description="Number of items per page (default: 50)")
    start_cursor: Optional[str] = Field(None, description="Pagination cursor for continuing from previous query")
    page_number: Optional[int] = Field(1, description="Page number for paginated output (default: 1)")
    
    # Database query parameters
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter object for database queries")
    sorts: Optional[list] = Field(None, description="Sort criteria for database queries")

    @model_validator(mode='after')
    def validate_action_parameters(self):
        """Validate that required parameters are provided for each action"""
        if self.action == "search":
            if not self.query:
                raise ValueError("query is required for search action")
        
        elif self.action == "retrieve_full_page":
            if not self.page_id:
                raise ValueError("page_id is required for retrieve_full_page action")
        
        elif self.action == "retrieve_block":
            if not self.block_id:
                raise ValueError("block_id is required for retrieve_block action")
        
        elif self.action == "retrieve_block_children":
            if not self.block_id:
                raise ValueError("block_id is required for retrieve_block_children action")
        
        elif self.action == "query_database":
            if not self.database_id:
                raise ValueError("database_id is required for query_database action")
            # if self.database_id not in ALLOWED_DB_IDS.values():
                # raise ValueError(f"Database ID {self.database_id} is not allowed. Allowed IDs: {list(ALLOWED_DB_IDS.values())}")
        
        return self

    def run(self) -> str:
        dispatch = {
            "search": self._search,
            "retrieve_full_page": self._retrieve_full_page,
            "retrieve_block": self._retrieve_block,
            "retrieve_block_children": self._retrieve_block_children,
            "query_database": self._query_database,
        }
        return dispatch[self.action]()

    def _search(self) -> str:
        search_params = {"query": self.query}
        if self.filter:
            search_params["filter"] = self.filter
        if self.page_size:
            search_params["page_size"] = self.page_size
        if self.start_cursor:
            search_params["start_cursor"] = self.start_cursor
        
        result = NOTION_CLIENT.search(**search_params)
        # Clean the search response using the new cleanup function
        cleaned_result = clean_notion_search_response(result)
        return limit_response_length(json.dumps(cleaned_result, indent=2), page_number=self.page_number)


    def _retrieve_full_page(self) -> str:
        # Retrieve full page data
        page_data = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
        # Use shared full block extraction
        blocks = get_blocks_recursive_full(self.page_id, depth=self.depth)
        result = {
            "page": page_data,
            "blocks": blocks
        }
        return limit_response_length(json.dumps(result, indent=2), page_number=self.page_number)

    def _retrieve_block(self) -> str:
        result = NOTION_CLIENT.blocks.retrieve(block_id=self.block_id)
        return limit_response_length(json.dumps(result, indent=2), page_number=self.page_number)

    def _retrieve_block_children(self) -> str:
        # Use shared clean block extraction for children
        result = get_blocks_recursive_full(self.block_id, depth=self.depth)
        return limit_response_length(json.dumps(result, indent=2), page_number=self.page_number)

    def _query_database(self) -> str:
        # Prepare query parameters
        query_params = {
            "page_size": self.page_size,
        }
        if self.filter:
            query_params["filter"] = self.filter
        if self.sorts:
            query_params["sorts"] = self.sorts
        else:
            # Default sorting: most recently edited first
            query_params["sorts"] = [{"timestamp": "last_edited_time", "direction": "descending"}]
        if self.start_cursor:
            query_params["start_cursor"] = self.start_cursor

        # Query database once
        raw_page = NOTION_CLIENT.databases.query(database_id=self.database_id, **query_params)
        results = raw_page.get("results", [])
        
        # Use the new general cleanup function
        cleaned_results = clean_notion_database_response(results, self.database_id)
        
        has_more = raw_page.get("has_more", False)
        next_cursor = raw_page.get("next_cursor")
        
        # Return items plus pagination metadata
        result = {"items": cleaned_results, "items_length": len(cleaned_results), "has_more": has_more, "next_cursor": next_cursor}
        return limit_response_length(json.dumps(result, indent=2), page_number=self.page_number)

if __name__ == "__main__":
    # Inline tests for NotionReadTool - replace IDs with real ones before running
    NOTES_DB_ID = "4542b3f7-39c3-47e0-9ecd-22c58437d812"
    PROJECTS_DB_ID = "567db0a8-1efc-4123-9478-ef08bdb9db6a"
    TASKS_DB_ID = "42fad9c5-af8f-4059-a906-ed6eedc6c571"
    RESOURCES_DB_ID = "133455f7-9bc8-40fc-b1ff-a4eaaba85337"
    TEAM_BOARD_DB_ID = "5f9cd87b-ced0-47e3-8714-cb614b16ba8c"

    NOTES_PAGE_ID = "1f15bd4b-16a6-8070-a69d-e40cf4364dbb"
    PROJECTS_PAGE_ID = "d88e42c2-ffe2-4f4d-a4be-f7f305d9b6cb"
    TASKS_PAGE_ID = "1fb5bd4b-16a6-808e-b95d-f22786976bba"
    MUHAMMAD_PAGE_ID = "1505bd4b-16a6-802f-95c8-e5b7e9931706"
    PAGE_ID = MUHAMMAD_PAGE_ID
    BLOCK_ID = TASKS_PAGE_ID  # Use a real block_id if available
    DATABASE_ID = RESOURCES_DB_ID

    print("\n== Search Test ==")
    try:
        tool = NotionReadTool(action="search", query="How To Deploy an Agency on Cloud Run", page_size=2)
        print(tool.run())
    except Exception as e:
        print(f"Search Test Error: {e}")

    # print("\n== Retrieve Page Test ==")
    # try:
    #     tool = NotionReadTool(action="retrieve_page", page_id=PAGE_ID)
    #     print(json.dumps(tool.run(), indent=5))
    # except Exception as e:
        # print(f"Retrieve Page Test Error: {e}")

    # print("\n== Retrieve Block Test ==")
    # try:
    #     tool = NotionReadTool(action="retrieve_block", block_id=BLOCK_ID)
    #     print(json.dumps(tool.run(), indent=2))
    # except Exception as e:
    #     print(f"Retrieve Block Test Error: {e}")

    # print("\n== Retrieve Block Children Test ==")
    # try:
    #     tool = NotionReadTool(action="retrieve_block_children", block_id=BLOCK_ID, depth=2)
    #     print(json.dumps(tool.run(), indent=2))
    # except Exception as e:
    #     print(f"Retrieve Block Children Test Error: {e}")

    # print("\n== Query Database Test ==")
    # try:
    #     tool = NotionReadTool(action="query_database", database_id=DATABASE_ID, page_size=5)
    #     print(tool.run())
    # except Exception as e:
    #     print(f"Query Database Test Error: {e}")


    # print("\n== 7. Query Database with Sort (Priority DESC) ==")
    # try:
    #     priority_sort = [
    #         {
    #             "property": "Priority",
    #             "direction": "descending"
    #         }
    #     ]
    #     tool = NotionReadTool(
    #         action="query_database", 
    #         database_id=DATABASE_ID,
    #         sorts=priority_sort,
    #         page_size=5
    #     )
    #     result_str = tool.run()
    #     result = json.loads(result_str)
    #     print(f"Sorted Query (Priority DESC): Found {result['items_length']} items")
    #     for item in result['items'][:3]:
    #         print(f"- {item.get('title', 'No title')} | Priority: {item.get('priority', 'No priority')}")
    # except Exception as e:
    #     print(f"Sorted Query Test Error: {e}")
