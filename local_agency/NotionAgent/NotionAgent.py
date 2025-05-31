from agency_swarm import Agent
from tools.NotionReadTool import NotionReadTool

# Create a temporary agent
class NotionAgent(Agent):
    def __init__(self):
        super().__init__(
            name="NotionAgent",
            description="Agent to query notion database",
            instructions="./instructions.md",
            tools=[NotionReadTool],
            temperature=0.3,
            max_prompt_tokens=60000,
            model="gpt-4.1"
        )

    def response_validator(self, message):
        return message
