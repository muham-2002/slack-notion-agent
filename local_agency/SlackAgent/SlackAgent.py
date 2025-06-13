from agency_swarm.agents import Agent
from tools.SlackAgent.SlackMCPTool import SlackMCPTool

class SlackAgent(Agent):
    def __init__(self):
        super().__init__(
            name="SlackAgent",
            description="Slack Communication Specialist that provides clean, structured responses about Slack workspace operations. Capabilities include: channel discovery and management, message search and posting, user information retrieval, thread management, and reaction handling. Designed to work seamlessly with CEO Agent to provide actionable Slack insights and facilitate efficient team communication workflows.",
            instructions="./instructions.md",
            tools=[SlackMCPTool],
            temperature=0.3,
            max_prompt_tokens=50000,
            model="gpt-4.1"
        )

    def response_validator(self, message):
        return message
