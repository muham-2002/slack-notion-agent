import os
from agency_swarm import Agent
from agency_swarm.tools.mcp import MCPServerStdio

notion_server = MCPServerStdio(
    name="Notion_Server",
    params={
        "env": {
            "NOTION_API_TOKEN": os.getenv("NOTION_API_KEY"),
            "NOTION_MARKDOWN_CONVERSION": os.getenv("NOTION_MARKDOWN_CONVERSION", "true"),
                },
        "command": "npx",
                "args": ["-y", "@suekou/mcp-notion-server"],
        },
    cache_tools_list=True
)
# Create a temporary agent
class NotionAgentMCP(Agent):
    def __init__(self):
        super().__init__(
            name="NotionAgentMCP",
            description="Temporary agent for Notion MCP queries.",
            instructions="Use the Notion MCP tools to answer the query.",
            mcp_servers=[notion_server],
            temperature=0.3,
            max_prompt_tokens=45000,
            model="gpt-4.1"
        )

    def response_validator(self, message):
        return message
