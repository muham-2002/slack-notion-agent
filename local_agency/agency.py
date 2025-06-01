from agency_swarm import Agency
from CEO.CEO import CEO
from NotionAgent.NotionAgent import NotionAgent

# Initialize agents
ceo = CEO()
notion_agent = NotionAgent()

# Create agency with CEO as the primary entry point
# CEO can communicate with NotionAgent to fulfill user requests
agency = Agency([
    ceo,  # CEO is the primary entry point for users
    [ceo, notion_agent],  # CEO can initiate communication with NotionAgent
])


if __name__ == "__main__":
    agency.demo_gradio()