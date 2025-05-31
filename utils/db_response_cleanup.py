def clean_notion_database_response(notion_response, database_id):
    """
    General function to clean Notion database responses based on database configuration.
    This function is scalable and can handle any database by adding its configuration.
    
    Args:
        notion_response (list): List of Notion database items
        database_id (str): The database ID to determine which configuration to use
        
    Returns:
        list[dict]: Cleaned data based on the database configuration
    """
    
    # Database-specific field configurations
    DATABASE_CONFIGS = {
        "4542b3f7-39c3-47e0-9ecd-22c58437d812": {  # Notes DB
            "name": "notes",
            "title_property": "",  # Empty string is the title property for Notes
            "fields": {
                "page_id": {"type": "id"},
                "created_by": {"type": "created_by", "property": "Created by", "extract": "name"},
                "page_title": {"type": "title", "property": ""},
                "page_url": {"type": "url"},
                "status": {"type": "status", "property": "Status"},
                "projects": {"type": "relation", "property": "Projects"},
                "tags": {"type": "multi_select", "property": "Tags"}
            }
        },
        "567db0a8-1efc-4123-9478-ef08bdb9db6a": {  # Projects DB
            "name": "projects",
            "title_property": "Project name",
            "fields": {
                "page_id": {"type": "id"},
                "created_by_name": {"type": "created_by", "property": "Created by", "extract": "name"},
                "created_by_id": {"type": "created_by", "property": "Created by", "extract": "id"},
                "project_title": {"type": "title", "property": "Project name"},
                "page_url": {"type": "url"},
                "status": {"type": "status", "property": "Status"},
                "priority": {"type": "select", "property": "Priority"},
                "git_repo": {"type": "url_property", "property": "Git Repo"},
                "project_manager_name": {"type": "people", "property": "Project Manager", "extract": "name", "single": True},
                "project_manager_id": {"type": "people", "property": "Project Manager", "extract": "id", "single": True},
                "project_type": {"type": "select", "property": "Project Type"},
                "team_members": {"type": "people", "property": "People", "extract": "full"},
                "production_url": {"type": "url_property", "property": "Production URL"},
                "staging_url": {"type": "url_property", "property": "Staging URL "},
                "tasks_count": {"type": "relation_count", "property": "Tasks"},
                "project_dates": {"type": "date_range", "property": "Dates"},
                "created_time": {"type": "timestamp", "property": "created_time"},
                "last_edited_time": {"type": "timestamp", "property": "last_edited_time"}
            }
        },
        "42fad9c5-af8f-4059-a906-ed6eedc6c571": {  # Tasks DB
            "name": "tasks",
            "title_property": "Task name",
            "fields": {
                "id": {"type": "id"},
                "created_by_user_name": {"type": "created_by", "property": "Created by", "extract": "name"},
                "created_by_user_id": {"type": "created_by", "property": "Created by", "extract": "id"},
                "title": {"type": "title", "property": "Task name"},
                "url": {"type": "url"},
                "status": {"type": "status", "property": "Status"},
                "priority": {"type": "select", "property": "Priority"},
                "task_id": {"type": "unique_id", "property": "Task ID"},
                "project_id": {"type": "relation", "property": "Project", "single": True},
                "assignee_name": {"type": "people", "property": "Assignee", "extract": "name", "single": True},
                "assignee_id": {"type": "people", "property": "Assignee", "extract": "id", "single": True},
                "due_date": {"type": "date_start", "property": "Due"},
                "urgency": {"type": "select", "property": "Urgency"},
                "category": {"type": "select", "property": "Category"},
                "tags": {"type": "multi_select", "property": "Tags"},
                "execution_time": {"type": "formula", "property": "Execution time", "formula_type": "string"},
                "over_due": {"type": "formula", "property": "Over Due", "formula_type": "boolean"},
                "created_time": {"type": "timestamp", "property": "created_time"},
                "last_edited_time": {"type": "timestamp", "property": "last_edited_time"},
                "started_time": {"type": "date_start", "property": "Started time"},
                "completed_time": {"type": "date_start", "property": "Completed Time"}
            }
        }
    }
    
    def extract_field_value(item, field_config):
        """Extract field value based on the field configuration"""
        field_type = field_config["type"]
        
        if field_type == "id":
            return item.get("id")
        
        elif field_type == "url":
            return item.get("url")
        
        elif field_type == "timestamp":
            return item.get(field_config["property"])
        
        elif field_type == "title":
            title_property = item.get("properties", {}).get(field_config["property"])
            if title_property and title_property.get("type") == "title":
                title_content = title_property.get("title", [])
                if title_content and len(title_content) > 0:
                    return title_content[0].get("plain_text")
            return None
        
        elif field_type == "created_by":
            created_by_property = item.get("properties", {}).get(field_config["property"])
            if created_by_property and created_by_property.get("type") == "created_by":
                created_by_data = created_by_property.get("created_by")
                if created_by_data and created_by_data.get("object") == "user":
                    extract_type = field_config.get("extract", "name")
                    return created_by_data.get(extract_type)
            return None
        
        elif field_type == "status":
            status_property = item.get("properties", {}).get(field_config["property"])
            if not status_property:
                # Try generic encoded property names
                encoded_names = [
                    f"notion%3A%2F%2F{DATABASE_CONFIGS.get(database_id, {}).get('name', 'unknown')}%2Fstatus_property"
                ]
                for encoded_name in encoded_names:
                    status_property = item.get("properties", {}).get(encoded_name)
                    if status_property:
                        break
            
            if status_property and status_property.get("type") == "status":
                status_data = status_property.get("status")
                if status_data:
                    return status_data.get("name")
            return None
        
        elif field_type == "select":
            select_property = item.get("properties", {}).get(field_config["property"])
            if select_property and select_property.get("type") == "select":
                select_data = select_property.get("select")
                if select_data:
                    return select_data.get("name")
            return None
        
        elif field_type == "multi_select":
            multi_select_property = item.get("properties", {}).get(field_config["property"])
            if multi_select_property and multi_select_property.get("type") == "multi_select":
                multi_select_list = multi_select_property.get("multi_select", [])
                return [tag.get("name") for tag in multi_select_list if tag.get("name")]
            return []
        
        elif field_type == "people":
            people_property = item.get("properties", {}).get(field_config["property"])
            if people_property and people_property.get("type") == "people":
                people_list = people_property.get("people", [])
                if people_list:
                    extract_type = field_config.get("extract", "name")
                    is_single = field_config.get("single", False)
                    
                    if extract_type == "full":
                        # Return full person objects with id, name, email
                        result = []
                        for person in people_list:
                            person_info = {
                                "id": person.get("id"),
                                "name": person.get("name"),
                                "email": person.get("person", {}).get("email") if person.get("person") else None
                            }
                            result.append(person_info)
                        return result
                    else:
                        # Return just names or ids
                        result = [person.get(extract_type) for person in people_list if person.get(extract_type)]
                        return result[0] if is_single and result else result
            return None if field_config.get("single") else []
        
        elif field_type == "relation":
            relation_property = item.get("properties", {}).get(field_config["property"])
            if relation_property and relation_property.get("type") == "relation":
                relation_list = relation_property.get("relation", [])
                relation_ids = [rel.get("id") for rel in relation_list if rel.get("id")]
                is_single = field_config.get("single", False)
                return relation_ids[0] if is_single and relation_ids else relation_ids
            return None if field_config.get("single") else []
        
        elif field_type == "relation_count":
            relation_property = item.get("properties", {}).get(field_config["property"])
            if relation_property and relation_property.get("type") == "relation":
                relation_list = relation_property.get("relation", [])
                return len(relation_list)
            return 0
        
        elif field_type == "url_property":
            url_property = item.get("properties", {}).get(field_config["property"])
            if url_property and url_property.get("type") == "url":
                return url_property.get("url")
            return None
        
        elif field_type == "date_start":
            date_property = item.get("properties", {}).get(field_config["property"])
            if date_property and date_property.get("type") == "date":
                date_data = date_property.get("date")
                if date_data:
                    return date_data.get("start")
            return None
        
        elif field_type == "date_range":
            date_property = item.get("properties", {}).get(field_config["property"])
            if date_property and date_property.get("type") == "date":
                date_data = date_property.get("date")
                if date_data:
                    return {
                        "start": date_data.get("start"),
                        "end": date_data.get("end")
                    }
            return None
        
        elif field_type == "unique_id":
            unique_id_property = item.get("properties", {}).get(field_config["property"])
            if unique_id_property and unique_id_property.get("type") == "unique_id":
                unique_id_data = unique_id_property.get("unique_id")
                if unique_id_data:
                    prefix = unique_id_data.get("prefix", "")
                    number = unique_id_data.get("number")
                    if number is not None:
                        return f"{prefix}{number}" if prefix else str(number)
            return None
        
        elif field_type == "formula":
            formula_property = item.get("properties", {}).get(field_config["property"])
            if formula_property and formula_property.get("type") == "formula":
                formula_data = formula_property.get("formula")
                expected_type = field_config.get("formula_type", "string")
                if formula_data and formula_data.get("type") == expected_type:
                    return formula_data.get(expected_type)
            return None
        
        return None
    
    # Validate input
    if not isinstance(notion_response, list):
        print("Error: Invalid Notion response format. notion_response is not a list.")
        return []
    
    # Get database configuration
    db_config = DATABASE_CONFIGS.get(database_id)
    if not db_config:
        print(f"Warning: No configuration found for database {database_id}. Using generic extraction.")
        # Fall back to generic extraction for unknown databases
        return _extract_generic_database_response(notion_response)
    
    cleaned_data = []
    
    for item in notion_response:
        extracted_item = {}
        
        # Extract each configured field
        for field_name, field_config in db_config["fields"].items():
            extracted_item[field_name] = extract_field_value(item, field_config)
        
        cleaned_data.append(extracted_item)
    
    return cleaned_data

def _extract_generic_database_response(notion_response):
    """
    Fallback function for databases without specific configuration.
    Extracts comprehensive information that most databases have.
    """
    cleaned_data = []
    
    for item in notion_response:
        generic_item = {
            # Basic page information
            "page_id": item.get("id"),
            "page_url": item.get("url"),
            "created_time": item.get("created_time"),
            "last_edited_time": item.get("last_edited_time"),
            "archived": item.get("archived", False),
            "in_trash": item.get("in_trash", False),
            
            # Page metadata
            "title": None,
            "icon": None,
            "parent_database_id": None,
            
            # User information
            "created_by_name": None,
            "created_by_id": None,
            "last_edited_by_name": None,
            "last_edited_by_id": None,
            
            # Common properties
            "tags": [],
            "categories": [],
            "people": [],
            "checkboxes": {},
            "dates": {},
            "urls": {},
            "rich_text_fields": {},
            "select_fields": {},
            "multi_select_fields": {},
            "numbers": {},
            "relations": {}
        }
        
        # Extract icon
        if item.get("icon"):
            if item["icon"]["type"] == "emoji":
                generic_item["icon"] = item["icon"]["emoji"]
            elif item["icon"]["type"] == "external":
                generic_item["icon"] = item["icon"]["external"]["url"]
            elif item["icon"]["type"] == "file":
                generic_item["icon"] = item["icon"]["file"]["url"]
        
        # Extract parent database ID
        parent = item.get("parent", {})
        if parent.get("type") == "database_id":
            generic_item["parent_database_id"] = parent.get("database_id")
        
        # Extract created by information from top level
        created_by = item.get("created_by", {})
        if created_by.get("object") == "user":
            generic_item["created_by_name"] = created_by.get("name")
            generic_item["created_by_id"] = created_by.get("id")
        
        # Extract last edited by information from top level
        last_edited_by = item.get("last_edited_by", {})
        if last_edited_by.get("object") == "user":
            generic_item["last_edited_by_name"] = last_edited_by.get("name")
            generic_item["last_edited_by_id"] = last_edited_by.get("id")

        
        # Extract properties comprehensively
        properties = item.get("properties", {})
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type")
            
            if prop_type == "title":
                title_content = prop_data.get("title", [])
                if title_content and len(title_content) > 0:
                    generic_item["title"] = title_content[0].get("plain_text")
            
            elif prop_type == "created_by":
                created_by_data = prop_data.get("created_by", {})
                if created_by_data.get("object") == "user":
                    # Override with property data if available (more reliable)
                    generic_item["created_by_name"] = created_by_data.get("name")
                    generic_item["created_by_id"] = created_by_data.get("id")
            
            elif prop_type == "last_edited_by":
                last_edited_by_data = prop_data.get("last_edited_by", {})
                if last_edited_by_data.get("object") == "user":
                    # Override with property data if available (more reliable)
                    generic_item["last_edited_by_name"] = last_edited_by_data.get("name")
                    generic_item["last_edited_by_id"] = last_edited_by_data.get("id")
            
            elif prop_type == "created_time":
                generic_item["created_time"] = prop_data.get("created_time")
            
            elif prop_type == "last_edited_time":
                generic_item["last_edited_time"] = prop_data.get("last_edited_time")
            
            elif prop_type == "status":
                status_data = prop_data.get("status")
                if status_data:
                    generic_item["select_fields"][prop_name] = status_data.get("name")
            
            elif prop_type == "select":
                select_data = prop_data.get("select")
                if select_data:
                    generic_item["select_fields"][prop_name] = select_data.get("name")
            
            elif prop_type == "multi_select":
                multi_select_list = prop_data.get("multi_select", [])
                if multi_select_list:
                    values = [item.get("name") for item in multi_select_list if item.get("name")]
                    generic_item["multi_select_fields"][prop_name] = values
                    
                    # Also categorize common field names
                    prop_name_lower = prop_name.lower().strip()
                    if prop_name_lower in ["tags", "tag"]:
                        generic_item["tags"].extend(values)
                    elif prop_name_lower in ["categories", "category", "category ", "types", "type"]:
                        generic_item["categories"].extend(values)
            
            elif prop_type == "people":
                people_list = prop_data.get("people", [])
                if people_list:
                    people_info = []
                    for person in people_list:
                        person_data = {
                            "id": person.get("id"),
                            "name": person.get("name"),
                            "email": person.get("person", {}).get("email") if person.get("person") else None
                        }
                        people_info.append(person_data)
                    generic_item["people"].extend(people_info)
            
            elif prop_type == "checkbox":
                checkbox_value = prop_data.get("checkbox", False)
                generic_item["checkboxes"][prop_name] = checkbox_value
            
            elif prop_type == "date":
                date_data = prop_data.get("date")
                if date_data:
                    generic_item["dates"][prop_name] = {
                        "start": date_data.get("start"),
                        "end": date_data.get("end")
                    }
            
            elif prop_type == "url":
                url_value = prop_data.get("url")
                if url_value:
                    generic_item["urls"][prop_name] = url_value
            
            elif prop_type == "rich_text":
                rich_text_list = prop_data.get("rich_text", [])
                if rich_text_list:
                    text_content = ''.join([rt.get("plain_text", "") for rt in rich_text_list])
                    if text_content.strip():
                        generic_item["rich_text_fields"][prop_name] = text_content.strip()
            
            elif prop_type == "number":
                number_value = prop_data.get("number")
                if number_value is not None:
                    generic_item["numbers"][prop_name] = number_value
            
            elif prop_type == "relation":
                relation_list = prop_data.get("relation", [])
                if relation_list:
                    relation_ids = [rel.get("id") for rel in relation_list if rel.get("id")]
                    if relation_ids:
                        generic_item["relations"][prop_name] = {
                            "ids": relation_ids,
                            "count": len(relation_ids)
                        }
            
            elif prop_type == "formula":
                formula_data = prop_data.get("formula", {})
                if formula_data:
                    formula_type = formula_data.get("type")
                    if formula_type in ["string", "number", "boolean", "date"]:
                        generic_item[f"formula_{prop_name}"] = formula_data.get(formula_type)
            
            elif prop_type == "rollup":
                rollup_data = prop_data.get("rollup", {})
                if rollup_data:
                    rollup_type = rollup_data.get("type")
                    if rollup_type in ["number", "date", "array"]:
                        generic_item[f"rollup_{prop_name}"] = rollup_data.get(rollup_type)
            
            elif prop_type == "unique_id":
                unique_id_data = prop_data.get("unique_id", {})
                if unique_id_data:
                    prefix = unique_id_data.get("prefix", "")
                    number = unique_id_data.get("number")
                    if number is not None:
                        generic_item[f"unique_id_{prop_name}"] = f"{prefix}{number}" if prefix else str(number)
        
        # Clean up empty collections
        if not generic_item["tags"]:
            del generic_item["tags"]
        if not generic_item["categories"]:
            del generic_item["categories"]
        if not generic_item["people"]:
            del generic_item["people"]
        if not generic_item["checkboxes"]:
            del generic_item["checkboxes"]
        if not generic_item["dates"]:
            del generic_item["dates"]
        if not generic_item["urls"]:
            del generic_item["urls"]
        if not generic_item["rich_text_fields"]:
            del generic_item["rich_text_fields"]
        if not generic_item["select_fields"]:
            del generic_item["select_fields"]
        if not generic_item["multi_select_fields"]:
            del generic_item["multi_select_fields"]
        if not generic_item["numbers"]:
            del generic_item["numbers"]
        if not generic_item["relations"]:
            del generic_item["relations"]
        
        # Remove None values
        generic_item = {k: v for k, v in generic_item.items() if v is not None and v != []}
        
        cleaned_data.append(generic_item)
    
    return cleaned_data

def clean_notion_search_response(notion_response):
    """
    Cleans and extracts key information from a Notion API search response.
    The search endpoint returns a mix of pages and databases with verbose metadata.
    This function extracts only the essential information for each result, plus additional
    searchable content to help users find and identify content.

    Args:
        notion_response (dict): The dictionary response from the Notion API's 
                               search endpoint.

    Returns:
        dict: A dictionary containing:
              - 'items': list of cleaned search results with enhanced searchable info
              - 'items_length': number of results
              - 'has_more': boolean indicating if more results exist
              - 'next_cursor': cursor for pagination (if any)
              - 'request_id': original request ID
    """
    if not isinstance(notion_response, dict):
        print("Error: Invalid Notion search response format. Expected dictionary.")
        return {"items": [], "items_length": 0, "has_more": False, "next_cursor": None, "request_id": None}
    
    results = notion_response.get('results', [])
    cleaned_items = []
    
    for item in results:
        object_type = item.get('object')
        
        # Initialize common fields
        cleaned_item = {
            'object_type': object_type,  # 'page' or 'database'
            'id': item.get('id'),
            'url': item.get('url'),
            'created_time': item.get('created_time'),
            'last_edited_time': item.get('last_edited_time'),
            'archived': item.get('archived', False),
            'in_trash': item.get('in_trash', False)
        }
        
        if object_type == 'page':
            # Extract page-specific information
            cleaned_item.update({
                'title': None,
                'parent_type': None,
                'parent_database_id': None,
                'parent_page_id': None,
                'status': None,
                'priority': None,
                'created_by': None,
                'assignees': [],
                'tags': [],
                'due_date': None,
                'project_relation': None,
                'rich_text_content': [],
                'select_properties': {},
                'dates': {}
            })
            
            # Extract title from properties
            properties = item.get('properties', {})
            
            # Try different title property keys
            title_keys = ['Task name', 'Project name', 'Name', '', 'title']
            for key in title_keys:
                title_prop = properties.get(key)
                if title_prop and title_prop.get('type') == 'title':
                    title_content = title_prop.get('title', [])
                    if title_content and len(title_content) > 0:
                        cleaned_item['title'] = title_content[0].get('plain_text')
                        break
            
            # Extract parent information
            parent = item.get('parent', {})
            if parent:
                cleaned_item['parent_type'] = parent.get('type')
                if parent.get('type') == 'database_id':
                    cleaned_item['parent_database_id'] = parent.get('database_id')
                elif parent.get('type') == 'page_id':
                    cleaned_item['parent_page_id'] = parent.get('page_id')
            
            # Extract status
            status_prop = properties.get('Status') or properties.get('notion%3A%2F%2Ftasks%2Fstatus_property') or properties.get('notion%3A%2F%2Fprojects%2Fstatus_property')
            if status_prop and status_prop.get('type') == 'status':
                status_data = status_prop.get('status')
                if status_data:
                    cleaned_item['status'] = status_data.get('name')
            
            # Extract priority
            priority_prop = properties.get('Priority') or properties.get('notion%3A%2F%2Ftasks%2Fpriority_property') or properties.get('notion%3A%2F%2Fprojects%2Fpriority_property')
            if priority_prop and priority_prop.get('type') == 'select':
                select_data = priority_prop.get('select')
                if select_data:
                    cleaned_item['priority'] = select_data.get('name')
            
            # Extract created by name
            created_by_prop = properties.get('Created by')
            if created_by_prop and created_by_prop.get('type') == 'created_by':
                created_by_data = created_by_prop.get('created_by')
                if created_by_data and created_by_data.get('object') == 'user':
                    cleaned_item['created_by'] = created_by_data.get('name')
            
            # Extract all people properties (assignees, project managers, etc.)
            people_fields = []
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'people':
                    people_list = prop_data.get('people', [])
                    if people_list:
                        names = [person.get('name') for person in people_list if person.get('name')]
                        if names:
                            people_fields.extend(names)
                            if prop_name.lower() in ['assignee', 'assignees', 'assigned to']:
                                cleaned_item['assignees'] = names
            
            # Extract all multi-select properties (tags, categories, etc.)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'multi_select':
                    multi_select_list = prop_data.get('multi_select', [])
                    if multi_select_list:
                        tags = [tag.get('name') for tag in multi_select_list if tag.get('name')]
                        if tags:
                            cleaned_item['tags'].extend(tags)
            
            # Extract all select properties
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'select' and prop_name not in ['Priority', 'Status']:
                    select_data = prop_data.get('select')
                    if select_data and select_data.get('name'):
                        cleaned_item['select_properties'][prop_name] = select_data.get('name')
            
            # Extract all rich_text properties (descriptions, notes, etc.)
            rich_text_fields = []
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'rich_text':
                    rich_text_list = prop_data.get('rich_text', [])
                    if rich_text_list:
                        text_content = ''.join([rt.get('plain_text', '') for rt in rich_text_list])
                        if text_content.strip():
                            rich_text_fields.append(f"{prop_name}: {text_content.strip()}")
            
            if rich_text_fields:
                cleaned_item['rich_text_content'] = rich_text_fields
            
            # Extract date properties
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'date':
                    date_data = prop_data.get('date')
                    if date_data:
                        date_info = {
                            'start': date_data.get('start'),
                            'end': date_data.get('end')
                        }
                        cleaned_item['dates'][prop_name] = date_info
                        
                        # Special handling for common date fields
                        if prop_name.lower() in ['due', 'due date', 'deadline']:
                            cleaned_item['due_date'] = date_data.get('start')
            
            # Extract URL properties (additional URLs beyond the page URL)
            additional_urls = []
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'url':
                    url = prop_data.get('url')
                    if url:
                        additional_urls.append(f"{prop_name}: {url}")
            
            if additional_urls:
                cleaned_item['additional_urls'] = additional_urls
            
            # Extract relation properties (projects, tasks, etc.)
            relations = {}
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'relation':
                    relation_list = prop_data.get('relation', [])
                    if relation_list:
                        relation_ids = [rel.get('id') for rel in relation_list if rel.get('id')]
                        if relation_ids:
                            relations[prop_name] = relation_ids
                            
                            # Special handling for project relations
                            if prop_name.lower() in ['project', 'projects']:
                                cleaned_item['project_relation'] = relation_ids[0] if relation_ids else None
            
            if relations:
                cleaned_item['relations'] = relations
        
        elif object_type == 'database':
            # Extract database-specific information
            cleaned_item.update({
                'title': None,
                'description': None,
                'parent_type': None,
                'is_inline': item.get('is_inline', False),
                'properties_count': 0,
                'properties_summary': []
            })
            
            # Extract database title
            title_info = item.get('title', [])
            if title_info and len(title_info) > 0:
                cleaned_item['title'] = title_info[0].get('plain_text')
            
            # Extract database description
            description_info = item.get('description', [])
            if description_info and len(description_info) > 0:
                cleaned_item['description'] = description_info[0].get('plain_text')
            
            # Extract parent information
            parent = item.get('parent', {})
            if parent:
                cleaned_item['parent_type'] = parent.get('type')
                if parent.get('type') == 'page_id':
                    cleaned_item['parent_page_id'] = parent.get('page_id')
                elif parent.get('type') == 'workspace':
                    cleaned_item['parent_type'] = 'workspace'
            
            # Extract database properties summary
            db_properties = item.get('properties', {})
            if db_properties:
                cleaned_item['properties_count'] = len(db_properties)
                properties_summary = []
                for prop_name, prop_info in db_properties.items():
                    prop_type = prop_info.get('type', 'unknown')
                    properties_summary.append(f"{prop_name} ({prop_type})")
                
                cleaned_item['properties_summary'] = properties_summary[:10]  # Limit to first 10 properties
        
        # Remove None values and empty lists/dicts to keep response clean
        cleaned_item = {k: v for k, v in cleaned_item.items() if v is not None and v != [] and v != {}}
        cleaned_items.append(cleaned_item)
    
    return {
        'items': cleaned_items,
        'items_length': len(cleaned_items),
        'has_more': notion_response.get('has_more', False),
        'next_cursor': notion_response.get('next_cursor'),
        'request_id': notion_response.get('request_id')
    }

# Legacy function wrappers for backward compatibility
def clean_notion_projects_response(notion_response):
    """Legacy wrapper for projects database cleanup"""
    return clean_notion_database_response(notion_response, "567db0a8-1efc-4123-9478-ef08bdb9db6a")

def clean_notion_notes_response(notion_response):
    """Legacy wrapper for notes database cleanup"""
    return clean_notion_database_response(notion_response, "4542b3f7-39c3-47e0-9ecd-22c58437d812")

def clean_notion_tasks_response(notion_response):
    """Legacy wrapper for tasks database cleanup"""
    return clean_notion_database_response(notion_response, "42fad9c5-af8f-4059-a906-ed6eedc6c571")
