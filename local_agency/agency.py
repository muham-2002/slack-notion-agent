from local_agency.NotionAgent.NotionAgent import NotionAgent
from agency_swarm import Agency


notion_agent = NotionAgent()
agency = Agency([
    notion_agent
])


if __name__ == "__main__":
    agency.demo_gradio()