from agency_swarm import Agent

class SlackNotionAssistant(Agent):
    def __init__(self):
        super().__init__(
            name="Slack-Notion Assistant",
            description="Acts as a bridge between Slack and Notion, enabling users to retrieve and update workspace knowledge efficiently and safely.",
            instructions="./instructions.md",
            tools_folder="./tools",
            temperature=0.5,
            max_prompt_tokens=25000,
        ) 