import os
import streamlit as st
import json
import re
from anthropic import Anthropic
from toolhouse import Toolhouse, Provider




# Initialize clients
@st.cache_resource
def initialize_clients():
    """Initialize Anthropic and Toolhouse clients"""
    anthropic_api_key = st.session_state.get("ANTHROPIC_API_KEY")
    toolhouse_api_key = st.session_state.get("TOOLHOUSE_API_KEY")

    
    # Check if API keys are available
    if not anthropic_api_key or not toolhouse_api_key:
        st.error("Missing API keys. Please set ANTHROPIC_API_KEY and TOOLHOUSE_API_KEY environment variables.")
        st.stop()
    
    # Initialize clients
    anthropic_client = Anthropic(api_key=anthropic_api_key)
    th_client = Toolhouse(api_key=toolhouse_api_key, provider=Provider.ANTHROPIC)
    
    return anthropic_client, th_client

def search_jobs(anthropic_client, th_client, location,job_position):
    """Search for jobs using Toolhouse tools"""
    # Create a simple message
    messages = [{
        "role": "user", 
        "content": f"Search for job openings for following job position:{job_position} in the following location:{location}. Return the results as a JSON object with format {{\"job_openings\": [{{\"title\": \"Job Title\", \"link\": \"URL\"}}]}}"
    }]
    
    # Call Claude with Toolhouse tools
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=f"Search for job openings in {location}",
        tools=th_client.get_tools(),
        messages=messages
    )
    
    # Process tool results
    tool_results = th_client.run_tools(response)
    
    # Final response with tool results incorporated
    final_response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=f"Search for job openings in {location}",
        tools=th_client.get_tools(),
        messages=messages + tool_results
    )
    
    return final_response, tool_results

def extract_jobs(response_text):
    """Extract job listings from the response text"""
    # Try to find a JSON object in the response
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    json_matches = re.findall(json_pattern, response_text)
    
    if json_matches:
        try:
            # Try to parse as JSON
            job_data = json.loads(json_matches[0])
            if "job_openings" in job_data:
                return job_data["job_openings"]
        except json.JSONDecodeError:
            pass
    
    # Fallback to regex extraction
    title_matches = re.findall(r'"title":\s*"([^"]+)"', response_text)
    link_matches = re.findall(r'"link":\s*"([^"]+)"', response_text)
    
    if len(title_matches) == len(link_matches) and len(title_matches) > 0:
        jobs = []
        for i in range(len(title_matches)):
            jobs.append({
                "title": title_matches[i],
                "link": link_matches[i]
            })
        return jobs
    
    return []

# Set up Streamlit UI
st.set_page_config(
    page_title="Toolhouse Job Finder",
    page_icon="💼",
    layout="centered"
)
# Sidebar for API keys 🔐
st.sidebar.header("API Configuration")
anthropic_api_key_input = st.sidebar.text_input("Anthropic API Key", type="password")
toolhouse_api_key_input = st.sidebar.text_input("Toolhouse API Key", type="password")


# Save API keys to session state
if anthropic_api_key_input:
    st.session_state["ANTHROPIC_API_KEY"] = anthropic_api_key_input
if toolhouse_api_key_input:
    st.session_state["TOOLHOUSE_API_KEY"] = toolhouse_api_key_input
# Custom CSS for better styling
st.markdown("""
    <style>
    .job-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .job-title {
        color: #0066cc;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .view-button {
        background-color: #0066cc;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 10px 0;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Main app
st.title("Toolhouse Job Finder")
st.markdown("Find job openings using Toolhouse!")

# Location input
location = st.text_input("Enter location for job search", "spain")
job_position = st.text_input("Enter job position", "software engineer")
# Submit button
if st.button("Find Jobs"):
    try:
        # Initialize clients
        anthropic_client, th_client = initialize_clients()
        
        # Show loading spinner during search
        with st.spinner(f"Searching for jobs in {location}..."):
            final_response, tool_results = search_jobs(anthropic_client, th_client, location,job_position)
            response_text = final_response.content[0].text
            
            # Extract jobs
            jobs = extract_jobs(response_text)
        
        # Display results
        if jobs:
            # Success message
            st.markdown(f'<div class="success-message">Found {len(jobs)} jobs in {location}</div>', unsafe_allow_html=True)
            
            # Display job cards
            for job in jobs:
                st.markdown(
                    f"""
                    <div class="job-card">
                        <div class="job-title">{job['title']}</div>
                        <a href="{job['link']}" target="_blank" class="view-button" style="color: white;">View Job Details</a>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
            # Show raw response in expander
            with st.expander("View Raw Response", expanded=False):
                st.text(response_text)
            
            # Show tool results in expander
            with st.expander("View Tool Results", expanded=False):
                st.json(tool_results)
        else:
            st.warning(f"No jobs found in {location}. Try another location.")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")