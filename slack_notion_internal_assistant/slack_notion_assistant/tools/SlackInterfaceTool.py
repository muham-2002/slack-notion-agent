from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

class SlackInterfaceTool(BaseTool):
    """
    Sends messages to Slack channels using the Slack Web API.
    """
    channel: str = Field(..., description="Slack channel ID where to send the message")
    message: str = Field(..., description="The message text to send to Slack")

    def run(self) -> str:
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        try:
            response = client.chat_postMessage(channel=self.channel, text=self.message)
            return f"Message sent to {self.channel} at timestamp {response['ts']}"
        except SlackApiError as e:
            return f"Error sending Slack message: {e.response['error']}"

if __name__ == "__main__":
    tool = SlackInterfaceTool(channel="#general", message="Hello from SlackInterfaceTool")
    print(tool.run()) 