# Startup Due Diligence Assistant
## Try the Demo: https://toolhouse-comapany-researcher.streamlit.app/
## Introduction

The Startup Due Diligence Assistant is a smart AI agent that makes it easy for investors/enthusiasts to learn about potential startup investments. By using Toolhouse tools, it gathers detailed information from various sources with very little effort required.

![Demo Screenshot](assets/demo.gif)

## What This Agent Can Do

This due diligence assistant can:

- Gather comprehensive company information (founding date, location, business model)
- Research the founding team and key executives via LinkedIn
- Analyze funding history and financial metrics from public sources
- Examine market position, competitors, and customer feedback
- Track recent company activities through Twitter/X
- Deliver a formatted HTML report via email

## Tools Used

This agent leverages five essential Toolhouse tools:

1. **[Web Search](https://app.toolhouse.ai/store/web_search)**: To gather company information, funding history, and market data
2. **[LinkedIn Search](https://app.toolhouse.ai/store/linkedin_search)**: To research founders and leadership teams
3. **[X/Twitter Search](https://app.toolhouse.ai/store/search_x)**: To track recent company activities
4. **[Send Email](https://app.toolhouse.ai/store/send_email)**: To deliver the due diligence report
5. **[Current Time](https://app.toolhouse.ai/store/current_time)**: To timestamp the analysis

## Getting Started

1. Make sure you have the necessary API keys set as environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export TOOLHOUSE_API_KEY="your_toolhouse_api_key"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit App:
   ```bash
   streamlit run streamlit_app.py
   ```

## How It Works

The Startup Due Diligence Assistant follows these steps:

1. **Input**: You provide the startup name, website, and your email address
2. **Research**: The agent gathers information from multiple sources (web, LinkedIn, X/Twitter)
3. **Analysis**: It compiles the data into a comprehensive due diligence report
4. **Delivery**: The report is displayed in the app and emailed to you

### Implementation Details

Here's how we implement this agent with minimal code using Toolhouse:

```python
# Initialize Toolhouse with Anthropic provider
th_client = Toolhouse(api_key=TOOLHOUSE_API_KEY, provider=Provider.ANTHROPIC)

# Generate response with tools available
response = anthropic_client.messages.create(
    model="claude-3-7-sonnet-20250219",
    system=system_prompt,
    # ✨ The magic happens here - all tools available with one line
    tools=th_client.get_tools(),
    messages=messages
)

# ✨ Execute tools automatically with minimal code
tool_results = th_client.run_tools(response)
```

Without Toolhouse, we would need hundreds of lines of code to handle tools like web searches, LinkedIn data extraction, Twitter API authentication, email sending, and error handling for each of these services.

## The Toolhouse Advantage

This agent demonstrates the power of Toolhouse's approach to tool integration. With minimal code:

1. The agent can perform sophisticated web searches across multiple sources
2. Access LinkedIn data for team analysis
3. Retrieve recent Twitter/X activity
4. Send formatted email reports

All of this functionality is accessed through the simple `th_client.get_tools()` and `th_client.run_tools()` methods, eliminating complex tool implementations.

## Example Use Cases

- Initial screening of potential investments
- Pre-meeting research for VC pitch meetings
- Competitive analysis of startups in a specific sector
- Tracking progress of portfolio companies
- Market research for startup founders

## Contributing

This is an example project showcasing Toolhouse capabilities. Feel free to extend it with additional features such as:

- Historical data analysis
- Sentiment analysis of news and social media
- Integration with financial databases
- PDF report generation
- Customizable research parameters

## License

MIT
