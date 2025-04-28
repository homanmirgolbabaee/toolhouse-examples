import os
from typing import List
from anthropic import Anthropic
from toolhouse import Toolhouse, Provider
from dotenv import load_dotenv

load_dotenv()


# Load API keys from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TOOLHOUSE_API_KEY = os.getenv("TOOLHOUSE_API_KEY")

# Initialize Anthropic and Toolhouse clients
client = Anthropic(api_key=ANTHROPIC_API_KEY)
th = Toolhouse(api_key=TOOLHOUSE_API_KEY, provider=Provider.ANTHROPIC)

# Define language options that the agent can teach
SUPPORTED_LANGUAGES = ["Spanish", "French", "German", "Italian", "Japanese", "Mandarin", "Korean"]

# Define system message for the AI agent
system_message = f"""
You are a language learning assistant that helps users practice and improve their foreign language skills.

Your primary capabilities include:
1. Teaching vocabulary and common phrases in the target language
2. Providing pronunciation guides (using phonetic spelling)
3. Creating customized practice exercises based on the user's proficiency level
4. Explaining grammar rules with simple examples
5. Offering cultural context for language usage
6. Suggesting daily practice routines based on the user's schedule
7. Correcting the user's attempts with constructive feedback

SUPPORTED LANGUAGES: {", ".join(SUPPORTED_LANGUAGES)}

GUIDELINES:
- First determine which language the user wants to learn
- Assess their current proficiency level through conversation
- Keep explanations simple and provide plenty of examples
- Use the web scraping tool to find authentic examples of language usage from native sources
- For vocabulary learning, suggest mnemonic techniques and contextual learning
- If the user wants study materials, offer to email them summaries of lessons or vocabulary lists
- Always encourage consistent practice and provide positive reinforcement
- When correcting mistakes, focus on one or two issues at a time to avoid overwhelming the user
- Use the current time to greet users appropriately in their target language

Never provide information on languages outside your supported list as you lack the training data to teach them properly.

Use your tools wisely:
- Use web scraping to find authentic example sentences and cultural context
- Use email functionality to send vocabulary lists or lesson summaries only when explicitly requested
- Use time awareness to provide appropriate greetings in the target language
"""

# Initialize message history
messages: List = []
# Flag to check if it's the first question
first_question = True

def process_response(messages):
    global first_question
    
    # Prompt user for question (different for first and follow-up questions)
    if first_question:
        input_question = input("\033[36m¡Hola! Bonjour! 你好! Hello! I'm your language tutor. Which language would you like to learn or practice today? \033[0m")
        first_question = False
    else:
        input_question = input("\033[36mWhat else would you like to learn or practice? \033[0m")
    
    # Exit if user types '/quit' '/exit'
    if input_question.lower() in ["/quit", "/exit"]:
        exit()
    
    # Add user's question to message history
    messages.append({"role": "user", "content": f"{input_question}" })
    
    # Generate initial response using Anthropic model
    response = client.messages.create(
                model="claude-3-5-sonnet-20240620", 
                max_tokens=1024,
                system=system_message,
                # Get the tools from toolhouse SDK to perform actions based on the request
                tools=th.get_tools(),
                messages=messages
            )
    
    # Run tools based on the response
    messages += th.run_tools(response)
    
    # Generate final response
    agent_setup = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=system_message,
        tools=th.get_tools(),
        messages=messages
    )
    agent_reply = agent_setup.content[0].text
    
    # Print AI agent's response
    print("\033[35mLanguage Tutor:\033[0m", agent_setup.content[0].text)
    
    # Add AI's response to message history
    messages.append({"role": "assistant", "content": f"{agent_reply}" })

# Main loop to continuously process responses
while True:
    process_response(messages)