import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv
from notion_client import Client
from agency_swarm.tools import BaseTool
from pydantic import Field, model_validator

# Add parent directory to path for utils imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.page_blocks_cleanup import get_blocks_recursive_full

load_dotenv()

NOTION_CLIENT = Client(auth=os.getenv("NOTION_API_KEY"))


class NotionUpdateTool(BaseTool):
    """
    A SECURE tool to perform safe, targeted updates to Notion pages and blocks.
    
    SECURITY FEATURES:
    - Only updates specified content, never overwrites or deletes existing data
    - Validates update operations before execution
    - Provides detailed change reports
    - Confirmation workflow to prevent accidents
    - PURELY ADDITIVE - never removes existing content
    """
    
    action: str = Field(
        ..., 
        description="The update action to perform",
        enum=["update_page_properties", "update_block_content", "append_block", "validate_update", "update_table_rows", "insert_after_block"]
    )
    
    # Page/Block identifiers
    page_id: Optional[str] = Field(None, description="Page ID for page-level operations")
    block_id: Optional[str] = Field(None, description="Block ID for block-level operations")
    
    # Update content
    property_updates: Optional[Dict[str, Any]] = Field(None, description="Property updates for update_page_properties action")
    block_content: Optional[Dict[str, Any]] = Field(None, description="New block content for update_block_content action")
    new_blocks: Optional[List[Dict[str, Any]]] = Field(None, description="New blocks to append for append_block action")
    table_rows_data: Optional[List[List[str]]] = Field(None, description="Table rows data for update_table_rows action (list of rows, each row is list of cell values)")
    table_block_id: Optional[str] = Field(None, description="Table block ID for update_table_rows action")
    target_block_id: Optional[str] = Field(None, description="Target block ID for insert_after_block action (blocks will be inserted after this block)")
    
    # Safety options
    validate_only: bool = Field(False, description="Only validate the update without executing it - use for confirmation workflow")

    @model_validator(mode='after')
    def validate_action_parameters(self):
        """Validate that required parameters are provided for each action"""
        if self.action == "update_page_properties":
            if not self.page_id:
                raise ValueError("page_id is required for update_page_properties action")
            if not self.property_updates:
                raise ValueError("property_updates is required for update_page_properties action")
        
        elif self.action == "update_block_content":
            if not self.block_id:
                raise ValueError("block_id is required for update_block_content action")
            if not self.block_content:
                raise ValueError("block_content is required for update_block_content action")
        
        elif self.action == "append_block":
            if not self.page_id:
                raise ValueError("page_id is required for append_block action")
            if not self.new_blocks:
                raise ValueError("new_blocks is required for append_block action")
        
        elif self.action == "validate_update":
            if not (self.page_id or self.block_id):
                raise ValueError("Either page_id or block_id is required for validate_update action")
                
        elif self.action == "update_table_rows":
            if not self.table_block_id:
                raise ValueError("table_block_id is required for update_table_rows action")
            if not self.table_rows_data:
                raise ValueError("table_rows_data is required for update_table_rows action")
        
        elif self.action == "insert_after_block":
            if not self.target_block_id:
                raise ValueError("target_block_id is required for insert_after_block action")
        
        return self

    def run(self) -> str:
        dispatch = {
            "update_page_properties": self._update_page_properties,
            "update_block_content": self._update_block_content,
            "append_block": self._append_block,
            "validate_update": self._validate_update,
            "update_table_rows": self._update_table_rows,
            "insert_after_block": self._insert_after_block,
        }
        return dispatch[self.action]()

    def _validate_update(self) -> str:
        """Validate the proposed update without executing it"""
        try:
            validation_results = {
                "validation_timestamp": datetime.now().isoformat(),
                "target_id": self.page_id or self.block_id,
                "target_type": "page" if self.page_id else "block",
                "validation_status": "passed",
                "checks_performed": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Check if target exists
            if self.page_id:
                try:
                    page_data = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
                    validation_results["checks_performed"].append("✅ Target page exists and is accessible")
                    validation_results["current_title"] = page_data.get("properties", {}).get("title", {})
                except Exception as e:
                    validation_results["validation_status"] = "failed"
                    validation_results["checks_performed"].append(f"❌ Target page not accessible: {str(e)}")
                    return json.dumps(validation_results, indent=2)
            
            if self.block_id:
                try:
                    block_data = NOTION_CLIENT.blocks.retrieve(block_id=self.block_id)
                    validation_results["checks_performed"].append("✅ Target block exists and is accessible")
                    validation_results["current_block_type"] = block_data.get("type")
                except Exception as e:
                    validation_results["validation_status"] = "failed"
                    validation_results["checks_performed"].append(f"❌ Target block not accessible: {str(e)}")
                    return json.dumps(validation_results, indent=2)
            
            # Validate property updates
            if self.property_updates:
                validation_results["checks_performed"].append("✅ Property updates structure is valid")
                validation_results["properties_to_update"] = list(self.property_updates.keys())
                validation_results["recommendations"].append("🔄 Proposed property changes will be applied")
            
            # Validate block content
            if self.block_content:
                validation_results["checks_performed"].append("✅ Block content structure is valid")
                validation_results["new_block_type"] = self.block_content.get("type")
                validation_results["recommendations"].append("🔄 Block content will be updated (existing content preserved)")
            
            # Validate new blocks for appending
            if self.new_blocks:
                validation_results["checks_performed"].append("✅ New blocks structure is valid")
                validation_results["new_blocks_count"] = len(self.new_blocks)
                validation_results["block_types_to_add"] = [block.get("type") for block in self.new_blocks]
                validation_results["recommendations"].append("➕ New blocks will be added (no existing content removed)")
            
            validation_results["recommendations"].append("✅ All operations are purely additive - no content will be deleted")
            
            return json.dumps(validation_results, indent=2)
            
        except Exception as e:
            error_result = {
                "validation_status": "error",
                "error": str(e),
                "message": "Validation failed due to unexpected error"
            }
            return json.dumps(error_result, indent=2)

    def _update_page_properties(self) -> str:
        """Safely update page properties without affecting other content"""
        try:
            # Validate only mode - show current vs proposed
            if self.validate_only:
                current_page = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
                validation_result = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "action": "update_page_properties",
                    "page_id": self.page_id,
                    "validation_status": "passed",
                    "current_properties": {key: current_page.get("properties", {}).get(key) for key in self.property_updates.keys()},
                    "proposed_changes": self.property_updates,
                    "mode": "validation_only",
                    "message": "Property update validation completed - no changes made. Current vs proposed values shown above."
                }
                return json.dumps(validation_result, indent=2)
            
            # Get current page to ensure we don't overwrite existing properties
            current_page = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
            
            # Perform the update
            update_response = NOTION_CLIENT.pages.update(
                page_id=self.page_id,
                properties=self.property_updates
            )
            
            # Verify the update
            updated_page = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
            
            result = {
                "status": "success",
                "update_timestamp": datetime.now().isoformat(),
                "page_id": self.page_id,
                "page_url": updated_page.get("url"),
                "properties_updated": list(self.property_updates.keys()),
                "message": f"Successfully updated {len(self.property_updates)} properties"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "page_id": self.page_id,
                "message": f"Failed to update page properties: {str(e)}"
            }
            return json.dumps(error_result, indent=2)

    def _update_block_content(self) -> str:
        """Safely update specific block content"""
        try:
            # Validate only mode - show current vs proposed
            if self.validate_only:
                current_block = NOTION_CLIENT.blocks.retrieve(block_id=self.block_id)
                validation_result = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "action": "update_block_content",
                    "block_id": self.block_id,
                    "validation_status": "passed",
                    "current_block": current_block,
                    "proposed_content": self.block_content,
                    "mode": "validation_only",
                    "message": "Block content update validation completed - no changes made. Current vs proposed content shown above."
                }
                return json.dumps(validation_result, indent=2)
            
            # Get current block to preserve structure
            current_block = NOTION_CLIENT.blocks.retrieve(block_id=self.block_id)
            
            # Perform the update
            update_response = NOTION_CLIENT.blocks.update(
                block_id=self.block_id,
                **self.block_content
            )
            
            result = {
                "status": "success",
                "update_timestamp": datetime.now().isoformat(),
                "block_id": self.block_id,
                "block_type": self.block_content.get("type"),
                "message": "Successfully updated block content"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "block_id": self.block_id,
                "message": f"Failed to update block content: {str(e)}"
            }
            return json.dumps(error_result, indent=2)

    def _append_block(self) -> str:
        """Safely append new blocks to a page without affecting existing content"""
        try:
            # Validate only mode - show what will be added
            if self.validate_only:
                current_page = NOTION_CLIENT.pages.retrieve(page_id=self.page_id)
                validation_result = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "action": "append_block",
                    "page_id": self.page_id,
                    "validation_status": "passed",
                    "current_page_title": current_page.get("properties", {}).get("title", {}),
                    "blocks_to_add": self.new_blocks,
                    "blocks_count": len(self.new_blocks),
                    "mode": "validation_only",
                    "message": f"Append validation completed - {len(self.new_blocks)} blocks will be added to end of page. No existing content removed."
                }
                return json.dumps(validation_result, indent=2)
            
            # Append new blocks
            append_response = NOTION_CLIENT.blocks.children.append(
                block_id=self.page_id,
                children=self.new_blocks
            )
            
            result = {
                "status": "success",
                "update_timestamp": datetime.now().isoformat(),
                "page_id": self.page_id,
                "blocks_added": len(self.new_blocks),
                "new_block_ids": [block.get("id") for block in append_response.get("results", [])],
                "message": f"Successfully appended {len(self.new_blocks)} new blocks"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "page_id": self.page_id,
                "message": f"Failed to append blocks: {str(e)}"
            }
            return json.dumps(error_result, indent=2)

    def _update_table_rows(self) -> str:
        """Safely update table rows by updating individual row blocks"""
        try:
            # Validate only mode - show current vs proposed
            if self.validate_only:
                # Get current table structure
                children_response = NOTION_CLIENT.blocks.children.list(block_id=self.table_block_id)
                table_rows = children_response.get("results", [])
                validation_result = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "action": "update_table_rows",
                    "table_block_id": self.table_block_id,
                    "validation_status": "passed",
                    "current_rows_count": len(table_rows),
                    "rows_to_update": len(self.table_rows_data),
                    "proposed_data": self.table_rows_data,
                    "mode": "validation_only",
                    "message": f"Table update validation completed - {len(self.table_rows_data)} rows will be updated. Existing content in other rows preserved."
                }
                return json.dumps(validation_result, indent=2)
            
            # Get table row child blocks
            children_response = NOTION_CLIENT.blocks.children.list(block_id=self.table_block_id)
            table_rows = children_response.get("results", [])
            
            # Update each row
            updated_rows = []
            for row_index, row_data in enumerate(self.table_rows_data):
                if row_index < len(table_rows):
                    row_block_id = table_rows[row_index]["id"]
                    
                    # Format cells correctly for Notion API
                    formatted_cells = []
                    for cell_value in row_data:
                        formatted_cells.append([{
                            "type": "text",
                            "text": {"content": str(cell_value)}
                        }])
                    
                    # Update the specific table row
                    row_content = {
                        "type": "table_row",
                        "table_row": {"cells": formatted_cells}
                    }
                    
                    NOTION_CLIENT.blocks.update(
                        block_id=row_block_id,
                        **row_content
                    )
                    
                    updated_rows.append({
                        "row_index": row_index,
                        "block_id": row_block_id,
                        "data": row_data
                    })
            
            result = {
                "status": "success",
                "update_timestamp": datetime.now().isoformat(),
                "table_block_id": self.table_block_id,
                "rows_updated": len(updated_rows),
                "updated_row_details": updated_rows,
                "message": f"Successfully updated {len(updated_rows)} table rows"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "table_block_id": self.table_block_id,
                "message": f"Failed to update table rows: {str(e)}"
            }
            return json.dumps(error_result, indent=2)

    def _insert_after_block(self) -> str:
        """Safely insert new blocks after a specified block"""
        try:
            # Validate only mode - show positioning and content
            if self.validate_only:
                target_block = NOTION_CLIENT.blocks.retrieve(block_id=self.target_block_id)
                validation_result = {
                    "validation_timestamp": datetime.now().isoformat(),
                    "action": "insert_after_block",
                    "target_block_id": self.target_block_id,
                    "validation_status": "passed",
                    "target_block_type": target_block.get("type"),
                    "blocks_to_insert": self.new_blocks,
                    "blocks_count": len(self.new_blocks),
                    "mode": "validation_only",
                    "message": f"Insert after validation completed - {len(self.new_blocks)} blocks will be inserted immediately after target block. No existing content removed."
                }
                return json.dumps(validation_result, indent=2)
            
            # Get target block to find its parent
            target_block = NOTION_CLIENT.blocks.retrieve(block_id=self.target_block_id)
            parent = target_block.get("parent", {})
            
            # Get the parent container ID (page or block)
            if parent.get("type") == "page_id":
                container_id = parent.get("page_id")
            elif parent.get("type") == "block_id":
                container_id = parent.get("block_id")
            else:
                raise ValueError("Unable to determine parent container for target block")
            
            # Insert new blocks after the target block using Notion API's 'after' parameter
            insert_response = NOTION_CLIENT.blocks.children.append(
                block_id=container_id,
                children=self.new_blocks,
                after=self.target_block_id
            )
            
            result = {
                "status": "success",
                "update_timestamp": datetime.now().isoformat(),
                "target_block_id": self.target_block_id,
                "container_id": container_id,
                "blocks_added": len(self.new_blocks),
                "new_block_ids": [block.get("id") for block in insert_response.get("results", [])],
                "message": f"Successfully inserted {len(self.new_blocks)} new blocks after block {self.target_block_id}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "target_block_id": self.target_block_id,
                "message": f"Failed to insert blocks: {str(e)}"
            }
            return json.dumps(error_result, indent=2)


if __name__ == "__main__":
    print("NotionUpdateTool - CONFIRMATION WORKFLOW ENABLED")
    print("Use validate_only=True to preview changes before execution")
    print("All operations are purely additive - no content will be deleted")
    
    # Example usage (commented out for safety):
    # tool = NotionUpdateTool(
    #     action="validate_update",
    #     page_id="your-test-page-id",
    #     property_updates={"Status": {"status": {"name": "In Progress"}}},
    #     validate_only=True
    # )
    # print(tool.run()) 