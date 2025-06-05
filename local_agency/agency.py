from agency_swarm import Agency
from CEO.CEO import CEO
from NotionAgent.NotionAgent import NotionAgent
from SlackAgent.SlackAgent import SlackAgent

# Initialize agents
ceo = CEO()
notion_agent = NotionAgent()
slack_agent = SlackAgent()

# Create agency with CEO as the primary entry point
# CEO can communicate with both NotionAgent and SlackAgent to fulfill user requests
agency = Agency([
    ceo,  # CEO is the primary entry point for users
    [ceo, notion_agent],  # CEO can initiate communication with NotionAgent
    [ceo, slack_agent],   # CEO can initiate communication with SlackAgent
])


if __name__ == "__main__":
    agency.demo_gradio()