# Reddit Engagement Assistant with Anthropic and Toolhouse

This agent helps users boost their Reddit engagement and karma by finding trending posts and crafting effective responses using Anthropic's Claude model and Toolhouse's tool management platform.

> 👋 Just like other Toolhouse examples, this agent gives you powerful Reddit engagement capabilities with just **3 lines of code** for tool integration.

## Intro - [VIDEO HERE]

![Reddit Assistant Demo](https://github.com/user-attachments/assets/example-placeholder-image.gif)

This Reddit Assistant helps you increase your karma and engagement on Reddit by:

1. Finding posts (Hot,New,Top) 
2. Analyzing the content using MCP servers (scraper,web_search,describe_image)
3. Comes up responses optimized for karma
4. Delivering results via email

## What This Agent Can Do

The Reddit Engagement Assistant can:

- Search for  posts across various subreddits
- Analyze post content and existing comments to identify engagement opportunities
- Draft concise, relevant responses optimized for karma
- Format results in an organized manner
- Email results directly to the user's inbox
- Schedule regular engagement opportunities based on optimal posting times

## Tools Used

This agent leverages three essential Toolhouse tools:

1. **[Get Page Contents](https://app.toolhouse.ai/store/scraper)**: To retrieve post content from Reddit
2. **[Send Email](https://app.toolhouse.ai/store/send_email)**: To deliver engagement opportunities directly to your inbox
3. **[Get Current Time](https://app.toolhouse.ai/store/current_time)**: To optimize posting times for maximum visibility
4. **[Web Search](https://app.toolhouse.ai/store/web_search)**: To gather more info from web search.

## Getting Started

1. Make sure you have the necessary API keys set as environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export TOOLHOUSE_API_KEY="your_toolhouse_api_key"
   ```

2. Install dependencies as explained in the main README

3. Run the Streamlit App:
   ```bash
   cd agents/reddit-assistant
   streamlit run streamlit_app.py
   ```

## How It Works

The Reddit Engagement Assistant follows these steps:

1. **Search**: It Searchs Reddit to find trending posts in specified subreddits
2. **Analyze**: It evaluates post content, existing responses, and engagement patterns
3. **Draft**: It creates tailored responses designed to maximize karma and engagement
4. **Deliver**: It formats results and can email them directly to your inbox

### Implementation Details

Here's how we implement this agent with minimal code using Toolhouse:

```python
# Initialize Toolhouse with Anthropic provider
th = Toolhouse(api_key=TOOLHOUSE_API_KEY, provider=Provider.ANTHROPIC)

# Generate response with tools available
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    system=system_message,
    # ✨ The magic happens here - all tools available with one line
    tools=th.get_tools(),
    messages=messages
)

# ✨ Execute tools automatically with minimal code
messages += th.run_tools(response)
```

Without Toolhouse, we would need hundreds of lines of code to handle Reddit API authentication, response parsing, error handling, and thread analysis logic.

Toolhouse Advantage

With just a few lines of code using Toolhouse's API, this assistant can perform web scraping, content analysis, and email delivery functions. The integration is seamless and eliminates the need for complex authentication handlers or parsing logic for Reddit's API responses.

This demonstrates how Toolhouse simplifies building powerful AI agents without the overhead of implementing each tool from scratch.
