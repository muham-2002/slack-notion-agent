from agency_swarm import Agent


class CEO(Agent):
    def __init__(self):
        super().__init__(
            name="CEO",
            description="Chief Executive Officer responsible for understanding user queries, making decisions, and coordinating with specialized agents like NotionAgent to fulfill user requests efficiently.",
            instructions="./instructions.md",
            tools=[],
            temperature=0.5,
            max_prompt_tokens=60000,
            model="gpt-4.1"
        )