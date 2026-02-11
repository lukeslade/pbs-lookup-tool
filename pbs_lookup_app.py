import streamlit as st
import requests
import pandas as pd
import re

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

# API Configuration
st.sidebar.header("API Configuration")
api_base = st.sidebar.text_input(
    "PBS API Base URL",
    value="https://data-api.health.gov.au/pbs/api/v3",
    help="The base URL for the PBS API"
)

subscription_key = st.sidebar.text_input(
    "Subscription Key (Optional)",
    value="2384af7c667342ceb5a736fe29f1dc6b",
    type="password",
    help="Optional subscription key for PBS API. Leave blank to try public access."
)

# Main search interface
st.header("Search PBS Items")

# Create tabs for different search methods
tab1, tab2 = st.tabs(["Search by Item Code", "Search by Drug Name"])

def get_headers():
    """Get API request headers"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if subscription_key:
        headers["Subscription-Key"] = subscription_key
    return headers

def get_restriction_texts(pbs_code, schedule_code):
    """Fetch all restriction texts for an item using item-restriction-relationships"""
    try:
        # First, get the restriction relationships for this item
        url = f"{api_base}/item-restriction-relationships"
        params = {
            'pbs_code': pbs_code,
            'schedule_code': schedule_code,
            'limit': 50
        }
        
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        # Extract data array
        if isinstance(data, dict) and 'data' in data:
            relationships = data['data']
        elif isinstance(data, list):
            relationships = data
        else:
            return []
        
        if not relationships:
            return []
        
        # Get all unique restriction codes
        restriction_codes = list(set([r.get('res_code') for r in relationships if r.get('res_code')]))
        
        if not restriction_codes:
            return []
        
        # Fetch all restrictions for this schedule in one call
        restrictions_url = f"{api_base}/restrictions"
        restrictions_params = {
            'schedule_code': schedule_code,
            'limit': 1000  # Get many at once to avoid rate limiting
        }
        
        restrictions_response = requests.get(restrictions_url, headers=get_headers(), params=restrictions_params, timeout=30)
        
        if restrictions_response.status_code == 200:
            restrictions_data = restrictions_response.json()
            
            if isinstance(restrictions_data, dict) and 'data' in restrictions_data:
                all_restrictions_list = restrictions_data['data']
            elif isinstance(restrictions_data, list):
                all_restrictions_list = restrictions_data
            else:
                return []
            
            # Filter to only the ones we need
            matching_restrictions = [r for r in all_restrictions_list if r.get('res_code') in restriction_codes]
            
            st.write(f"DEBUG: Total restrictions in schedule: {len(all_restrictions_list)}")
            st.write(f"DEBUG: Matching restrictions: {len(matching_restrictions)}")
            st.write(f"DEBUG: Looking for res_codes: {restriction_codes}")
            
            # Build list of restriction objects with formatted text
            restriction_list = []
            for restriction in matching_restrictions:
                res_code = restriction.get('res_code', '')
                
                # Get the text - li_html_text is the main field
                text = restriction.get('li_html_text') or restriction.get('schedule_html_text', '')
                
                if text:
                    # Remove HTML tags and format nicely
                    # First replace common HTML elements with newlines
                    text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                    text = text.replace('</p>', '\n\n').replace('<p>', '')
                    text = text.replace('</li>', '\n').replace('<li>', '• ')
                    text = text.replace('</div>', '\n').replace('<div>', '')
                    
                    # Remove remaining HTML tags
                    clean_text = re.sub('<[^<]+?>', '', text)
                    
                    # Clean up whitespace
                    clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text)  # Max 2 newlines
                    clean_text = re.sub(r' +', ' ', clean_text)  # Collapse multiple spaces
                    
                    # Decode HTML entities
                    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&')
                    clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>')
                    
                    clean_text = clean_text.strip()
                    
                    if clean_text:
                        treatment_phase = restriction.get('treatment_phase', '')
                        authority_method = restriction.get('authority_method', '')
                        
                        # Create a descriptive label for this restriction
                        label_parts = []
                        if treatment_phase:
                            label_parts.append(treatment_phase)
                        if authority_method:
                            label_parts.append(f"({authority_method})")
                        
                        label = " - ".join(label_parts) if label_parts else res_code
                        
                        restriction_list.append({
                            'res_code': res_code,
                            'label': label,
                            'text': clean_text,
                            'treatment_phase': treatment_phase,
                            'authority_method': authority_method
                        })
            
            return restriction_list
        
        return []
        
    except Exception as e:
        st.warning(f"Could not fetch restriction details: {str(e)}")
        return []

def get_item_by_code(item_code):
    """Fetch PBS item by code - returns (item_data, schedule_code) tuple"""
    try:
        # First get the latest schedule
        schedule_url = f"{api_base}/schedules"
        schedule_response = requests.get(schedule_url, headers=get_headers(), timeout=30)
        
        if schedule_response.status_code != 200:
            st.error(f"Failed to get schedule info. Status: {schedule_response.status_code}")
            return None, None
        
        schedules_resp = schedule_response.json()
        
        # Extract the data array
        if isinstance(schedules_resp, dict) and 'data' in schedules_resp:
            schedules = schedules_resp['data']
        else:
            st.error("Unexpected schedule response structure")
            return None, None
            
        if not schedules:
            st.error("No schedules available")
            return None, None
        
        # Get the latest schedule code
        latest_schedule = sorted(schedules, key=lambda x: x.get('schedule_code', 0), reverse=True)[0]
        schedule_code = latest_schedule.get('schedule_code')
        
        st.info(f"Using schedule: {schedule_code} (Effective: {latest_schedule.get('effective_date')})")
        
        # Now search for the item
        url = f"{api_base}/items"
        params = {
            'pbs_code': item_code.upper(),
            'schedule_code': schedule_code,
            'limit': 100
        }
        
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        
        if response.status_code == 200:
            items_resp = response.json()
            
            # Extract items from data array
            if isinstance(items_resp, dict) and 'data' in items_resp:
                items = items_resp['data']
                
                if len(items) > 0:
                    # Filter to exact match on PBS code
                    exact_matches = [item for item in items if item.get('pbs_code', '').upper() == item_code.upper()]
                    if exact_matches:
                        return exact_matches[0], schedule_code
                    return items[0], schedule_code
                else:
                    st.warning(f"No items found with code {item_code}")
                    return None, None
            else:
                st.error("Unexpected items response structure")
                return None, None
        else:
            st.error(f"API Error (Status {response.status_code})")
            return None, None
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None, None

def search_items(drug_name=None):
    """Search PBS items by drug name"""
    try:
        # First get the latest schedule
        schedule_url = f"{api_base}/schedules"
        schedule_response = requests.get(schedule_url, headers=get_headers(), timeout=30)
        
        if schedule_response.status_code != 200:
            st.error("Failed to get schedule info")
            return None
        
        schedules_resp = schedule_response.json()
        
        if isinstance(schedules_resp, dict) and 'data' in schedules_resp:
            schedules = schedules_resp['data']
        else:
            return None
            
        if not schedules:
            return None
        
        latest_schedule = sorted(schedules, key=lambda x: x.get('schedule_code', 0), reverse=True)[0]
        schedule_code = latest_schedule.get('schedule_code')
        
        st.info(f"Using schedule: {schedule_code} (Effective: {latest_schedule.get('effective_date')})")
        
        url = f"{api_base}/items"
        params = {
            'schedule_code': schedule_code,
            'limit': 200
        }
        
        if drug_name:
            params['filter'] = f"li_drug_name:like:{drug_name}"
        
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        
        if response.status_code == 200:
            items_resp = response.json()
            
            if isinstance(items_resp, dict) and 'data' in items_resp:
                items = items_resp['data']
                
                # Filter by drug name if API filter didn't work
                if drug_name:
                    filtered = []
                    for item in items:
                        item_drug = (item.get('li_drug_name', '') or 
                                   item.get('drug_name', '') or '').lower()
                        if drug_name.lower() in item_drug:
                            filtered.append(item)
                    return {'items': filtered if filtered else items, 'schedule_code': schedule_code}
                return {'items': items, 'schedule_code': schedule_code}
        
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

def display_item_details(item_data, schedule_code=None):
    """Display PBS item details in a formatted way"""
    if not item_data:
        st.warning("No item data available")
        return
    
    # Extract relevant information
    item_code = (item_data.get('pbs_code') or 
                 item_data.get('code') or 
                 'N/A')
    
    drug_name = (item_data.get('li_drug_name') or
                 item_data.get('drug_name') or 
                 'N/A')
    
    # Get restrictions using the PBS code and schedule
    restriction_list = []
    selected_restriction_text = "No restrictions"
    
    if item_code != 'N/A' and schedule_code:
        with st.spinner("Fetching restriction details..."):
            restriction_list = get_restriction_texts(item_code, schedule_code)
            st.write(f"DEBUG: Found {len(restriction_list)} restrictions")
            for r in restriction_list:
                st.write(f"DEBUG: Restriction - {r['label']}")
    
    # Determine authority type
    benefit_type_code = item_data.get('benefit_type_code', '')
    
    if benefit_type_code == 'A':
        authority_type = "Phone Authority"
    elif benefit_type_code == 'S':
        authority_type = "Streamlined Authority"
    elif benefit_type_code == 'U':
        authority_type = "No authority required (Unrestricted)"
    else:
        authority_type = "Check PBS website for authority requirements"
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Item Details")
        st.write(f"**Item Code:** {item_code}")
        st.write(f"**Drug Name:** {drug_name}")
        st.write(f"**Authority Type:** {authority_type}")
    
    with col2:
        st.subheader("Additional Details")
        st.write(f"**Program:** {item_data.get('program_code', 'N/A')}")
        st.write(f"**Benefit Type:** {benefit_type_code or 'N/A'}")
        
        with st.expander("View all item data"):
            st.json(item_data)
    
    # Show restrictions with dropdown if multiple exist
    if restriction_list and len(restriction_list) > 0:
        st.divider()
        st.subheader("Restrictions")
        
        if len(restriction_list) > 1:
            # Create dropdown for multiple restrictions
            restriction_options = {r['label']: r for r in restriction_list}
            
            selected_label = st.selectbox(
                "Select restriction criteria:",
                options=list(restriction_options.keys()),
                key=f"restriction_select_{item_code}"
            )
            
            selected_restriction = restriction_options[selected_label]
            selected_restriction_text = selected_restriction['text']
            
        else:
            # Only one restriction
            selected_restriction_text = restriction_list[0]['text']
        
        st.text_area("", value=selected_restriction_text, height=400, disabled=True, key=f"restrictions_{item_code}")
    
    # If authority required, show formatted application
    if benefit_type_code in ['A', 'S']:
        st.divider()
        st.subheader("Authority Application")
        
        application_text = format_authority_application(item_code, selected_restriction_text, provider_number)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area(
                "Copy the text below for your authority application:",
                value=application_text,
                height=300,
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
        placeholder="e.g., 12119W",
        help="Enter the PBS item code"
    )
    
    if st.button("Search by Code", type="primary"):
        if item_code_input:
            with st.spinner("Fetching item details..."):
                result = get_item_by_code(item_code_input)
                if result and result[0]:
                    item_data, schedule_code = result
                    display_item_details(item_data, schedule_code)
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
                    schedule_code = results.get('schedule_code')
                    
                    if len(items) > 0:
                        st.success(f"Found {len(items)} item(s)")
                        
                        if len(items) > 1:
                            item_options = {}
                            for item in items:
                                pbs_code = (item.get('pbs_code') or 'N/A')
                                drug = (item.get('li_drug_name') or item.get('drug_name') or 'Unknown')
                                program = item.get('program_code', '')
                                key = f"{pbs_code} - {drug} [{program}]"
                                item_options[key] = item
                            
                            selected_item_key = st.selectbox(
                                "Select an item to view details:",
                                options=list(item_options.keys())
                            )
                            
                            if selected_item_key:
                                selected_item = item_options[selected_item_key]
                                st.divider()
                                display_item_details(selected_item, schedule_code)
                        else:
                            display_item_details(items[0], schedule_code)
                    else:
                        st.warning(f"No items found for '{drug_name_input}'")
                else:
                    st.error("No results found. Please try a different search term.")
        else:
            st.warning("Please enter a drug name")

# Footer
st.divider()
st.caption("Data sourced from PBS Public Data API | For healthcare professional use")

with st.sidebar:
    st.divider()
    st.subheader("ℹ️ API Information")
    st.info("""
    **Note:** The PBS Public API requires a subscription key.
    
    Get your key at:
    [PBS Developer Portal](https://data-api-portal.health.gov.au/)
    """)
    
    st.markdown("""
    **Useful Links:**
    - [PBS Website](https://www.pbs.gov.au/)
    - [PBS Data Documentation](https://data.pbs.gov.au/)
    """)
