import streamlit as st
import os
from toolhouse import Toolhouse

# Page setup
st.set_page_config(page_title="ToolHouse Query", page_icon="🔍")
st.title("ToolHouse Streamlit Template")

# Sidebar for API keys
with st.sidebar:
    # API keys
    toolhouse_key = st.text_input("ToolHouse API Key", type="password", 
                                  value=os.environ.get("TOOLHOUSE_API_KEY", ""))
    
    # Provider selection - only supported providers
    provider = st.selectbox("Provider", ["openai", "anthropic"], index=0)
    
    # Provider-specific API key and model
    if provider == "openai":
        llm_key = st.text_input("OpenAI API Key", type="password", 
                               value=os.environ.get("OPENAI_API_KEY", ""))
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    
    elif provider == "anthropic":
        llm_key = st.text_input("Anthropic API Key", type="password", 
                               value=os.environ.get("ANTHROPIC_KEY", ""))
        model = st.selectbox("Model", ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-latest"], index=0)
    
    # Sidebar footer with API key links
    st.markdown("---")
    st.markdown("### How to get the API keys")
    
    if provider == "anthropic":
        st.markdown("[Anthropic Console](https://console.anthropic.com/settings/keys)")
    else:
        st.markdown("[OpenAI Console](https://platform.openai.com/api-keys)")
        
    # ToolHouse API key link
    st.markdown("[ToolHouse Console](https://toolhouse.ai/settings)")


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(message["content"])

# Chat input
query = st.chat_input("Ask a question...", key="user_input")

# Process query
if query:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)
    
    # Check for API keys
    if not toolhouse_key or not llm_key:
        st.error("Please enter API keys in the sidebar")
    else:
        # Show assistant thinking
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                try:
                    # Initialize ToolHouse client
                    th = Toolhouse(api_key=toolhouse_key, provider=provider)
                    
                    # Get current messages
                    messages = st.session_state.messages.copy()
                    
                    # Process based on the provider
                    if provider == "openai":
                        # Import OpenAI
                        from openai import OpenAI
                        client = OpenAI(api_key=llm_key)
                        
                        # First API call with tools
                        response = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            tools=th.get_tools()
                        )
                        
                        # Process tool calls
                        tool_messages = th.run_tools(response)
                        messages += tool_messages
                        
                        # Final call with tool results
                        response = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            tools=th.get_tools()
                        )
                        
                        # Get the response
                        assistant_response = response.choices[0].message.content
                    
                    elif provider == "anthropic":
                        # Import Anthropic
                        from anthropic import Anthropic
                        client = Anthropic(api_key=llm_key)
                        
                        # First API call with tools
                        response = client.messages.create(
                            model=model,
                            messages=messages,
                            max_tokens=1000,
                            tools=th.get_tools()
                        )
                        
                        # Process tool calls
                        tool_messages = th.run_tools(response)
                        messages += tool_messages
                        
                        # Final call with tool results
                        response = client.messages.create(
                            model=model,
                            messages=messages,
                            max_tokens=1000,
                            tools=th.get_tools()
                        )
                        
                        # Get the response
                        assistant_response = response.content[0].text
                    

                    
                    # Display response
                    message_placeholder.write(assistant_response)
                    
                    # Save to history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    
                except Exception as e:
                    message_placeholder.error(f"Error: {str(e)}")

# Add a clear button
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.rerun()