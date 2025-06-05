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
class SlackMCPTool(BaseTool):
    """
    Sends a query to Slack via an internal MCPServer and Agent, wrapped in a minimal Agency. The agent decides which Slack MCP tool and arguments to use based on the query.
    
    The tool can:
    - List available channels and their IDs
    - Send messages to channels
    - Read messages from channels
    - Search for messages
    - Get channel information
    - List available Slack operations/tools
    
    If SLACK_CHANNEL_IDS is not set, the tool will first attempt to discover channels.
    """
    query: str = Field(..., description="The query for retrieving information from Slack (the agent will decide how to handle it). Examples: 'list channels', 'list available operations', 'send message to general', 'search for messages about project'")

    def run(self) -> Any:
        try:
            # Check for required environment variables
            slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
            slack_team_id = os.getenv("SLACK_TEAM_ID")
            slack_channel_ids = os.getenv("SLACK_CHANNEL_IDS", "")  # Default to empty string
            
            if not slack_bot_token:
                return {"error": "SLACK_BOT_TOKEN environment variable is required but not set"}
            
            if not slack_team_id:
                return {"error": "SLACK_TEAM_ID environment variable is required but not set"}
            
            # Setup MCPServer for Slack with fallback for missing SLACK_CHANNEL_IDS
            env_vars = {
                "SLACK_BOT_TOKEN": slack_bot_token,
                "SLACK_TEAM_ID": slack_team_id,
            }
            
            # Only add SLACK_CHANNEL_IDS if it's not empty
            if slack_channel_ids:
                env_vars["SLACK_CHANNEL_IDS"] = slack_channel_ids
            
            slack_server = MCPServerStdio(
                name="slack",
                params={
                    "env": env_vars,
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-slack"],
                },
                cache_tools_list=True
            )
            
            # Create a temporary agent with specific instructions for handling Slack queries
            class _SlackAgent(Agent):
                def __init__(self):
                    super().__init__(
                        name="SlackAgent",
                        description="Temporary agent for Slack MCP queries.",
                        instructions="""You are a Slack interface agent. Use the available Slack MCP tools to:

1. If asked to list channels or operations, use the appropriate MCP tools to discover them
2. If asked to send messages, use the messaging tools
3. If asked to search or read, use the search/read tools
4. Always provide clear, structured responses
5. If channel IDs are needed but not known, first list channels to find the right ones
6. Handle errors gracefully and suggest alternatives

Available operations you can perform:
- List channels and get their IDs
- Send messages to channels
- Read messages from channels
- Search for messages
- Get channel information
- List all available Slack MCP tools

Respond in a clear, structured format showing what was found or accomplished.""",
                        mcp_servers=[slack_server],
                        temperature=0.3,
                        max_prompt_tokens=25000,
                        model="gpt-4o-mini"
                    )
                def response_validator(self, message):
                    return message
            
            agent = _SlackAgent()
            
            # Create a minimal Agency with this agent as CEO
            agency = Agency([agent])
            
            # Use the agency to get a completion from the agent
            result = agency.get_completion(self.query)
            return result
            
        except Exception as e:
            return {
                "error": f"SlackMCPTool error: {str(e)}",
                "suggestion": "Check your Slack bot token and team ID. If SLACK_CHANNEL_IDS is missing, try querying 'list channels' first to discover available channels."
            }

if __name__ == "__main__":
    query = "list channels"
    print(f"\n=== Testing Query: {query} ===")
    tool = SlackMCPTool(query=query)
    result = tool.run()
    print(result)
    print("-" * 50)