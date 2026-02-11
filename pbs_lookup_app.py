import streamlit as st
import requests
import pandas as pd

# Set page config
st.set_page_config(
    page_title="PBS Item Lookup & Authority Application",
    page_icon="💊",
    layout="wide"
)

# Title
st.title("💊 PBS Item Lookup & Authority Application")

# Sidebar for hospital provider number
st.sidebar.header("Settings")
provider_number = st.sidebar.text_input(
    "Hospital Provider Number",
    value="000000",
    max_chars=6,
    help="Enter your 6-digit hospital provider number"
)

# Main search interface
st.header("Search PBS Items")

# Create tabs for different search methods
tab1, tab2 = st.tabs(["Search by Item Code", "Search by Drug Name"])

# API base URL
API_BASE = "https://api.pbs.gov.au/v1"

def get_item_by_code(item_code):
    """Fetch PBS item by code"""
    try:
        url = f"{API_BASE}/items/{item_code}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def search_items(drug_name=None):
    """Search PBS items by drug name"""
    try:
        url = f"{API_BASE}/items"
        params = {}
        if drug_name:
            params['name'] = drug_name
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error searching: {str(e)}")
        return None

def format_authority_application(item_code, restrictions, provider_num):
    """Format the authority application text"""
    application = f"""Hospital Provider Number [{provider_num}]
{item_code}
{restrictions}"""
    return application

def display_item_details(item_data):
    """Display PBS item details in a formatted way"""
    if not item_data:
        st.warning("No item data available")
        return
    
    # Extract relevant information
    item_code = item_data.get('code', 'N/A')
    
    # Get drug name - check multiple possible fields
    drug_name = (item_data.get('drug_name') or 
                 item_data.get('name') or 
                 item_data.get('li_drug_name') or
                 'N/A')
    
    # Get restrictions
    restrictions = item_data.get('restriction_text', 'None')
    if restrictions == 'None' or not restrictions:
        restrictions_list = item_data.get('restrictions', [])
        if restrictions_list:
            restrictions = '\n'.join([r.get('text', '') for r in restrictions_list if r.get('text')])
        if not restrictions:
            restrictions = 'No restrictions'
    
    # Determine authority type
    authority_required = item_data.get('authority_required', False)
    streamlined = item_data.get('streamlined_authority', False)
    
    if authority_required:
        if streamlined:
            authority_type = "Streamlined Authority"
        else:
            authority_type = "Phone Authority"
    else:
        authority_type = "No authority required"
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Item Details")
        st.write(f"**Item Code:** {item_code}")
        st.write(f"**Drug Name:** {drug_name}")
        st.write(f"**Authority Type:** {authority_type}")
    
    with col2:
        st.subheader("Restrictions")
        st.text_area("", value=restrictions, height=150, disabled=True, key=f"restrictions_{item_code}")
    
    # If authority required, show formatted application
    if authority_required:
        st.divider()
        st.subheader("Authority Application")
        
        application_text = format_authority_application(item_code, restrictions, provider_number)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area(
                "Copy the text below for your authority application:",
                value=application_text,
                height=200,
                key=f"app_{item_code}"
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("📋 Copy to Clipboard", key=f"copy_{item_code}"):
                st.code(application_text, language=None)
                st.success("Text ready to copy above!")

# Tab 1: Search by Item Code
with tab1:
    item_code_input = st.text_input(
        "Enter PBS Item Code",
        placeholder="e.g., 12345A",
        help="Enter the PBS item code"
    )
    
    if st.button("Search by Code", type="primary"):
        if item_code_input:
            with st.spinner("Fetching item details..."):
                item_data = get_item_by_code(item_code_input)
                if item_data:
                    display_item_details(item_data)
                else:
                    st.error(f"Item code '{item_code_input}' not found. Please check the code and try again.")
        else:
            st.warning("Please enter an item code")

# Tab 2: Search by Drug Name
with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        drug_name_input = st.text_input(
            "Enter Drug Name",
            placeholder="e.g., paracetamol",
            help="Enter the drug name to search"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("Search by Name", type="primary")
    
    if search_button:
        if drug_name_input:
            with st.spinner("Searching PBS database..."):
                results = search_items(drug_name=drug_name_input)
                
                if results and 'items' in results:
                    items = results['items']
                    
                    if len(items) > 0:
                        st.success(f"Found {len(items)} item(s)")
                        
                        # Show selection dropdown
                        if len(items) > 1:
                            item_options = {
                                f"{item.get('code', 'N/A')} - {item.get('drug_name') or item.get('name') or item.get('li_drug_name', 'Unknown')}": item 
                                for item in items
                            }
                            
                            selected_item_key = st.selectbox(
                                "Select an item to view details:",
                                options=list(item_options.keys())
                            )
                            
                            if selected_item_key:
                                selected_item = item_options[selected_item_key]
                                st.divider()
                                display_item_details(selected_item)
                        else:
                            # Only one result, display it
                            display_item_details(items[0])
                    else:
                        st.warning(f"No items found for '{drug_name_input}'")
                else:
                    st.error("No results found. Please try a different search term.")
        else:
            st.warning("Please enter a drug name")

# Footer
st.divider()
st.caption("Data sourced from PBS Public Data API | For healthcare professional use")
