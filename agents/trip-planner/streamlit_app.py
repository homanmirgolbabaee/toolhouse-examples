import streamlit as st
import requests
import json
import time
import base64
import os

# Main Streamlit app
st.set_page_config(page_title="Travel Advisor", layout="wide", initial_sidebar_state="collapsed")

# Add sidebar for API key management
with st.sidebar:
    st.title("Settings")
    
    # API key input with environment variable fallback
    api_key = st.text_input(
        "Toolhouse API Key", 
        value=os.environ.get("TOOLHOUSE_API_KEY", "th-Iim4benuS8hMsDNCWAFtOrQknQa5P9EsprRiaTIHpP0"),
        type="password",
        help="Enter your Toolhouse API key"
    )
    
    # Save API key button
    if st.button("Save API Key"):
        if api_key:
            st.success("API key saved for this session")
        else:
            st.error("Please enter an API key")
    
    # API key info and link
    st.markdown("---")
    st.markdown("### How to get an API key")
    st.markdown("Get your API key from the [Toolhouse Console](https://toolhouse.ai/settings)")
    
    # Clear conversation button
    if st.button("Clear Session Data"):
        # Reset all session states
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Function to handle the API request and response for travel advice
def fetch_travel_advice(destination, age, trip_duration):
    # Prepare the data for the POST request
    data = {
        "chat_id": "38c03f17-071e-46af-9632-bb55485513ed",
        "vars": {
            "destination": destination,
            "age": age,
            "trip_duration": trip_duration
        }
    }

    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Create a placeholder for the status message
    status_placeholder = st.empty()
    
    # Send the POST request to start the agent run
    response = requests.post("https://api.toolhouse.ai/v1/agent-runs", headers=headers, json=data)

    if response.status_code == 200:
        status_placeholder.write("API call successful! Initial response:")
        st.json(response.json())
        
        # Get the agent run ID from the response
        agent_run_id = response.json()['data']['id']

        # Poll the status of the agent run
        status = "queued"  # Start with queued status
        progress_bar = st.progress(0)
        
        while status != "completed" and status != "failed":
            status_placeholder.write(f"Waiting for agent run to complete... Current status: {status}")
            
            # Update progress animation
            if status == "queued":
                progress_value = 0.25
            elif status == "in_progress":
                progress_value = 0.75
            else:
                progress_value = 1.0
                
            progress_bar.progress(progress_value)
            
            time.sleep(5)  # Wait for 5 seconds before checking again

            # Check the status of the agent run
            status_response = requests.get(
                f"https://api.toolhouse.ai/v1/agent-runs/{agent_run_id}",
                headers=headers
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data['data']['status']
            else:
                st.error(f"Error while checking status: {status_response.status_code}")
                return None

        # Clear the status placeholder and progress bar once complete
        status_placeholder.empty()
        progress_bar.empty()
        
        # Once the status is 'completed', print the actual results
        if status == "completed":
            st.write("Agent run completed! Results:")
            
            # Store the complete results data
            results = status_data['data']['results']
            
            # Find the last message from the assistant
            assistant_messages = [r for r in results if r.get('role') == 'assistant']
            
            if assistant_messages:
                # Get the last assistant message
                last_assistant_message = assistant_messages[-1]
                
                # Extract the text content (the JSON output)
                if 'content' in last_assistant_message:
                    if isinstance(last_assistant_message['content'], list):
                        for content_item in last_assistant_message['content']:
                            if content_item.get('type') == 'text':
                                try:
                                    # Parse the JSON string into a Python dictionary
                                    travel_plan_text = content_item.get('text', '{}')
                                    travel_plan = json.loads(travel_plan_text)
                                    
                                    # Return both the text and parsed JSON
                                    return travel_plan_text, travel_plan
                                except json.JSONDecodeError:
                                    st.error("Failed to parse the JSON response from the agent.")
                                    return None, None
                    else:
                        # If content is not a list
                        try:
                            travel_plan_text = last_assistant_message['content']
                            travel_plan = json.loads(travel_plan_text)
                            return travel_plan_text, travel_plan
                        except (json.JSONDecodeError, TypeError):
                            st.error("Unexpected response format from the agent.")
                            return None, None
                else:
                    st.warning("No content found in the assistant's response.")
                    return None, None
            else:
                st.warning("No assistant response found in the results.")
                return None, None
        elif status == "failed":
            st.error("Agent run failed. Please try again.")
            return None, None
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return None, None

# Function to fetch visual tour based on travel plan JSON
def fetch_visual_tour(travel_plan_json):
    # Create a placeholder for the visual tour status
    tour_status = st.empty()
    tour_status.write("🔍 Creating your visual tour...")
    
    # Prepare the data for the POST request with the correct variable name "input_json"
    data = {
        "chat_id": "8079d372-16d8-46ed-aec3-38848c873db3",  # Visual tour agent ID
        "vars": {
            "input_json": travel_plan_json  # Using the exact variable name from your curl command
        }
    }

    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Visual tour loading indicator
    tour_progress = st.progress(0)
    
    # Send the POST request to start the agent run
    response = requests.post("https://api.toolhouse.ai/v1/agent-runs", headers=headers, json=data)
    
    if response.status_code == 200:
        # Get the agent run ID from the response
        agent_run_id = response.json()['data']['id']
        
        # Poll the status of the agent run
        status = "queued"
        while status != "completed" and status != "failed":
            # Update status message
            if status == "queued":
                tour_status.write("🔍 Preparing your visual tour...")
                tour_progress.progress(0.3)
            elif status == "in_progress":
                tour_status.write("🖼️ Generating stunning visuals for your trip...")
                tour_progress.progress(0.7)
            
            time.sleep(3)  # Wait before checking again
            
            # Check the status of the agent run
            status_response = requests.get(
                f"https://api.toolhouse.ai/v1/agent-runs/{agent_run_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data['data']['status']
            else:
                tour_status.error(f"Error while checking visual tour status: {status_response.status_code}")
                tour_progress.empty()
                return None, None
        
        # Clear status indicators
        tour_status.empty()
        tour_progress.empty()
        
        # Once completed, extract the visual tour data
        if status == "completed":
            results = status_data['data']['results']
            assistant_messages = [r for r in results if r.get('role') == 'assistant']
            
            if assistant_messages:
                last_assistant_message = assistant_messages[-1]
                
                if 'content' in last_assistant_message:
                    if isinstance(last_assistant_message['content'], list):
                        for content_item in last_assistant_message['content']:
                            if content_item.get('type') == 'text':
                                try:
                                    visual_tour_text = content_item.get('text', '{}')
                                    visual_tour = json.loads(visual_tour_text)
                                    return visual_tour_text, visual_tour
                                except json.JSONDecodeError:
                                    st.error("Failed to parse the visual tour JSON response.")
                                    return None, None
                    else:
                        try:
                            visual_tour_text = last_assistant_message['content']
                            visual_tour = json.loads(visual_tour_text)
                            return visual_tour_text, visual_tour
                        except (json.JSONDecodeError, TypeError):
                            st.error("Failed to parse the visual tour response.")
                            return None, None
            else:
                st.error("No visual tour data returned from the agent.")
                return None, None
        else:
            st.error("Failed to generate the visual tour.")
            return None, None
    else:
        st.error(f"Visual Tour API Error: {response.status_code}")
        return None, None

# Function to display the travel plan
def display_travel_plan(travel_plan):
    if not travel_plan:
        return
        
    st.subheader(f"📍 Travel Plan for {travel_plan.get('destination', 'Your Destination')}")
    
    # Display traveler info
    traveler_info = travel_plan.get('traveler_info', {})
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"👤 Age: {traveler_info.get('age')}")
    with col2:
        st.write(f"⏱️ Trip Duration: {traveler_info.get('trip_duration_days')} days")
    
    # Display daily activities
    st.subheader("📆 Daily Itinerary")
    for day in travel_plan.get('trip_plan', []):
        with st.expander(f"Day {day.get('day')}", expanded=True):
            for activity in day.get('activities', []):
                st.markdown(f"### {activity.get('name')}")
                st.write(activity.get('description', ''))
                st.write(f"📍 **Location:** {activity.get('location', '')}")
                st.write(f"⏱️ **Duration:** {activity.get('estimated_time', '')}")
                st.write(f"👥 **Suitability:** {activity.get('suitability', '')}")
                st.write("---")
    
    # Display recommendations
    recommendations = travel_plan.get('recommendations', {})
    
    if recommendations.get('food'):
        st.subheader("🍽️ Food Recommendations")
        cols = st.columns(2)
        for i, food in enumerate(recommendations.get('food', [])):
            with cols[i % 2]:
                st.markdown(f"### {food.get('name')}")
                st.write(f"**Type:** {food.get('type')}")
                st.write(f"📍 **Location:** {food.get('location')}")
                st.write(f"ℹ️ {food.get('notes')}")
    
    if recommendations.get('accommodations'):
        st.subheader("🏨 Accommodation Recommendations")
        cols = st.columns(2)
        for i, acc in enumerate(recommendations.get('accommodations', [])):
            with cols[i % 2]:
                st.markdown(f"### {acc.get('name')}")
                st.write(f"📍 **Location:** {acc.get('location')}")
                st.write(f"💰 **Price Range:** {acc.get('price_range')}")
                st.write(f"✨ **Features:** {', '.join(acc.get('features', []))}")
    
    if recommendations.get('tips'):
        st.subheader("💡 Travel Tips")
        for i, tip in enumerate(recommendations.get('tips', []), 1):
            st.write(f"{i}. {tip}")

# Enhanced function to display visual tour with better image handling
def display_visual_tour(attractions_data):
    if not attractions_data:
        st.error("No visual tour data to display.")
        return
    
    destination = st.session_state.travel_plan.get('destination', 'Your Destination') if st.session_state.travel_plan else "Your Destination"
    
    # Add a stylish header
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1E88E5;">📸 Visual Tour of {destination}</h1>
        <p style="font-size: 18px; color: #555;">Explore the must-see attractions through stunning visuals</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a separator
    st.markdown('<hr style="height:2px;border:none;color:#333;background-color:#f0f0f0;" />', unsafe_allow_html=True)
    
    # Display instructions for the gallery
    st.info("⚡ **Scroll through the gallery below to discover the highlights of your destination.**")
    
    # Create a card-based layout for attractions
    for i, attraction in enumerate(attractions_data):
        # Create a card-like container for each attraction
        st.markdown(f"""
        <div style="margin: 30px 0; background-color: white; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background-color: #1E88E5; color: white; padding: 15px 20px;">
                <h2 style="margin: 0;">{i+1}. {attraction.get('name')}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display image and info in columns
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Display the image with proper sizing
            if 'image_url' in attraction:
                st.image(
                    attraction['image_url'],
                    use_container_width=True,  # Changed from use_column_width
                    caption=f"View of {attraction.get('name')}"
                )
        
        with col2:
            # Display historic fact in an attractive format
            if 'historic_fact' in attraction:
                st.markdown("""
                <style>
                .fact-box {
                    background-color: #f8f9fa;
                    border-left: 4px solid #1E88E5;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 5px 5px 0;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="fact-box">
                    <h3 style="margin-top: 0; color: #1E88E5;">📜 Historic Fact</h3>
                    <p style="color: #333; font-size: 16px;">{attraction.get('historic_fact')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add a "View on Map" button (this would be a placeholder unless you implement map functionality)
                # Using a unique key for this button based on attraction name to avoid conflicts
                map_button_key = f"map_button_{i}"
                st.button("📍 View on Map", key=map_button_key, disabled=True)
        
        # Add a separator between attractions
        if i < len(attractions_data) - 1:
            st.markdown('<hr style="height:1px;border:none;color:#333;background-color:#f0f0f0; margin: 30px 0;" />', unsafe_allow_html=True)

    # Add a footer with navigation hint
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
        <p style="color: #555;">Ready to explore these amazing attractions? Don't forget to check your travel plan for daily itinerary details!</p>
    </div>
    """, unsafe_allow_html=True)

# Function to create a download link for JSON data
def get_json_download_link(json_string, filename="travel_plan.json"):
    # Encode the JSON string to bytes
    b64 = base64.b64encode(json_string.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download JSON file</a>'
    return href

# Function to create copy to clipboard button for JSON
def get_copy_button(json_string, button_text="Copy JSON"):
    # Create a unique button ID to avoid conflicts
    button_id = f"copy_button_{hash(json_string) % 10000000}"  # Use modulo to keep the ID shorter
    
    # Create a JavaScript-friendly JSON string by escaping single quotes and line breaks
    js_safe_json = json_string.replace("'", "\\'").replace("\n", "\\n").replace('"', '\\"')
    
    st.markdown(f"""
    <style>
    #{button_id} {{
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 10px;
    }}
    #{button_id}:hover {{
        background-color: #3e8e41;
    }}
    </style>
    <button id="{button_id}" onclick="copyToClipboard()">
        {button_text}
    </button>
    <script>
    function copyToClipboard() {{
        const text = `{js_safe_json}`;
        navigator.clipboard.writeText(text)
        .then(() => {{
            let button = document.getElementById("{button_id}");
            button.innerHTML = "Copied!";
            setTimeout(function() {{
                button.innerHTML = "{button_text}";
            }}, 2000);
        }})
        .catch(err => {{
            console.error('Error copying text: ', err);
        }});
    }}
    </script>
    """, unsafe_allow_html=True)

# Custom CSS for styling the entire app
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    h1, h2, h3 {
        color: #1E88E5;
    }
    .stExpander {
        border-radius: 8px;
        border: 1px solid #f0f0f0;
    }
    .json-container {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
    }
    .button-container {
        display: flex;
        gap: 10px;
        margin: 15px 0;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1976D2;
    }
    /* Make images appear crisp and high-quality */
    img {
        object-fit: cover;
        border-radius: 5px;
    }
    /* Style the text inputs */
    .stTextInput>div>div>input {
        border-radius: 4px;
        border: 1px solid #ddd;
        padding: 8px 12px;
    }
    /* Add a subtle effect to the app background */
    .stApp {
        background: linear-gradient(to bottom, #f5f7fa, #ffffff);
    }
</style>
""", unsafe_allow_html=True)

# Create a banner
st.markdown("""
<div style="background-color: #1E88E5; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; text-align: center;">
    <h1 style="color: white; margin: 0;">✈️ Travel Advisor</h1>
    <p style="color: white; margin-top: 0.5rem;">Get personalized travel plans and explore stunning destinations</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for app state management
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'travel_plan_text' not in st.session_state:
    st.session_state.travel_plan_text = None
if 'visual_tour' not in st.session_state:
    st.session_state.visual_tour = None
if 'visual_tour_text' not in st.session_state:
    st.session_state.visual_tour_text = None
if 'page' not in st.session_state:
    st.session_state.page = "travel_plan"  # Default page is travel plan

# User input fields
if st.session_state.page == "travel_plan":
    # Create a more attractive input form
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #1E88E5; margin-top: 0;">Plan Your Adventure</h2>
        <p style="color: #555;">Enter your travel details below to get personalized recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a form-like container with columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        destination = st.text_input("Where do you want to go?", placeholder="e.g., Rome, Tokyo, etc.")
    
    with col2:
        age = st.text_input("Your age", placeholder="e.g., 24")
    
    with col3:
        trip_duration = st.text_input("Trip duration (days)", placeholder="e.g., 3")

    # Using form to properly handle button logic
    with st.form(key="travel_form"):
        # Submit button with a more attractive style and a unique key
        submit_button = st.form_submit_button(
            label="🚀 Get Travel Advice", 
            help="Click to generate your personalized travel plan"
        )

    # Process form submission
    if submit_button:
        if destination and age and trip_duration:
            # Reset session state for a new travel plan
            st.session_state.visual_tour = None
            st.session_state.visual_tour_text = None
            
            # Fetch travel advice
            travel_plan_text, travel_plan = fetch_travel_advice(destination, age, trip_duration)
            
            if travel_plan_text and travel_plan:
                st.session_state.travel_plan_text = travel_plan_text
                st.session_state.travel_plan = travel_plan
    
    # Display travel plan if it exists
    if st.session_state.travel_plan:
        # Display the travel plan
        display_travel_plan(st.session_state.travel_plan)
        
        # Display the raw JSON with copy and download options
        st.subheader("Raw JSON Output")
        with st.expander("View Raw JSON", expanded=False):
            st.json(st.session_state.travel_plan)
            st.markdown("##### Download or Copy JSON")
            col1, col2 = st.columns(2)
            with col1:
                # Copy button
                get_copy_button(st.session_state.travel_plan_text, "Copy JSON")
            with col2:
                # Download link
                st.markdown(get_json_download_link(st.session_state.travel_plan_text), unsafe_allow_html=True)
        
        # Enter Visual Tour button with attractive styling
        st.markdown("""
        <div style="margin-top: 30px; text-align: center;">
            <hr style="margin: 30px 0; border: none; height: 1px; background-color: #f0f0f0;">
            <h3 style="color: #1E88E5;">Ready to see your destination?</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Use a unique key for this Enter Visual Tour button
        if st.button("✨ Enter Visual Tour", help="Click to see images of your destination", key="enter_tour_btn"):
            # Change to visual tour page
            st.session_state.page = "visual_tour"
            st.rerun()

# Visual Tour page
elif st.session_state.page == "visual_tour":
    # Back button with icon and unique key
    if st.button("← Back to Travel Plan", key="back_btn"):
        st.session_state.page = "travel_plan"
        st.rerun()
    
    # If we already have a visual tour, display it
    if st.session_state.visual_tour:
        # Use the enhanced display function for better UI
        display_visual_tour(st.session_state.visual_tour)
        
        # Display the raw JSON with copy and download options in a collapsible section
        with st.expander("🔍 View Raw Visual Tour JSON", expanded=False):
            st.json(st.session_state.visual_tour)
            st.markdown("##### Download or Copy JSON")
            col1, col2 = st.columns(2)
            with col1:
                # Copy button
                get_copy_button(st.session_state.visual_tour_text, "Copy JSON")
            with col2:
                # Download link
                st.markdown(get_json_download_link(st.session_state.visual_tour_text, "visual_tour.json"), unsafe_allow_html=True)
    
    # If we don't have a visual tour yet, fetch it
    elif st.session_state.travel_plan_text:
        visual_tour_text, visual_tour = fetch_visual_tour(st.session_state.travel_plan_text)
        
        if visual_tour_text and visual_tour:
            st.session_state.visual_tour_text = visual_tour_text
            st.session_state.visual_tour = visual_tour
            
            # Use the enhanced display function for better UI
            display_visual_tour(visual_tour)
            
            # Display the raw JSON with copy and download options in a collapsible section
            with st.expander("🔍 View Raw Visual Tour JSON", expanded=False):
                st.json(visual_tour)
                st.markdown("##### Download or Copy JSON")
                col1, col2 = st.columns(2)
                with col1:
                    # Copy button
                    get_copy_button(visual_tour_text, "Copy JSON")
                with col2:
                    # Download link
                    st.markdown(get_json_download_link(visual_tour_text, "visual_tour.json"), unsafe_allow_html=True)
        else:
            st.error("Failed to generate visual tour. Please try again.")
            # Return to travel plan page
            st.session_state.page = "travel_plan"
            st.rerun()
    else:
        st.error("No travel plan found. Please create a travel plan first.")
        # Return to travel plan page
        st.session_state.page = "travel_plan"
        st.rerun()

# Add a footer
st.markdown("""
<div style="margin-top: 50px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center;">
    <p style="color: #555; margin-bottom: 0;">Powered by Toolhouse ❤️</p>
</div>
""", unsafe_allow_html=True)