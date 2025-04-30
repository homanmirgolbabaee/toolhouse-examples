import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import tempfile
import fitz  # PyMuPDF for PDF handling
from PIL import Image
import io
import json

# Import Toolhouse integration (conditionally)
try:
    from groq import Groq
    from toolhouse import Toolhouse
    TOOLHOUSE_AVAILABLE = True
except ImportError:
    TOOLHOUSE_AVAILABLE = False

# Define enhanced prompts for better information extraction
DOCUMENT_ANALYSIS_PROMPT = """
Analyze this declassified JFK assassination document image in detail:

1. DOCUMENT IDENTIFICATION:
   - Document type (memo, report, telegram, etc.)
   - Classification level (Top Secret, Secret, Confidential, etc.)
   - Document date and reference numbers
   - Originating agency or department

2. KEY ENTITIES:
   - All individuals mentioned (full names and positions if available)
   - Organizations, agencies, and departments
   - Locations mentioned (cities, countries, specific places)

3. SUBJECT MATTER:
   - Main topic or purpose of the document
   - Key events described or referenced
   - Connections to the Kennedy assassination (if explicit)
   - Any mentioned dates of significance

4. INTELLIGENCE VALUE:
   - Notable facts or claims presented
   - Any redactions or apparent omissions
   - Connections to other known intelligence operations
   - Unusual or seemingly significant details

Format your response in clear sections using the categories above.
"""

SUMMARY_PROMPT_TEMPLATE = """
Create a comprehensive summary of this declassified JFK document based on the following page-by-page analysis:

{all_analysis}

Your summary should:
1. Identify the document type, date, and originating agency
2. Explain the primary subject matter and purpose
3. List all key individuals mentioned and their roles
4. Highlight the most significant revelations or intelligence
5. Note any apparent redactions or missing information
6. Explain connections to the Kennedy assassination investigation
7. Identify any notable inconsistencies or areas requiring further research

Format your summary with clear headings and bullet points for key findings.
"""

# Initialize session state variables if they don't exist
if 'results' not in st.session_state:
    st.session_state.results = []
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'summary_toolhouse' not in st.session_state:
    st.session_state.summary_toolhouse = None
if 'file_details' not in st.session_state:
    st.session_state.file_details = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "upload"  # Possible values: upload, analysis, summary
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'model_choice' not in st.session_state:
    st.session_state.model_choice = "gemini-1.5-flash"
if 'max_pages' not in st.session_state:
    st.session_state.max_pages = 5
if 'use_custom_prompt' not in st.session_state:
    st.session_state.use_custom_prompt = False
if 'user_prompt' not in st.session_state:
    st.session_state.user_prompt = DOCUMENT_ANALYSIS_PROMPT
if 'use_toolhouse' not in st.session_state:
    st.session_state.use_toolhouse = False  # Default to False, will be checked against availability
if 'groq_model' not in st.session_state:
    st.session_state.groq_model = "llama-3.3-70b-versatile"

# Page configuration
st.set_page_config(
    page_title="JFK Files Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
    }
    section[data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 300px;
        max-width: 400px;
    }
    .big-font {
        font-size: 20px !important;
    }
    .medium-font {
        font-size: 18px !important;
    }
    div.stButton > button {
        width: 100%;
    }
    .analysis-box {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f8f9fa;
        color: #333;
    }
    .download-btn {
        display: flex;
        justify-content: flex-end;
        margin-top: 10px;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client if API key is available
if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.error("Gemini API key not found. Please add it to your .env file or Streamlit secrets.")
    st.stop()

# Check for Toolhouse API key
toolhouse_api_key = os.getenv("TOOLHOUSE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
toolhouse_enabled = (toolhouse_api_key is not None and groq_api_key is not None and TOOLHOUSE_AVAILABLE)

# Fix function to correct the Toolhouse message format
def fix_tool_messages(messages):
    fixed_messages = []
    for msg in messages:
        if msg.get("role") == "assistant" and "reasoning" in msg:
            # Replace 'reasoning' with 'content'
            fixed_msg = {
                "role": "assistant",
                "content": msg.get("reasoning", ""),
            }
            # Copy tool_calls if they exist
            if "tool_calls" in msg:
                fixed_msg["tool_calls"] = msg["tool_calls"]
            fixed_messages.append(fixed_msg)
        else:
            # Keep other messages unchanged
            fixed_messages.append(msg)
    return fixed_messages

# Function to run Toolhouse analysis with fixed message handling
def run_toolhouse_analysis(text_content):
    if not toolhouse_enabled or not st.session_state.use_toolhouse:
        return "Toolhouse analysis not enabled. Please check API keys and dependencies."
    
    try:
        # Initialize Toolhouse and Groq
        th = Toolhouse(api_key=toolhouse_api_key)
        groq_client = Groq(api_key=groq_api_key)
        
        # Create prompt with the Gemini analysis
        messages = [{
            "role": "user",
            "content": f"""I'm reading JFK Assassination files published in the National Archives website. 
            I've noticed a document with below content, use tools to help me understand what I'm looking at, act as a history teacher while you're at it.

            The content is provided in the <text> tags:

            <text>
            {text_content}
            </text>"""
        }]
        
        # First API call to get tool calls
        response = groq_client.chat.completions.create(
            model=st.session_state.groq_model,
            messages=messages,
            tools=th.get_tools(),
        )
        
        # Run the tools
        tool_run = th.run_tools(response)
        
        # Fix the messages format before sending to Groq
        fixed_tool_run = fix_tool_messages(tool_run)
        
        # Extend messages with fixed tool run results
        messages.extend(fixed_tool_run)
        
        # Second API call to get the final response
        final_response = groq_client.chat.completions.create(
            model=st.session_state.groq_model,
            messages=messages,
        )
        
        return final_response.choices[0].message.content
    
    except Exception as e:
        return f"Error running Toolhouse analysis: {str(e)}"

# Main function to process PDFs
def process_pdf(pdf_file, max_pages=5, prompt=DOCUMENT_ANALYSIS_PROMPT):
    results = []
    
    # Create a temporary file to save the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Open the PDF using PyMuPDF
        doc = fitz.open(tmp_path)
        total_pages = doc.page_count
        
        # Limit pages to analyze
        pages_to_analyze = total_pages if max_pages == 0 else min(max_pages, total_pages)
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for page_num in range(pages_to_analyze):
            status_text.text(f"Processing page {page_num + 1} of {pages_to_analyze}...")
            
            # Get the page
            page = doc.load_page(page_num)
            
            # Render page to an image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
            img_bytes = pix.tobytes("png")
            
            # Convert to PIL Image for Gemini
            image = Image.open(io.BytesIO(img_bytes))
            
            # Send to Gemini for analysis
            try:
                response = client.models.generate_content(
                    model=st.session_state.model_choice,
                    contents=[prompt, image]
                )
                
                # Store the analysis text
                analysis_text = response.text
                
                results.append({
                    "page_num": page_num + 1,
                    "analysis": analysis_text,
                    "image": img_bytes,
                    "toolhouse_result": None
                })
            except Exception as e:
                results.append({
                    "page_num": page_num + 1,
                    "analysis": f"Error analyzing this page: {str(e)}",
                    "image": img_bytes,
                    "toolhouse_result": None
                })
            
            # Update progress bar
            progress_bar.progress((page_num + 1) / pages_to_analyze)
        
        status_text.text("Processing complete!")
        
        # Close and clean up
        doc.close()
        os.unlink(tmp_path)
        
        return results
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return []

# Function to generate document summary
def generate_summary():
    # Combine all the analysis text
    all_analysis = "\n\n".join([f"**Page {r['page_num']}**:\n{r['analysis']}" for r in st.session_state.results])
    
    # Generate a summary using Gemini
    try:
        summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(all_analysis=all_analysis)
        
        summary_response = client.models.generate_content(
            model=st.session_state.model_choice,
            contents=[summary_prompt]
        )
        return summary_response.text
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

# Function to process single image
def process_single_image(image_file, prompt=DOCUMENT_ANALYSIS_PROMPT):
    try:
        # Load the image
        image = Image.open(image_file)
        
        # Send to Gemini for analysis
        response = client.models.generate_content(
            model=st.session_state.model_choice,
            contents=[prompt, image]
        )
        
        return {
            "analysis": response.text,
            "toolhouse_result": None
        }
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return None

# Function to handle view changes
def change_view(new_view):
    st.session_state.current_view = new_view
    st.rerun()

# App header
st.title("JFK Assassination Files Analyzer")
st.markdown("""
This app helps you analyze declassified JFK assassination files from the National Archives
using Toolhouse.ai and Gemini Vision Models to extract information and provide historical context.
""")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    
    # Model selection - correctly handling stateful UI
    model_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro-vision"]
    model_index = model_options.index(st.session_state.model_choice) if st.session_state.model_choice in model_options else 0
    
    model_choice = st.selectbox(
        "Select Gemini Model",
        model_options,
        index=model_index,
        key="model_selector"
    )
    # Update session state after UI interaction
    st.session_state.model_choice = model_choice
    
    # Page limit
    max_pages = st.number_input(
        "Max pages to analyze (0 for all)",
        min_value=0,
        value=st.session_state.max_pages,
        key="max_pages_input"
    )
    # Update session state after UI interaction
    st.session_state.max_pages = max_pages
    
    # Prompt customization - FIXED CHECKBOX BEHAVIOR
    use_custom_prompt = st.checkbox(
        "Use custom prompt", 
        value=st.session_state.use_custom_prompt,
        key="custom_prompt_checkbox"
    )
    # Update session state after UI interaction
    st.session_state.use_custom_prompt = use_custom_prompt
    
    if st.session_state.use_custom_prompt:
        user_prompt = st.text_area(
            "Custom analysis prompt",
            value=st.session_state.user_prompt,
            height=150,
            key="prompt_textarea"
        )
        # Update session state after UI interaction
        st.session_state.user_prompt = user_prompt
    
    # Advanced configuration (collapsible)
    with st.expander("Advanced Analysis Options"):
        # Toolhouse configuration - FIXED CHECKBOX BEHAVIOR
        use_toolhouse = st.checkbox(
            "Enable Toolhouse", 
            value=st.session_state.use_toolhouse,
            key="toolhouse_checkbox",
            disabled=not toolhouse_enabled
        )
        # Update session state after UI interaction and enforce toolhouse availability
        st.session_state.use_toolhouse = use_toolhouse and toolhouse_enabled
        
        if st.session_state.use_toolhouse and not toolhouse_enabled:
            st.warning("Historical Context requires Toolhouse and Groq API keys.")
        
        if st.session_state.use_toolhouse and toolhouse_enabled:
            groq_options = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
            groq_index = groq_options.index(st.session_state.groq_model) if st.session_state.groq_model in groq_options else 0
            
            groq_model = st.selectbox(
                "Select Groq Model",
                groq_options,
                index=groq_index,
                key="groq_model_selector"
            )
            # Update session state after UI interaction
            st.session_state.groq_model = groq_model
            
            st.info("Historical Context Analysis provides connections to broader research sources.")
    
    # Sidebar actions based on current view
    if st.session_state.current_view == "analysis" or st.session_state.current_view == "summary":
        if st.button("⬅️ Return to Upload", key="return_upload"):
            st.session_state.current_view = "upload"
            st.session_state.results = []
            st.session_state.summary = None
            st.session_state.summary_toolhouse = None
            st.session_state.file_details = None
            st.rerun()
            
        if st.session_state.results and st.session_state.current_view == "analysis":
            if st.button("📊 View Summary", key="go_to_summary"):
                if not st.session_state.summary:
                    st.session_state.summary = generate_summary()
                st.session_state.current_view = "summary"
                st.rerun()
                
        if st.session_state.current_view == "summary":
            if st.button("📄 View Document Analysis", key="go_to_analysis"):
                st.session_state.current_view = "analysis"
                st.rerun()
    
    st.markdown("---")
    st.caption("About")
    st.info("""
    This application uses AI to analyze declassified JFK assassination files.
    Source: [National Archives](https://www.archives.gov/research/jfk/release-2025)
    """)

# Main content area - conditionally display based on current view
if st.session_state.current_view == "upload":
    # Upload section
    st.subheader("Upload Document")
    input_type = st.radio("Choose input type:", ["PDF Document", "Single Image"], horizontal=True)

    if input_type == "PDF Document":
        uploaded_file = st.file_uploader("Upload a JFK file (PDF format)", type=["pdf"])

        if uploaded_file:
            # Display file details
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.session_state.file_details = file_details
            st.write(file_details)
            
            # Process button
            if st.button("🔍 Analyze Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    prompt = st.session_state.user_prompt if st.session_state.use_custom_prompt else DOCUMENT_ANALYSIS_PROMPT
                    st.session_state.results = process_pdf(
                        uploaded_file, 
                        max_pages=st.session_state.max_pages, 
                        prompt=prompt
                    )
                    
                if st.session_state.results:
                    st.session_state.current_view = "analysis"
                    st.rerun()

    else:  # Single Image option
        uploaded_image = st.file_uploader("Upload an image of a JFK document", type=["png", "jpg", "jpeg"])
        
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("🔍 Analyze Image", use_container_width=True):
                with st.spinner("Analyzing image..."):
                    prompt = st.session_state.user_prompt if st.session_state.use_custom_prompt else DOCUMENT_ANALYSIS_PROMPT
                    result = process_single_image(uploaded_image, prompt=prompt)
                    
                    if result:
                        # Create a special single-page result
                        st.session_state.results = [{
                            "page_num": 1,
                            "analysis": result["analysis"],
                            "image": uploaded_image.getvalue(),
                            "toolhouse_result": None
                        }]
                        st.session_state.file_details = {
                            "Filename": uploaded_image.name,
                            "File type": "Image"
                        }
                        st.session_state.current_view = "analysis"
                        st.rerun()

elif st.session_state.current_view == "analysis":
    # Show file details if available
    if st.session_state.file_details:
        st.markdown(f"**File:** {st.session_state.file_details.get('Filename', 'Document')}")
    
    # Navigation buttons
    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("⬅️ Upload New Document", use_container_width=True):
            st.session_state.current_view = "upload"
            st.rerun()
    with cols[1]:
        if st.button("📊 View Document Summary", use_container_width=True):
            if not st.session_state.summary:
                with st.spinner("Generating document summary..."):
                    st.session_state.summary = generate_summary()
            st.session_state.current_view = "summary"
            st.rerun()
    
    st.markdown("---")
    
    # Document analysis results
    st.subheader("Document Analysis")
    
    # Create tabs for each page
    if len(st.session_state.results) > 0:
        page_tabs = st.tabs([f"Page {r['page_num']}" for r in st.session_state.results])
        
        for i, tab in enumerate(page_tabs):
            with tab:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Display the document image
                    st.image(st.session_state.results[i]["image"], 
                             caption=f"Page {st.session_state.results[i]['page_num']}", 
                             use_column_width=True)
                
                with col2:
                    # Display AI analysis in a styled container
                    st.markdown("### AI Analysis")
                    st.markdown(f"""<div class="analysis-box">{st.session_state.results[i]["analysis"]}</div>""", unsafe_allow_html=True)
                    
                    # Download button for basic analysis
                    text_data = f"# Analysis of Page {st.session_state.results[i]['page_num']}\n\n{st.session_state.results[i]['analysis']}"
                    st.download_button(
                        label="💾 Download Analysis",
                        data=text_data,
                        file_name=f"analysis_page_{st.session_state.results[i]['page_num']}.txt",
                        mime="text/plain"
                    )
                    
                    # Historical Context Analysis (if enabled)
                    if toolhouse_enabled and st.session_state.use_toolhouse:
                        st.markdown("---")
                        st.markdown("### Historical Context Analysis")
                        
                        # Only show the button if we don't already have results
                        if not st.session_state.results[i].get("toolhouse_result"):
                            if st.button(f"🔍 Get Historical Context", key=f"toolhouse_{i}", use_container_width=True):
                                with st.spinner("Researching historical context..."):
                                    toolhouse_result = run_toolhouse_analysis(st.session_state.results[i]["analysis"])
                                    st.session_state.results[i]["toolhouse_result"] = toolhouse_result
                                    st.rerun()
                        else:
                            # Display the historical context results
                            st.markdown(f"""<div class="analysis-box">{st.session_state.results[i]["toolhouse_result"]}</div>""", unsafe_allow_html=True)
                            
                            # Download button for complete analysis
                            full_text = f"# Analysis of Page {st.session_state.results[i]['page_num']}\n\n## AI Analysis\n\n{st.session_state.results[i]['analysis']}\n\n## Historical Context Analysis\n\n{st.session_state.results[i]['toolhouse_result']}"
                            st.download_button(
                                label="💾 Download Complete Analysis",
                                data=full_text,
                                file_name=f"complete_analysis_page_{st.session_state.results[i]['page_num']}.txt",
                                mime="text/plain"
                            )

elif st.session_state.current_view == "summary":
    # Show file details if available
    if st.session_state.file_details:
        st.markdown(f"**File:** {st.session_state.file_details.get('Filename', 'Document')}")
    
    # Navigation buttons
    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("⬅️ Upload New Document", use_container_width=True):
            st.session_state.current_view = "upload"
            st.rerun()
    with cols[1]:
        if st.button("📄 View Page Analysis", use_container_width=True):
            st.session_state.current_view = "analysis"
            st.rerun()
    
    st.markdown("---")
    
    # Document summary
    st.subheader("Document Summary")
    
    if st.session_state.summary:
        # Display the summary in a styled container
        st.markdown(f"""<div class="analysis-box">{st.session_state.summary}</div>""", unsafe_allow_html=True)
        
        # Download button for summary
        st.download_button(
            label="💾 Download Summary",
            data=st.session_state.summary,
            file_name="document_summary.txt",
            mime="text/plain"
        )
        
        # Historical Context for the summary
        if toolhouse_enabled and st.session_state.use_toolhouse:
            st.markdown("---")
            st.markdown("### Historical Context for Full Document")
            
            # Only show the button if we don't already have results
            if not st.session_state.summary_toolhouse:
                if st.button("🔍 Get Historical Context for Document", use_container_width=True):
                    with st.spinner("Researching historical context..."):
                        toolhouse_summary = run_toolhouse_analysis(st.session_state.summary)
                        st.session_state.summary_toolhouse = toolhouse_summary
                        st.rerun()
            else:
                # Display the historical context results
                st.markdown(f"""<div class="analysis-box">{st.session_state.summary_toolhouse}</div>""", unsafe_allow_html=True)
                
                # Download button for complete analysis
                full_text = f"# Document Summary\n\n## AI Summary\n\n{st.session_state.summary}\n\n## Historical Context Analysis\n\n{st.session_state.summary_toolhouse}"
                st.download_button(
                    label="💾 Download Complete Summary",
                    data=full_text,
                    file_name="complete_document_summary.txt",
                    mime="text/plain"
                )
        
        # Download full report option
        with st.expander("Generate Full Report"):
            st.write("The full report combines the document summary with all page analyses.")
            
            all_analyses = "\n\n".join([f"## Page {r['page_num']}\n\n{r['analysis']}" for r in st.session_state.results])
            toolhouse_analyses = ""
            
            if any(r.get("toolhouse_result") for r in st.session_state.results) or st.session_state.summary_toolhouse:
                toolhouse_analyses += "\n\n# Historical Context Analyses\n\n"
                
                if st.session_state.summary_toolhouse:
                    toolhouse_analyses += f"## Document Summary Context\n\n{st.session_state.summary_toolhouse}\n\n"
                
                for r in st.session_state.results:
                    if r.get("toolhouse_result"):
                        toolhouse_analyses += f"## Page {r['page_num']} Context\n\n{r['toolhouse_result']}\n\n"
            
            full_report = f"# JFK Document Analysis Report\n\n## Document Summary\n\n{st.session_state.summary}\n\n# Page-by-Page Analysis\n\n{all_analyses}{toolhouse_analyses}"
            
            st.download_button(
                label="📑 Download Complete Report",
                data=full_report,
                file_name="jfk_complete_analysis_report.txt",
                mime="text/plain",
                use_container_width=True
            )

# Add footer with version info
st.markdown("---")
st.caption("JFK Files Analyzer v1.0 | Built with Streamlit, Google Gemini & Toolhouse")