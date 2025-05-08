# Import the email function at the top with other imports
import streamlit as st
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any
from anthropic import Anthropic
from toolhouse import Toolhouse, Provider

import pandas as pd

# Import the Reddit client
from reddit import RedditClient


# Set page configuration
st.set_page_config(
    page_title="Reddit Engagement Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem !important;
        color: #FF4500;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem !important;
        color: #0078D7;
        margin-bottom: 1rem;
    }
    .post-title {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .post-info {
        font-size: 0.9rem;
        color: #666;
    }
    .post-content {
        padding: 10px;
        background-color: #f9f9f9;
        border-radius: 5px;
        margin: 5px 0;
    }
    .reddit-link {
        color: #FF4500;
        text-decoration: none;
    }
    .response-box {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #0078D7;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
# Sidebar for API keys 🔐
st.sidebar.header("API Configuration")
anthropic_api_key_input = st.sidebar.text_input("Anthropic API Key", type="password")
toolhouse_api_key_input = st.sidebar.text_input("Toolhouse API Key", type="password")

if anthropic_api_key_input:
    # Clear cached resources when API key changes
    if "ANTHROPIC_API_KEY" not in st.session_state or st.session_state["ANTHROPIC_API_KEY"] != anthropic_api_key_input:
        st.cache_resource.clear()
    st.session_state["ANTHROPIC_API_KEY"] = anthropic_api_key_input
    
if toolhouse_api_key_input:
    # Clear cached resources when API key changes
    if "TOOLHOUSE_API_KEY" not in st.session_state or st.session_state["TOOLHOUSE_API_KEY"] != toolhouse_api_key_input:
        st.cache_resource.clear()
    st.session_state["TOOLHOUSE_API_KEY"] = toolhouse_api_key_input

# Initialize session state
if 'posts' not in st.session_state:
    st.session_state.posts = []
if 'selected_posts' not in st.session_state:
    st.session_state.selected_posts = []
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'email_sent' not in st.session_state:
    st.session_state.email_sent = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Popular Subreddits
POPULAR_SUBREDDITS = [
    "LocalLLaMA", "ChatGPT", "MachineLearning", "artificial", 
    "datascience", "programming", "Python", "learnprogramming",
    "AskReddit", "explainlikeimfive", "IAmA", "todayilearned"
]

# Initialize clients
@st.cache_resource
def initialize_clients():
    """Initialize Reddit, Anthropic, and Toolhouse clients"""
    # Initialize clients
    anthropic_client = Anthropic(api_key=st.session_state.get("ANTHROPIC_API_KEY", ""))
    
    # Fix: Use proper Toolhouse initialization with API key
    # Note: Use the API key from session state, not directly from the input
    th_client = Toolhouse(api_key=st.session_state.get("TOOLHOUSE_API_KEY", ""), 
                         provider=Provider.ANTHROPIC)
    
    reddit_client = RedditClient(user_agent="RedditEngagementAssistant/1.0")
    
    return anthropic_client, th_client, reddit_client

anthropic_client, th_client, reddit_client = initialize_clients()

def send_engagement_email(anthropic_client, th_client, email_address, subject, email_content):
    """
    A dedicated function to send emails via Toolhouse.ai
    
    Parameters:
    -----------
    anthropic_client : Anthropic
        Initialized Anthropic client
    th_client : Toolhouse
        Initialized Toolhouse client
    email_address : str
        Recipient email address
    subject : str
        Email subject line
    email_content : str
        The formatted email content (markdown formatted)
    
    Returns:
    --------
    bool
        True if email was successfully sent, False otherwise
    """
    # Create a system prompt specifically for email sending
    email_system_prompt = """
    You are an email sending assistant. Your only job is to send an email with the provided content in a table format.
    
    DO NOT modify, summarize, or change the email content in any way.
    DO NOT add any additional text, commentary, or explanations.
    DO NOT respond to the user with anything except confirmation that you've sent the email.
    
    Send the email exactly as instructed with the provided subject and content.
    """
    
    # Create a user message with the email details
    email_message = f"""
    Please send an email with the following details ina well structured table using the CONTENT material using HTML/CSS formatting:
    
    TO: {email_address}
    SUBJECT: {subject}
    
    CONTENT:
    {email_content}
    

    IMPORTANT: MAKE SURE THE EMAIL IS FORMATED WELL IN A TABLE FORMAT.

    """
    
    # Create a simple message list just for this email task
    email_messages = [{"role": "user", "content": email_message}]
    
    # Generate response using Anthropic model with Toolhouse tools
    try:
        response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            system=email_system_prompt,
            tools=th_client.get_tools(),
            messages=email_messages
        )
        
        # Run tools based on the response
        email_result = th_client.run_tools(response)
        
        # Check if email was sent successfully
        email_success = any("send_email" in str(msg) for msg in email_result)
        
        return email_success
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# System prompt for the assistant
def create_system_prompt() -> str:
    """Create the system prompt for the assistant"""
    return """
You're helping craft engaging Reddit responses that get upvotes. 

Your task:
1. Analyze the Reddit post content I've selected
2. Draft a concise, authentic response (2-3 sentences works best)
3. Match the subreddit's vibe and culture

Your response should be:
- Helpful or informative 
- Add something valuable to the discussion
- Sound natural, not corporate or robotic
- Encourage further conversation

REQUIRED FORMAT - You MUST present your responses in a properly formatted markdown table with these EXACT columns:
| Post Title | Suggested Response | Engagement Potential |

Include a header row and separator row like this:
| Post Title | Suggested Response | Engagement Potential |
|-----------|-------------------|---------------------|

For each post:
1. Post Title: Use the exact title of the post (no need for links)
2. Suggested Response: Write a brief, engaging comment (2-3 sentences)
3. Engagement Potential: Rate as "High", "Medium", or "Low"

Remember: Reddit rewards authenticity and value. No fluff or jargon.
"""

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #FF4500;'>Reddit Engagement Assistant</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Subreddit selection
    st.subheader("Find Posts")
    
    # Option to enter custom subreddit or choose from popular ones
    subreddit_option = st.radio("Select Subreddit Option:", 
                               ["Choose from Popular", "Enter Custom"])
    
    if subreddit_option == "Choose from Popular":
        selected_subreddits = st.multiselect("Select Subreddits:", 
                                           POPULAR_SUBREDDITS,
                                           default=["ChatGPT", "LocalLLaMA"])
    else:
        custom_subreddit = st.text_input("Enter Subreddit Name:", placeholder="e.g., AskScience")
        selected_subreddits = [custom_subreddit] if custom_subreddit else []
    
    # Post type selection
    post_type = st.radio("Post Type:", ["Hot", "New", "Top"])
    
    # Additional options based on post type
    if post_type == "Top":
        timeframe = st.select_slider("Timeframe:", 
                                   options=["hour", "day", "week", "month", "year", "all"],
                                   value="day")
    else:
        timeframe = "day"  # Default
    
    # Limit posts per subreddit
    posts_per_subreddit = st.slider("Posts per Subreddit:", 1, 10, 3)
    
    # Fetch posts button
    fetch_button = st.button("Fetch Posts", type="primary")
    
    st.markdown("---")
    
    # Email section
    st.subheader("Email Options")
    email_address = st.text_input("Email Address:", placeholder="your@email.com")
    
    # Email options
    if st.session_state.responses:
        email_button = st.button("Email Responses", type="secondary")
        if email_button and email_address:
            st.session_state.email_address = email_address
            st.session_state.email_requested = True
    
    st.markdown("---")
    
    # About section
    st.markdown("### About")
    st.markdown("""
    This Reddit Engagement Assistant helps you boost your karma by:
    1. Finding trending posts across subreddits
    2. Crafting effective responses
    3. Email delivery of engagement opportunities
    
    Built with Streamlit, Anthropic, and Toolhouse.
    """)

# Main content area
st.markdown("<h1 class='main-header'>Reddit Engagement Assistant</h1>", unsafe_allow_html=True)
st.markdown("Boost your Reddit karma with AI-powered engagement strategies")

# Initialize tabs
tab1, tab2, tab3 = st.tabs(["📊 Reddit Posts", "💬 Responses", "📧 Email"])

# Tab 1: Reddit Posts
with tab1:
    if fetch_button and selected_subreddits:
        # Clear previous posts
        st.session_state.posts = []
        
        with st.spinner(f"Fetching {post_type.lower()} posts from {', '.join(['r/' + sub for sub in selected_subreddits])}..."):
            for subreddit in selected_subreddits:
                if post_type == "Hot":
                    posts = reddit_client.get_hot_posts(subreddit, posts_per_subreddit)
                elif post_type == "New":
                    posts = reddit_client.get_new_posts(subreddit, posts_per_subreddit)
                else:  # Top
                    posts = reddit_client.get_top_posts(subreddit, timeframe, posts_per_subreddit)
                
                st.session_state.posts.extend(posts)
                time.sleep(0.5)  # To avoid hitting rate limits
    
    if st.session_state.posts:
        st.markdown(f"<h2 class='sub-header'>Found {len(st.session_state.posts)} Posts</h2>", unsafe_allow_html=True)
        
        # Create checkboxes for post selection
        selected_indices = []
        for i, post in enumerate(st.session_state.posts):
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.checkbox("Select", key=f"post_{i}"):
                    selected_indices.append(i)
            
            with col2:
                # Format the post information
                created_time = datetime.fromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M:%S')
                
                st.markdown(f"<div class='post-title'>{post['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='post-info'>r/{post['subreddit']} • Posted by u/{post['author']} • {created_time}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='post-info'>Score: {post['score']} • Comments: {post['num_comments']}</div>", unsafe_allow_html=True)
                
                # Show post content for self posts
                if post.get('is_self', False) and post.get('selftext', ''):
                    # Truncate very long self texts
                    selftext = post['selftext']
                    if len(selftext) > 300:
                        selftext = selftext[:300] + "... [truncated]"
                    st.markdown(f"<div class='post-content'>{selftext}</div>", unsafe_allow_html=True)
                
                # Link to the post
                st.markdown(f"<a href='{post['url']}' target='_blank' class='reddit-link'>View on Reddit</a>", unsafe_allow_html=True)
                st.markdown("---")
        
        # Store selected posts
        if selected_indices:
            st.session_state.selected_posts = [st.session_state.posts[i] for i in selected_indices]
            
            # Generate responses button
            if st.button("Generate Responses for Selected Posts", type="primary"):
                # Clear previous responses
                st.session_state.responses = {}
                
                # Switch to responses tab
                st.session_state.active_tab = "responses"
                st.rerun()
        else:
            st.info("Select posts to generate engagement responses")
    
    elif not fetch_button:
        st.info("Select subreddits and click 'Fetch Posts' to begin")
    else:
        st.warning("No posts found. Try different subreddits or post types.")

# Tab 2: Responses
with tab2:
    if hasattr(st.session_state, 'active_tab') and st.session_state.active_tab == "responses":
        st.session_state.active_tab = None  # Reset

    if st.session_state.selected_posts and not st.session_state.responses:
        with st.spinner("Generating optimized responses for maximum engagement..."):
            # Clear previous messages when generating new responses
            st.session_state.messages = []
            
            # Format posts for Claude in a simpler way
            formatted_posts = "Here are the Reddit posts to respond to:\n\n"
            for i, post in enumerate(st.session_state.selected_posts, 1):
                formatted_posts += f"POST {i}:\n"
                formatted_posts += f"Title: {post['title']}\n"
                formatted_posts += f"Subreddit: r/{post['subreddit']}\n"
                
                # Include post content if it's a text post
                if post.get('is_self', False) and post.get('selftext', ''):
                    # Truncate very long self texts
                    selftext = post['selftext']
                    if len(selftext) > 300:
                        selftext = selftext[:300] + "..."
                    formatted_posts += f"Content: {selftext}\n"
                
                formatted_posts += f"URL: {post['url']}\n\n"

            # Create a message to Claude
            user_message = f"Help me write engaging Reddit responses for these posts. For each one, give me a brief but valuable response that would likely get upvotes. Format your response in a table with Post Title, Suggested Response, and Engagement Potential columns.\n\n{formatted_posts}"
            
            # Add user message to message history
            st.session_state.messages = [{"role": "user", "content": user_message}]
            
            # Step 1: Generate initial response with tools
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                system=create_system_prompt(),
                tools=th_client.get_tools(),
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Step 2: Run tools based on response (if any tools were called)
            tool_results = th_client.run_tools(response)
            
            # Combine original user message with tool results for final response
            final_messages = [{"role": "user", "content": user_message}]
            if tool_results:
                final_messages.extend(tool_results)
            
            # Step 3: Generate final response with tool results incorporated
            # Force a direct response by adding specific instructions to generate a table
            final_user_message = """
I need you to provide engaging Reddit responses for the posts I shared earlier.
IMPORTANT: Present your responses in a markdown table with these exact columns:
| Post Title | Suggested Response | Engagement Potential |

For each post, provide:
1. The exact post title
2. A 2-3 sentence response that would get upvotes
3. Rate the engagement potential as High, Medium, or Low

Please format as a proper markdown table, including the header row and separator row.
"""
            
            final_messages.append({"role": "user", "content": final_user_message})
            
            # Get final response with explicit table request
            final_response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                system=create_system_prompt(),
                messages=final_messages
            )
            
            # Extract text content from response
            agent_reply = ""
            for content_block in final_response.content:
                if hasattr(content_block, "text"):
                    agent_reply += content_block.text
            
            # Add AI's response to message history
            st.session_state.messages.append({"role": "assistant", "content": agent_reply})
            
            # Add debug expander to show raw response
            with st.expander("Debug: Raw Response", expanded=False):
                st.code(agent_reply, language="markdown")
            
            # Parse the table from the response and create structured data for each post
            try:
                # Enhanced debugging
                st.session_state.debug_info = {"parsing_steps": []}
                
                # Simple table parsing
                lines = agent_reply.split('\n')
                table_start = -1
                table_end = -1
                
                # Add debug info
                st.session_state.debug_info["parsing_steps"].append(f"Total lines in response: {len(lines)}")
                
                # Find the table boundaries
                for i, line in enumerate(lines):
                    if '|' in line and ('Post Title' in line or 'Reddit Post' in line or 'Post' in line):
                        table_start = i
                        st.session_state.debug_info["parsing_steps"].append(f"Found table header at line {i}: {line}")
                        break
                
                # Find separator line (contains only |, -, and spaces)
                if table_start != -1:
                    separator_line = table_start + 1
                    if separator_line < len(lines) and all(c in '|-: ' for c in lines[separator_line]):
                        st.session_state.debug_info["parsing_steps"].append(f"Found separator at line {separator_line}: {lines[separator_line]}")
                    else:
                        st.session_state.debug_info["parsing_steps"].append(f"Warning: No proper separator line found after header")
                
                # Find end of table
                if table_start != -1:
                    for i in range(table_start + 2, len(lines)):
                        if not lines[i].strip() or '|' not in lines[i]:
                            table_end = i
                            st.session_state.debug_info["parsing_steps"].append(f"Found table end at line {i}")
                            break
                
                if table_end == -1:
                    table_end = len(lines)
                    st.session_state.debug_info["parsing_steps"].append(f"Table extends to end of response")
                
                # Extract table rows
                if table_start != -1:
                    st.session_state.debug_info["parsing_steps"].append(f"Processing table rows from {table_start+2} to {table_end}")
                    
                    for i in range(table_start + 2, table_end):  # Skip header and separator
                        if '|' in lines[i]:
                            cells = [cell.strip() for cell in lines[i].split('|')]
                            st.session_state.debug_info["parsing_steps"].append(f"Row {i} has {len(cells)} cells: {cells}")
                            
                            if len(cells) >= 3:  # Accounting for empty cells at start/end
                                # Extract post title/link (accounting for various formats)
                                title_cell = cells[1] if len(cells) > 1 else ""
                                response_cell = cells[2] if len(cells) > 2 else ""
                                potential_cell = cells[3] if len(cells) > 3 else "Medium"
                                
                                url = ""
                                title = title_cell
                                
                                # Try to extract URL if it's in markdown format
                                if '[' in title_cell and ']' in title_cell and '(' in title_cell and ')' in title_cell:
                                    title = title_cell.split('[')[1].split(']')[0]
                                    url = title_cell.split('(')[1].split(')')[0]
                                    st.session_state.debug_info["parsing_steps"].append(f"Extracted title: {title}, URL: {url}")
                                
                                # Find the matching post
                                matching_post = None
                                for post in st.session_state.selected_posts:
                                    if post['title'] == title or post['url'] == url:
                                        matching_post = post
                                        st.session_state.debug_info["parsing_steps"].append(f"Found exact match for: {title}")
                                        break
                                
                                # If no exact match, try partial match on title
                                if not matching_post:
                                    for post in st.session_state.selected_posts:
                                        if title.lower() in post['title'].lower() or post['title'].lower() in title.lower():
                                            matching_post = post
                                            st.session_state.debug_info["parsing_steps"].append(f"Found partial match: {title} ~ {post['title']}")
                                            break
                                
                                # If still no match, use the first unmatched post
                                if not matching_post and st.session_state.selected_posts:
                                    for post in st.session_state.selected_posts:
                                        if post['url'] not in st.session_state.responses:
                                            matching_post = post
                                            st.session_state.debug_info["parsing_steps"].append(f"Using first unmatched post as fallback: {post['title']}")
                                            break
                                
                                if matching_post:
                                    # Store the suggested response
                                    st.session_state.responses[matching_post['url']] = {
                                        'post': matching_post,
                                        'suggested_response': response_cell,
                                        'engagement_potential': potential_cell
                                    }
                                    st.session_state.debug_info["parsing_steps"].append(f"Stored response for: {matching_post['title']}")
                
                # If no responses were parsed from the table, create responses for each post
                if not st.session_state.responses:
                    st.session_state.debug_info["parsing_steps"].append("Table parsing failed, trying alternative extraction")
                    
                    # First try to look for post titles directly
                    for post in st.session_state.selected_posts:
                        post_title = post['title']
                        response_text = ""
                        potential = "Medium"
                        
                        for i, line in enumerate(lines):
                            # Check if this line contains the post title
                            if post_title.lower() in line.lower():
                                st.session_state.debug_info["parsing_steps"].append(f"Found title '{post_title}' at line {i}")
                                
                                # Look for response in the next few lines
                                for j in range(i+1, min(i+5, len(lines))):
                                    if lines[j].strip() and lines[j].strip() != '---' and not lines[j].startswith('#'):
                                        response_text = lines[j].strip()
                                        st.session_state.debug_info["parsing_steps"].append(f"Found response text at line {j}: {response_text[:50]}...")
                                        break
                                
                                if response_text:
                                    break
                        
                        # If a response was found, store it
                        if response_text:
                            st.session_state.responses[post['url']] = {
                                'post': post,
                                'suggested_response': response_text,
                                'engagement_potential': potential
                            }
                        else:
                            # Create a generic response if nothing was found
                            st.session_state.responses[post['url']] = {
                                'post': post,
                                'suggested_response': "Please see the full analysis for the suggested response to this post.",
                                'engagement_potential': "Medium"
                            }
                            st.session_state.debug_info["parsing_steps"].append(f"Created generic response for: {post['title']}")
                
                # Debug: Show parsing results
                st.session_state.debug_info["responses_found"] = len(st.session_state.responses)
                
            except Exception as e:
                st.error(f"Error parsing response: {str(e)}")
                # Log the full exception for debugging
                import traceback
                error_details = traceback.format_exc()
                
                with st.expander("Debug: Error Details", expanded=True):
                    st.code(error_details)
                
                # Create a fallback response
                for post in st.session_state.selected_posts:
                    st.session_state.responses[post['url']] = {
                        'post': post,
                        'suggested_response': "Error parsing the assistant's response. Please check the full analysis.",
                        'engagement_potential': "Unknown"
                    }
    
    # Display responses
    if st.session_state.responses:
        st.markdown("<h2 class='sub-header'>Engagement Opportunities</h2>", unsafe_allow_html=True)
        
        # Show debug information if available
        if hasattr(st.session_state, 'debug_info'):
            with st.expander("Debug: Parsing Information", expanded=False):
                st.write("### Parsing Steps")
                for step in st.session_state.debug_info.get("parsing_steps", []):
                    st.write(f"- {step}")
                st.write(f"### Results: Found {st.session_state.debug_info.get('responses_found', 0)} responses")
        
        # Display the full response
        if st.session_state.messages and len(st.session_state.messages) >= 1:
            assistant_response = next((msg['content'] for msg in reversed(st.session_state.messages) 
                                     if msg['role'] == 'assistant'), "")
            if assistant_response:
                with st.expander("View Full Analysis", expanded=False):
                    st.markdown(assistant_response)
        
        # Create a cleaner display for responses
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        # Display each post with its suggested response
        for url, data in st.session_state.responses.items():
            post = data['post']
            suggested_response = data['suggested_response']
            engagement_potential = data['engagement_potential']
            
            # Create a card-like container for each response
            with st.container():
                st.markdown("""
                <style>
                .response-card {
                    border: 1px solid #e6e6e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='response-card'>", unsafe_allow_html=True)
                
                # Post title and link
                st.markdown(f"<div class='post-title'>{post['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='post-info'>r/{post['subreddit']} • <a href='{post['url']}' target='_blank' class='reddit-link'>View on Reddit</a></div>", unsafe_allow_html=True)
                
                # Add post preview if it's a text post
                if post.get('is_self', False) and post.get('selftext', ''):
                    preview = post['selftext'][:150] + "..." if len(post['selftext']) > 150 else post['selftext']
                    with st.expander("Show Post Content", expanded=False):
                        st.markdown(preview)
                
                # Suggested response with improved formatting
                st.markdown("<br><span style='font-weight: bold; color: #0078D7;'>Suggested Response:</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='response-box'>{suggested_response}</div>", unsafe_allow_html=True)
                
                # Engagement potential with colored indicator
                potential_color = "#2E8B57" if engagement_potential.lower() == "high" else "#FFA500" if engagement_potential.lower() == "medium" else "#6495ED"
                st.markdown(f"<span style='font-weight: bold;'>Engagement Potential:</span> <span style='color: {potential_color}; font-weight: bold;'>{engagement_potential}</span>", unsafe_allow_html=True)
                
                # Copy button for the response
                if st.button("Copy to Clipboard", key=f"copy_{post['url']}"):
                    st.code(suggested_response)
                    st.success("Response copied! You can now paste it on Reddit.")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    elif not st.session_state.selected_posts:
        st.info("Select posts in the 'Reddit Posts' tab to generate responses")

# Tab 3: Email
with tab3:
    st.markdown("<h2 class='sub-header'>Email Engagement Opportunities</h2>", unsafe_allow_html=True)
    
    if not st.session_state.responses:
        st.info("Generate responses first in the 'Responses' tab")
    else:
        # Email configuration
        st.markdown("### Configure Email")
        
        if not email_address:
            email_address = st.text_input("Recipient Email:", placeholder="your@email.com", key="email_tab")
        
        subject = st.text_input("Email Subject:", value="Reddit Engagement Opportunities")
        
        include_full_analysis = st.checkbox("Include Full Analysis", value=True)
        
        # Preview email content
        st.markdown("### Email Preview")
        
        email_content = f"# Reddit Engagement Opportunities\n\nHere are your engagement opportunities for maximum karma:\n\n"
        
        # Create a table for the email
        email_content += "| Post Title & Link | Suggested Response | Engagement Potential |\n"
        email_content += "|-------------------|-------------------|---------------------|\n"
        
        for url, data in st.session_state.responses.items():
            post = data['post']
            title_md = f"[{post['title']}]({post['url']})"
            response = data['suggested_response'].replace('\n', ' ')
            potential = data['engagement_potential']
            
            email_content += f"| {title_md} | {response} | {potential} |\n"
        
        # Add the full analysis if requested
        if include_full_analysis and st.session_state.messages:
            assistant_response = next((msg['content'] for msg in reversed(st.session_state.messages) 
                                     if msg['role'] == 'assistant'), "")
            if assistant_response:
                email_content += "\n\n## Full Analysis\n\n"
                email_content += assistant_response
        
        # Show preview
        with st.expander("Email Content Preview", expanded=True):
            st.markdown(email_content)
        
        # Send email button
        if st.button("Send Email", type="primary"):
            if not email_address:
                st.error("Please enter an email address")
            else:
                with st.spinner("Sending email..."):
                    # Use our dedicated email sender function
                    email_success = send_engagement_email(
                        anthropic_client, 
                        th_client, 
                        email_address, 
                        subject, 
                        email_content
                    )
                    
                    if email_success:
                        st.session_state.email_sent = True
                        st.success(f"✅ Email sent successfully to {email_address}")
                    else:
                        st.error("Failed to send email. Please try again.")

# Handle any email request from the sidebar
if hasattr(st.session_state, 'email_requested') and st.session_state.email_requested:
    with st.spinner("Sending email from sidebar..."):
        email_address = st.session_state.email_address
        
        # Create email content
        email_content = f"# Reddit Engagement Opportunities\n\nHere are your engagement opportunities for maximum karma:\n\n"
        
        # Create a table for the email
        email_content += "| Post Title & Link | Suggested Response | Engagement Potential |\n"
        email_content += "|-------------------|-------------------|---------------------|\n"
        
        for url, data in st.session_state.responses.items():
            post = data['post']
            title_md = f"[{post['title']}]({post['url']})"
            response = data['suggested_response'].replace('\n', ' ')
            potential = data['engagement_potential']
            
            email_content += f"| {title_md} | {response} | {potential} |\n"
        
        # Add full analysis
        if st.session_state.messages:
            assistant_response = next((msg['content'] for msg in reversed(st.session_state.messages) 
                                     if msg['role'] == 'assistant'), "")
            if assistant_response:
                email_content += "\n\n## Full Analysis\n\n"
                email_content += assistant_response
        
        # Use our dedicated email sender function for sidebar emails too
        email_success = send_engagement_email(
            anthropic_client, 
            th_client, 
            email_address, 
            "Reddit Engagement Opportunities", 
            email_content
        )
        
        # Reset the email request flag
        st.session_state.email_requested = False
        
        # Show success message
        if email_success:
            st.sidebar.success(f"✅ Email sent to {email_address}")
        else:
            st.sidebar.error("Failed to send email. Please try again.")