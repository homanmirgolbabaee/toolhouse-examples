# Language Learning Assistant with Toolhouse

This agent helps users learn and practice foreign languages using Anthropic's Claude model and Toolhouse's tool management platform.

## What This Agent Can Do

This language learning assistant can:

- Teach vocabulary and common phrases in multiple languages
- Provide pronunciation guides using phonetic spelling
- Create customized practice exercises based on proficiency level
- Explain grammar rules with clear examples
- Offer cultural context for proper language usage
- Suggest personalized practice routines
- Provide constructive feedback on language attempts
- Email vocabulary lists and lesson materials

## Supported Languages

The agent can help with learning:

- Spanish
- French
- German
- Italian
- Japanese
- Mandarin
- Korean

## Tools Used

This agent leverages three essential Toolhouse tools:

1. **[Get Current Time](https://app.toolhouse.ai/store/current_time)**: To provide culturally appropriate greetings based on time of day
2. **[Get Page Contents](https://app.toolhouse.ai/store/scraper)**: To retrieve authentic language examples from native sources
3. **[Send Email](https://app.toolhouse.ai/store/send_email)**: To deliver vocabulary lists and lesson summaries

## Getting Started

1. Make sure you have the necessary API keys set as environment variables:

   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export TOOLHOUSE_API_KEY="your_toolhouse_api_key"
   ```

2. Install dependencies found in requirements.txt as explained in the main README

3. Run the agent:
   ```bash
   cd agents/language-tutor
   python agent.py
   ```

## Example Interactions

- "I'd like to learn some basic Spanish phrases for my upcoming trip to Madrid."
- "Can you explain the difference between por and para in Spanish?"
- "How do I conjugate French verbs in the past tense?"
- "I need to practice ordering food in Italian. Can we do a roleplay?"
- "What are some common honorifics in Japanese and when should I use them?"
- "Can you email me a list of the essential 100 German words I should learn first?"

## The Toolhouse Advantage

This language learning assistant demonstrates the power of Toolhouse's approach to tool integration. With minimal code:

1. The agent can access authentic language examples from native sources
2. Provide time-appropriate greetings in the target language
3. Deliver study materials directly to the user's inbox

All of this functionality comes through the simple `th.get_tools()` and `th.run_tools()` methods, eliminating the need for complex tool implementation or management.
