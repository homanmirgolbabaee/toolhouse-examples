import os
import streamlit as st
import time
from anthropic import Anthropic
from toolhouse import Toolhouse, Provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
@st.cache_resource
def initialize_clients():
    """Initialize Anthropic and Toolhouse clients"""
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    toolhouse_api_key = os.getenv("TOOLHOUSE_API_KEY")
    
    # Check if API keys are available
    if not anthropic_api_key:
        st.error("Missing ANTHROPIC_API_KEY environment variable")
        st.stop()
    if not toolhouse_api_key:
        st.error("Missing TOOLHOUSE_API_KEY environment variable")
        st.stop()
    
    # Initialize clients
    anthropic_client = Anthropic(api_key=anthropic_api_key)
    th_client = Toolhouse(api_key=toolhouse_api_key, provider=Provider.ANTHROPIC)
    
    return anthropic_client, th_client

# System prompt for the due diligence assistant
def create_system_prompt(startup_name, website_url) -> str:
    """Create the system prompt for the due diligence assistant"""
    return f"""
    Create me perform initial due diligence on {startup_name} for my investment research, here is company website url {website_url}
    1. Search Internet to Gather key company information:
       - Use exa_web_search to find the company website, founding date, and location
       - Identify what the startup does and what problem they're solving
       - Determine their business model and revenue streams
       - Find their current stage (seed, Series A, B, etc.)
    2. Search Linkedin to Research the team:
       - Use exa_linkedin_search to identify founders and key executives
       - Summarize relevant background and prior experience
       - Note any notable advisors or board members
    3. Search Internet to Get funding and financials Numbers:
       - Use exa_web_search to gather funding history and investors
       - Find any publicly available metrics on growth or revenue (from whatever is publicly available; For example: crunchbase, pitchbook, or any other known public sources)
       - Identify recent funding rounds or financial news
    4. Examine market position:
       - Identify main competitors and market size
       - Find customer reviews or testimonials
       - Note any major partnerships or client relationships
    5. Search on X(Twitter) to Track recent Activities:
       - Use search_x to list company's latest 3 tweets 
    6. Format and deliver:
       - Incorporate proper HTML and CSS to Compile findings into a concise, organized report, inserted into proper tables
       - Include all relevant links for further research
       - Focus on facts rather than opinions, and clearly indicate when information is unavailable.
       - DO NOT send any emails during this research phase
       
    Use proper HTML formatting with tables and styling. Make sure every finding is organized in a clear, readable format.
    This is critical: DO NOT include placeholder text or mention that you are "currently gathering information".
    I need complete, factual findings only. If information is unavailable, state that clearly but still provide a complete report
    with whatever information you were able to find.
    """

# Separate system prompt dedicated to email sending
def create_email_system_prompt(startup_name) -> str:
    """Create a system prompt specifically for sending emails"""
    return f"""
    You are an email assistant. Your only job is to format and send the research report about {startup_name}.
    
    IMPORTANT REQUIREMENTS:
    1. Format the email with proper HTML tables and styling 
    2. Make sure the information is presented clearly and professionally
    3. Use the exact content provided - do not summarize or reduce the information
    4. Make sure all details, links, and sections from the original report are included
    5. Organize the content in a clear, readable format with tables
    6. Do not add any introduction or conclusion beyond what's in the report
    7. Include a professional subject line: "{startup_name} Investment Research"
    
    Send the complete email with all available information. This is critical: DO NOT send placeholder text
    or mention that you are "currently gathering information". Send only the actual complete findings.
    """

def run_due_diligence(anthropic_client, th_client, startup_name, website_url):
    """Run the due diligence process and ensure complete output"""
    system_prompt = create_system_prompt(startup_name, website_url)
    
    # Create the initial message
    messages = [{
        "role": "user", 
        "content": f"Perform detailed due diligence on {startup_name}. Their website is {website_url}. I need comprehensive information on the company, founding team, funding history, market position, and recent activities. Format the results in clear HTML tables."
    }]
    
    # Start the analysis with progress indicators
    progress_placeholder = st.empty()
    status_text = st.empty()
    
    # Step 1: Initial query with tool access
    progress_placeholder.progress(0.1)
    status_text.text("Step 1/4: Gathering initial information...")
    
    response = anthropic_client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system=system_prompt,
        tools=th_client.get_tools(),
        messages=messages
    )
    progress_placeholder.progress(0.25)
    
    # Step 2: Run tools based on the response
    status_text.text("Step 2/4: Processing research data...")
    tool_results = th_client.run_tools(response)
    messages.extend(tool_results)
    progress_placeholder.progress(0.5)
    
    # Step 3: Generate comprehensive report with all gathered information
    status_text.text("Step 3/4: Analyzing results and compiling report...")
    final_prompt = """
    Based on all the information you've gathered, compile a comprehensive due diligence report.
    
    Requirements:
    1. Organize all findings in proper HTML tables with clear styling
    2. Include ALL information you've discovered, not just highlights
    3. Use section headings for different aspects (Company Overview, Team, Funding, etc.)
    4. Include links to sources wherever available
    5. Present facts rather than opinions
    6. Format the report for maximum readability and professional appearance
    7. Do not include any placeholders or mentions of "gathering information" - only present actual findings
    
    Create a complete, thorough report with all available information - this will be used for investment decisions.
    """
    messages.append({"role": "user", "content": final_prompt})
    
    final_response = anthropic_client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        system=system_prompt,
        tools=th_client.get_tools(),
        messages=messages
    )
    
    # Step 4: Process any final tool calls if needed
    status_text.text("Step 4/4: Finalizing report...")
    final_tool_results = th_client.run_tools(final_response)
    if final_tool_results:
        messages.extend(final_tool_results)
        
        # If there were more tool calls, generate one final response
        final_final_prompt = """
        Now that you have all the information, create the final complete due diligence report
        with proper HTML formatting and tables. Include everything you've found about the company.
        """
        messages.append({"role": "user", "content": final_final_prompt})
        
        final_final_response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )
        
        # Extract the report content from the final response
        report_content = ""
        for content_block in final_final_response.content:
            if hasattr(content_block, "text"):
                report_content += content_block.text
    else:
        # Extract the report content from the assistant's response
        report_content = ""
        for content_block in final_response.content:
            if hasattr(content_block, "text"):
                report_content += content_block.text
    
    # Add default styling to ensure attractive formatting
    css_style = """
    <style>
        .report-container {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #1E3A8A;
            border-bottom: 2px solid #4B72B0;
            padding-bottom: 10px;
            font-size: 24px;
            margin-top: 25px;
        }
        h2 {
            color: #2C5282;
            margin-top: 20px;
            border-bottom: 1px solid #BEE3F8;
            padding-bottom: 5px;
            font-size: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        th {
            background-color: #E6F2FF;
            padding: 12px;
            text-align: left;
            border: 1px solid #BEE3F8;
            font-weight: bold;
        }
        td {
            padding: 10px;
            border: 1px solid #E2E8F0;
            vertical-align: top;
        }
        tr:nth-child(even) {
            background-color: #F7FAFC;
        }
        .section {
            margin-bottom: 30px;
            padding: 15px;
            background-color: #FFFFFF;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .highlight {
            background-color: #FFFBEA;
            padding: 15px;
            border-left: 4px solid #F6AD55;
            margin: 15px 0;
        }
        a {
            color: #3182CE;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .tweet {
            border-left: 3px solid #1DA1F2;
            padding-left: 15px;
            margin: 10px 0;
            background-color: #F7FAFC;
            padding: 10px;
        }
        ul, ol {
            margin-left: 20px;
            margin-bottom: 15px;
        }
        li {
            margin-bottom: 5px;
        }
    </style>
    """
    
    # Check if report already has HTML
    if "<html" not in report_content.lower() and "<!doctype" not in report_content.lower():
        # Extract just the body content if there are HTML tags
        if "<body" in report_content.lower() and "</body>" in report_content.lower():
            start_idx = report_content.lower().find("<body")
            end_idx = report_content.lower().find("</body>") + 7
            report_content = report_content[start_idx:end_idx]
        
        # Add the styling
        report_content = f"<div class='report-container'>{css_style}{report_content}</div>"
    
    # Check if the report seems incomplete (less than 1000 characters or missing key sections)
    if len(report_content) < 1000 or not any(section in report_content.lower() for section in ["founder", "fund", "market", "competitor"]):
        # Flag as potentially incomplete
        st.warning("The report may be incomplete. You might want to try again or check the debug information.")
    
    progress_placeholder.progress(1.0)
    status_text.text("Due diligence completed!")
    
    return report_content, messages

def send_email_report(anthropic_client, th_client, startup_name, email_address, report_content):
    """Send the due diligence report via email ensuring full content is transmitted"""
    # Create a system prompt specifically for email sending
    email_system_prompt = create_email_system_prompt(startup_name)
    
    # Create a message instructing to send the email with the FULL report
    email_message = [{
        "role": "user", 
        "content": f"""
        Send an email with the following details:
        
        TO: {email_address}
        SUBJECT: {startup_name} Investment Research
        
        CONTENT: 
        {report_content}
        
        IMPORTANT: 
        1. Include ALL the information above in the email
        2. Format it with proper HTML tables and styling
        3. Make sure all details are preserved exactly as provided
        4. Do NOT summarize or reduce the information
        5. Do NOT include placeholder text about "gathering information"
        """
    }]
    
    # Send the email using Toolhouse
    email_response = anthropic_client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,  # Increase token limit to handle large reports
        system=email_system_prompt,
        tools=th_client.get_tools(),
        messages=email_message
    )
    
    # Execute email sending tool
    email_results = th_client.run_tools(email_response)
    
    # Check if email was sent successfully
    success = any("send_email" in str(msg) for msg in email_results)
    
    return success, email_results

# Set up Streamlit UI
def main():
    st.set_page_config(
        page_title="Startup Due Diligence Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem !important;
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem !important;
            color: #0078D7;
            margin-bottom: 1rem;
        }
        .report-container {
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            background-color: white;
            margin-top: 20px;
        }
        .email-container {
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #d0e8ff;
            background-color: #f0f8ff;
            margin-top: 20px;
        }
        .stProgress > div > div > div {
            background-color: #4361ee !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Initialize session state for storing the report
    if 'report_content' not in st.session_state:
        st.session_state.report_content = None
    if 'startup_name' not in st.session_state:
        st.session_state.startup_name = None
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False
    if 'debug_email_results' not in st.session_state:
        st.session_state.debug_email_results = None
    
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Startup Due Diligence</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("""
        ### How it works
        
        This tool performs comprehensive due diligence on startups by:
        
        1. Gathering company information
        2. Researching the founding team
        3. Analyzing funding history
        4. Examining market position
        5. Tracking recent activities
        6. Delivering an organized report

        """)
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        Built with:
        - Streamlit
        - Anthropic Claude
        - Toolhouse SDK
        """)
        # Add a link to Agent Studio
        st.markdown("<h2 style='color: #FF4B4B;'>Check out the Agent Studio where this agent was built: <a href='https://app.toolhouse.ai/agents/e0edf907-41b9-4529-b477-5c0d5fc6db9f'>Agent Studio Link</a></h2>", unsafe_allow_html=True)
            

    # Main content
    st.markdown("<h1 class='main-header'>Startup Due Diligence Assistant</h1>", unsafe_allow_html=True)
    st.markdown("Automate investment research with AI-powered due diligence")
    
    # Input form
    st.markdown("<h2 class='sub-header'>Company Information</h2>", unsafe_allow_html=True)
    
    with st.form("startup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            startup_name = st.text_input("Startup Name", placeholder="e.g., Stripe, Notion, Anthropic")
        
        with col2:
            website_url = st.text_input("Company Website", placeholder="e.g., https://stripe.com")
        
        example_companies = st.selectbox(
            "Or select an example company:",
            ["", "Anthropic", "Notion", "Replit", "Scale AI", "Cohere"],
            index=0
        )
        
        submitted = st.form_submit_button("Start Due Diligence")
    
    # Handle example selection
    if example_companies and not startup_name:
        example_websites = {
            "Anthropic": "https://anthropic.com",
            "Notion": "https://notion.so",
            "Replit": "https://replit.com",
            "Scale AI": "https://scale.com",
            "Cohere": "https://cohere.com"
        }
        startup_name = example_companies
        website_url = example_websites.get(example_companies, "")
    
    # Process form submission
    if submitted and startup_name and website_url:
        # Initialize clients
        try:
            anthropic_client, th_client = initialize_clients()
            
            # Run the due diligence process
            with st.spinner(f"Performing due diligence on {startup_name}..."):
                report, messages = run_due_diligence(
                    anthropic_client, 
                    th_client, 
                    startup_name, 
                    website_url
                )
            
            # Store the report in session state
            st.session_state.report_content = report
            st.session_state.startup_name = startup_name
            st.session_state.email_sent = False
            
            # Display success message
            st.success("Due diligence completed!")
            
            # Display the report
            st.markdown("<h2 class='sub-header'>Due Diligence Report</h2>", unsafe_allow_html=True)
            st.markdown(f"<div class='report-container'>{report}</div>", unsafe_allow_html=True)
            
            # Provide debug information in an expander
            with st.expander("Debug Information", expanded=False):
                st.markdown("### Message History")
                for i, msg in enumerate(messages):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    
                    if isinstance(content, list):
                        content = "[Complex content structure]"
                    elif isinstance(content, str) and len(content) > 500:
                        content = content[:500] + "... [truncated]"
                    
                    st.markdown(f"**Message {i+1} ({role})**: {content}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Email section (appears only after report is generated)
    if st.session_state.report_content:
        st.markdown("<h2 class='sub-header'>Email the Report</h2>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='email-container'>", unsafe_allow_html=True)
            
            if st.session_state.email_sent:
                st.success("✅ Report has been sent to your email")
                
                # Show email debug info if available
                if st.session_state.debug_email_results:
                    with st.expander("Email Debug Information", expanded=False):
                        st.markdown("### Email Response")
                        for i, msg in enumerate(st.session_state.debug_email_results):
                            st.markdown(f"**Result {i+1}**: {str(msg)[:500]}... [truncated]")
            else:
                st.markdown("Would you like to receive this report via email?")
                
                with st.form("email_form"):
                    email_address = st.text_input("Your Email Address", placeholder="your@email.com")
                    send_email = st.form_submit_button("Send Report via Email")
                    
                    if send_email:
                        if not email_address:
                            st.warning("Please enter your email address")
                        else:
                            # Initialize clients
                            try:
                                anthropic_client, th_client = initialize_clients()
                                
                                # Send the email
                                with st.spinner("Sending email..."):
                                    success, email_results = send_email_report(
                                        anthropic_client,
                                        th_client,
                                        st.session_state.startup_name,
                                        email_address,
                                        st.session_state.report_content
                                    )
                                
                                if success:
                                    st.session_state.email_sent = True
                                    st.session_state.debug_email_results = email_results
                                    st.success(f"✅ Report has been sent to {email_address}")
                                else:
                                    st.error("Failed to send email. Please try again.")
                                    
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Display placeholder if no report yet
    elif not submitted:
        st.info("Fill in the form and click 'Start Due Diligence' to begin the analysis")

if __name__ == "__main__":
    main()