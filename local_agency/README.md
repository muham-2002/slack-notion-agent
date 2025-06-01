# Slack-Notion Internal Assistant Agency

A multi-agent system with a CEO agent that coordinates with specialized agents to query and interact with your VRSEN AI Notion workspace.

## 🏗️ Architecture

### Agency Structure
```
👤 User
    ↓
🏢 CEO Agent (Decision Maker & Coordinator)
    ↓
📚 NotionAgent (Clean Response Specialist)
    ↓
📊 Cleaned, Actionable Results
```

### Agent Roles

#### 🏢 CEO Agent
- **Primary Interface**: Acts as the main entry point for all user interactions
- **Decision Maker**: Analyzes user queries and determines the best approach to fulfill them
- **Coordinator**: Manages communication with specialized agents (currently NotionAgent, expandable to more)
- **Synthesizer**: Combines results from multiple sources into coherent responses
- **Strategic**: Makes intelligent decisions about follow-up queries and pagination handling

#### 📚 NotionAgent
- **Command Executor**: Follows specific CEO instructions to query Notion
- **Response Cleaner**: Converts raw tool results into clean, actionable information
- **Error Handler**: Automatically retries failed queries with corrections
- **Efficiency Expert**: Provides only relevant data with clear next-step suggestions

## 🚀 Getting Started

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Agency
```bash
cd local_agency

# Test the agency structure
python test_agency.py

# Run the full agency with Gradio interface
python agency.py

# See workflow demonstrations
python demo_ceo_workflow.py

# See clean response examples
python demo_clean_responses.py
```

## 🧹 Clean Response System

The NotionAgent now provides **clean, focused responses** instead of raw JSON data:

### Before (Raw JSON):
```json
{
  "results": [
    {
      "object": "page",
      "id": "abc123",
      "properties": {
        "Title": {
          "type": "title",
          "title": [{"plain_text": "Zapier Integration"}]
        }
        // ... 200+ lines of nested data
      }
    }
  ]
}
```

### After (Clean Response):
```
✅ Search Results for "zapier":
- Found 3 items across workspace
- Top results:
  1. "Zapier Integration Setup" (Notes) - Active
  2. "API Credentials - Zapier" (Notes) - Draft

📊 Status: has_more=false, total_found=3
💡 Suggestion: Retrieve "API Credentials" page for detailed info
```

## 💬 Example Workflows

### 1. Finding Credentials/Account Information
**User Query**: "Tell me about our Zapier account info"

**CEO → NotionAgent**: "Search for 'Zapier' across the workspace"
**NotionAgent → CEO**: 
```
✅ Found 3 Zapier-related items
💡 Suggestion: Retrieve "API Credentials - Zapier" page for details
```
**CEO Follow-up**: "Get the API credentials page content"
**Final Response**: Organized account information with credentials

### 2. Error Handling & Retry
**CEO → NotionAgent**: "Query tasks with invalid filter"
**NotionAgent → CEO**:
```
❌ Filter Error: Property 'Invalid_Field' not found
🔄 Retried with: Basic task query
✅ Found 15 tasks successfully
```

## 🔧 Key Features

### CEO Agent Capabilities
- **Intelligent Query Analysis**: Understands user intent and context
- **Strategic Planning**: Determines optimal search strategies
- **Multi-step Coordination**: Manages complex queries requiring multiple API calls
- **Result Evaluation**: Assesses completeness and requests follow-ups
- **Response Synthesis**: Combines multiple data sources into coherent answers
- **Future-Ready**: Designed to coordinate with additional agents as system grows

### NotionAgent Capabilities (Simplified & Focused)
- **Clean Response Generation**: Converts raw tool data into actionable insights
- **Automatic Error Recovery**: Retries failed queries with logical corrections
- **Smart Suggestions**: Recommends next steps based on results
- **Pagination Awareness**: Always reports result counts and "has_more" status
- **Efficiency Focus**: Provides only relevant information, no unnecessary data

## 📊 Notion Database Integration

### Supported Databases
- **Tasks**: `42fad9c5-af8f-4059-a906-ed6eedc6c571`
- **Projects**: `567db0a8-1efc-4123-9478-ef08bdb9db6a`
- **Notes**: `4542b3f7-39c3-47e0-9ecd-22c58437d812`

### Available Operations
- **search**: Global workspace search
- **query_database**: Targeted database queries with filters/sorts
- **retrieve_page**: Get complete page content with blocks
- **retrieve_block**: Get specific block information
- **retrieve_block_children**: Get hierarchical block content

## 🎯 Benefits of Updated Architecture

### For CEO Agent
- **Clean Data**: Receives only relevant, processed information
- **Actionable Insights**: Every response includes next-step suggestions
- **Error Transparency**: Clear error reports with retry attempts
- **Efficient Decision Making**: No need to parse complex JSON structures

### For Users
- **Faster Responses**: No time wasted processing irrelevant data
- **Better Accuracy**: Clean data leads to better CEO decisions
- **Comprehensive Coverage**: Automatic retry ensures complete information gathering
- **Professional Output**: Well-structured, business-appropriate responses

### For Development
- **Simplified Debugging**: Clean responses make issues easier to identify
- **Scalable Pattern**: Other agents can follow the same clean response model
- **Maintainable Code**: Clear separation between raw data and processed insights
- **Robust Error Handling**: Built-in retry logic prevents single-point failures

## 🔮 Future Expansion

The CEO agent architecture easily accommodates additional clean-response agents:

```
👤 User
    ↓
🏢 CEO Agent
    ├── 📚 NotionAgent (Clean Notion responses)
    ├── 📧 SlackAgent (Clean Slack responses)
    ├── 📅 CalendarAgent (Clean calendar responses)
    ├── 📈 AnalyticsAgent (Clean analytics responses)
    └── 🤖 AutomationAgent (Clean automation responses)
```

Each agent follows the same pattern: execute commands, clean responses, suggest next steps.

## 🔐 Security & Configuration

- **Environment Variables**: All API keys stored securely in `.env`
- **Access Control**: Agents operate within defined database permissions
- **Safe Operations**: Read-only operations prevent accidental data modification
- **Audit Trail**: All agent communications are logged

## 📞 Support

For issues or questions about the CEO agent system:
1. Check clean response examples: `python demo_clean_responses.py`
2. Check the workflow demonstrations: `python demo_ceo_workflow.py`
3. Test individual components: `python test_agency.py`
4. Review agent instructions in their respective folders
5. Check Notion API permissions and database access 