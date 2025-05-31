

def limit_response_length(response: str, max_length: int = 20000, remove_whitespace: bool = True) -> str:
    """
    Limit the response length to prevent overly long outputs.
    If remove_whitespace is True, remove all whitespace from the response before truncating.
    If the response is longer than max_length, truncate it and add a note.
    """
    if remove_whitespace:
        # Remove all whitespace (spaces, tabs, newlines)
        response = ''.join(response.split())
    if len(response) <= max_length:
        return response
    truncated = response[:max_length]  # Leave space for truncation message
    return f"{truncated}\n\n... [Response truncated. Total length was {len(response)} characters, showing first {len(truncated)} characters]"

