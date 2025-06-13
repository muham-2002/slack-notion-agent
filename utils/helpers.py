import os

def limit_response_length(response: str, max_length: int = 20000, remove_whitespace: bool = True, page_number: int = 1) -> str:
    """
    Limit the response length to a fixed page_length per page, supporting pagination.
    If remove_whitespace is True, remove all whitespace from the response before paginating.
    page_number is 1-based. Returns the correct slice and a message about total pages and how to get the next page.
    page_length is taken from the NOTION_TOOL_PAGE_LENGTH env variable if not provided, otherwise defaults to 10000.
    """
    page_length = int(os.getenv("NOTION_TOOL_PAGE_LENGTH", 10000))
    
    if remove_whitespace:
        response = ''.join(response.split())
    total_length = len(response)
    if total_length == 0:
        return "[No content to display]"
    # Calculate total pages
    total_pages = (total_length + page_length - 1) // page_length
    # Clamp page_number
    page_number = max(1, min(page_number, total_pages))
    start = (page_number - 1) * page_length
    end = min(start + page_length, total_length)
    page_content = response[start:end]
    msg = f"\n\n[Page {page_number}/{total_pages}. Showing characters {start+1}-{end} of {total_length} characters. "
    if page_number < total_pages:
        msg += f"To get the next page, call the tool with page_number={page_number+1}]"
    else:
        msg += "End of content.]"
    return page_content + msg

