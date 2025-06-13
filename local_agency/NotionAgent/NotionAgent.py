from agency_swarm import Agent
import sys
import os

# Add the parent directory to sys.path to access tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.NotionAgent.NotionUpdateTool import NotionUpdateTool
from tools.NotionAgent.NotionReadTool import NotionReadTool

# Create a temporary agent
class NotionAgent(Agent):
    def __init__(self):
        super().__init__(
            name="NotionAgent",
            description="Specialized agent for querying and retrieving information from the VRSEN AI Notion workspace. Works under CEO direction to execute specific Notion API operations and provide comprehensive results.",
            instructions="./instructions.md",
            tools=[NotionReadTool, NotionUpdateTool],
            temperature=0.3,
            max_prompt_tokens=100000,
            model="gpt-4.1-mini"
        )

    def response_validator(self, message):
        return message