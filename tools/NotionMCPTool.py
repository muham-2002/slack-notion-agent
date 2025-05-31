import os
from dotenv import load_dotenv
from typing import Any
from agency_swarm.tools.mcp import MCPServerStdio
from agency_swarm.tools import BaseTool
from pydantic import Field
from agency_swarm import Agent
from agency_swarm.agency import Agency

load_dotenv()


# This is a workaround for enabling the use of MCP tools in agencii.ai
# TODO: Refactor this once MCP integration in agencii.ai is complete
class NotionMCPTool(BaseTool):
    """
    Sends a query to Notion via an internal MCPServer and Agent, wrapped in a minimal Agency. The agent decides which Notion MCP tool and arguments to use based on the query.
    """
    query: str = Field(..., description="The query for retrieving information from Notion (the agent will decide how to handle it)")

    def run(self) -> Any:
        # Setup MCPServer for Notion
        notion_server = MCPServerStdio(
            name="Notion_Server",
            params={
                "env": {
                    "NOTION_API_TOKEN": os.getenv("NOTION_API_KEY"),
                    # Enable markdown conversion for more concise output
                    "NOTION_MARKDOWN_CONVERSION": os.getenv("NOTION_MARKDOWN_CONVERSION", "true"),
                },
                "command": "npx",
                "args": ["-y", "@suekou/mcp-notion-server"],
            },
            cache_tools_list=True
        )
        # Create a temporary agent
        class _NotionAgent(Agent):
            def __init__(self):
                super().__init__(
                    name="NotionAgent",
                    description="Temporary agent for Notion MCP queries.",
                    instructions="Use the Notion MCP tools to answer the query.",
                    mcp_servers=[notion_server],
                    temperature=0.3,
                    max_prompt_tokens=25000,
                    model="gpt-4.1"
                )
            def response_validator(self, message):
                return message
        agent = _NotionAgent()
        # Create a minimal Agency with this agent as CEO
        agency = Agency([
            agent
        ])
        # Use the agency to get a completion from the agent
        try:
            result = agency.get_completion(self.query)
            return result
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run NotionMCPTool queries via CLI")
    parser.add_argument(
        "--query",
        required=True,
        help="The query for retrieving information from Notion MCP server",
    )
    args = parser.parse_args()

    tool = NotionMCPTool(query=args.query)
    result = tool.run()
    # Print the result (in markdown format when enabled)
    if isinstance(result, (dict, list)):
        # if JSON-like, convert to string
        import json

        print(json.dumps(result, indent=2))
    else:
        print(result)