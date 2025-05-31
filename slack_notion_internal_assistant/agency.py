from agency_swarm import Agency
from slack_notion_assistant.slack_notion_assistant import SlackNotionAssistant
from dotenv import load_dotenv

load_dotenv()

agent = SlackNotionAssistant()

agency = Agency(
    [agent],
    shared_instructions="agency_manifesto.md",
    temperature=0.5,
    max_prompt_tokens=25000
)

if __name__ == "__main__":
    agency.run_demo() 