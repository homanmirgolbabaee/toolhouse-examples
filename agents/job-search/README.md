# Building a Job-Search agent with Anthropic and Toolhouse# AI Job Finder with Toolhouse

This AI Job Finder agent helps you discover and apply for relevant job opportunities based on your preferences. Using just a few lines of code for Toolhouse tool integration, this agent searches for recent job listings, researches companies, and provides personalized application tips.

![Job Finder Demo](demo.gif)

## What This Agent Can Do

The AI Job Finder can:

- Search for job listings matching your title and location preferences
- Filter for recent postings (within the last 7 days)
- Extract comprehensive job details (company, requirements, deadlines, salaries)
- Research company profiles on LinkedIn
- Generate personalized resume tailoring tips for each position
- Deliver a well-formatted HTML email digest
- Remember previous searches to avoid duplicate recommendations

## Tools Used

This agent leverages four essential Toolhouse tools:

1. **[Web Search](https://app.toolhouse.ai/store/web_search)**: To find job listings from multiple sources
2. **[LinkedIn Search](https://app.toolhouse.ai/store/linkedin_search)**: To research companies and related profiles
3. **[Current Time](https://app.toolhouse.ai/store/current_time)**: To filter for recent postings and track deadlines
4. **[Send Email](https://app.toolhouse.ai/store/send_email)**: To deliver the job digest

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
   streamlit run job_finder.py
   ```

## How It Works

The AI Job Finder follows these steps:

1. **Input**: You provide a job title, location, and optional email address
2. **Search**: The agent finds recent job listings matching your criteria
3. **Research**: It gathers company information and LinkedIn profiles
4. **Analyze**: It generates tailored resume tips for each position
5. **Deliver**: Results are displayed in the app and/or emailed to you

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

## The Toolhouse Advantage

This agent demonstrates the power of Toolhouse's approach to tool integration. With minimal code:

1. The agent can search multiple job boards and company sites
2. Access LinkedIn data for company research
3. Filter results based on recency and deadlines
4. Send formatted email digests

All of this functionality is accessed through the simple `th_client.get_tools()` and `th_client.run_tools()` methods, eliminating complex tool implementations.

## Customization Options

You can easily customize this agent for your needs:

- Modify the system prompt to search for specific skills or industries
- Adjust the location filters for your desired regions
- Change the email formatting to match your preferences
- Add additional search parameters like salary range or company size

## License

MIT