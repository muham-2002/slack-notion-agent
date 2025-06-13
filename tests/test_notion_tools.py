import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from tools.NotionAgent.NotionReadTool import NotionReadTool
from tools.NotionAgent.NotionUpdateTool import NotionUpdateTool

# NotionReadTool tests
@pytest.mark.parametrize("action,params,should_raise", [
    ("search", {"query": "test"}, False),
    ("retrieve_full_page", {"page_id": "page123"}, False),
    ("retrieve_block", {"block_id": "block123"}, False),
    ("retrieve_block_children", {"block_id": "block123"}, False),
    ("query_database", {"database_id": "db123"}, False),
    ("search", {}, True),
    ("retrieve_full_page", {}, True),
    ("retrieve_block", {}, True),
    ("retrieve_block_children", {}, True),
    ("query_database", {}, True),
])
def test_notion_readtool_validation(action, params, should_raise):
    params = dict(params)
    params["action"] = action
    if should_raise:
        with pytest.raises(Exception):
            NotionReadTool(**params)
    else:
        tool = NotionReadTool(**params)
        assert tool.action == action

@patch("tools.NotionAgent.NotionReadTool.NOTION_CLIENT")
def test_notion_readtool_run_search(mock_client):
    tool = NotionReadTool(action="search", query="test")
    mock_client.search.return_value = {"results": []}
    with patch("tools.NotionAgent.NotionReadTool.clean_notion_search_response", return_value={"cleaned": True}):
        result = tool.run()
        assert "Page" in result

@patch("tools.NotionAgent.NotionReadTool.NOTION_CLIENT")
def test_notion_readtool_run_retrieve_full_page(mock_client):
    tool = NotionReadTool(action="retrieve_full_page", page_id="page123")
    mock_client.pages.retrieve.return_value = {"id": "page123"}
    with patch("tools.NotionAgent.NotionReadTool.get_blocks_recursive_full", return_value=[{"block": 1}]):
        result = tool.run()
        assert "Page" in result or "page" in result

# NotionUpdateTool tests
@pytest.mark.parametrize("action,params,should_raise", [
    ("update_page_properties", {"page_id": "page123", "property_updates": {"Status": {"select": {"name": "Done"}}}}, False),
    ("append_block", {"page_id": "page123", "new_blocks": [{"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": "Hello"}}]}}]}, False),
    ("update_page_properties", {}, True),
    ("append_block", {}, True),
])
def test_notion_updatetool_validation(action, params, should_raise):
    params = dict(params)
    params["action"] = action
    if should_raise:
        with pytest.raises(Exception):
            NotionUpdateTool(**params)
    else:
        tool = NotionUpdateTool(**params)
        assert tool.action == action

@patch("tools.NotionAgent.NotionUpdateTool.NOTION_CLIENT")
def test_notion_updatetool_run_update_page_properties(mock_client):
    tool = NotionUpdateTool(action="update_page_properties", page_id="page123", property_updates={"Status": {"select": {"name": "Done"}}})
    mock_client.pages.retrieve.return_value = {"id": "page123", "properties": {"Status": {"select": {"name": "Old"}}}}
    mock_client.pages.update.return_value = {"id": "page123", "properties": {"Status": {"select": {"name": "Done"}}}}
    result = tool.run()
    assert "Done" in result or "page123" in result

@patch("tools.NotionAgent.NotionUpdateTool.NOTION_CLIENT")
def test_notion_updatetool_run_append_block(mock_client):
    tool = NotionUpdateTool(action="append_block", page_id="page123", new_blocks=[{"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": "Hello"}}]}}])
    mock_client.blocks.children.append.return_value = {"results": [{"object": "block", "id": "block123"}]}
    result = tool.run()
    assert "block" in result or "block123" in result 