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

# API Configuration
st.sidebar.header("API Configuration")
api_base = st.sidebar.text_input(
    "PBS API Base URL",
    value="https://data-api.health.gov.au/pbs/api/v3",
    help="The base URL for the PBS API"
)

subscription_key = st.sidebar.text_input(
    "Subscription Key (Optional)",
    value="",
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
        headers["Subscription-Key"] = subscription_key  # Note: Capital S and K
    return headers

def get_restriction_text(restriction_code, schedule_code):
    """Fetch restriction text from the restrictions endpoint"""
    try:
        url = f"{api_base}/restrictions"
        params = {
            'res_code': restriction_code,
            'schedule_code': schedule_code,
            'limit': 10
        }
        
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                # Get the restriction text
                restriction = data[0]
                
                # Try to get prescribing text if available
                prescribing_txt_id = restriction.get('prescribing_txt_id')
                if prescribing_txt_id:
                    prescribing_url = f"{api_base}/prescribing-texts"
                    prescribing_params = {
                        'prescribing_txt_id': prescribing_txt_id,
                        'schedule_code': schedule_code
                    }
                    prescribing_response = requests.get(prescribing_url, headers=get_headers(), params=prescribing_params, timeout=30)
                    
                    if prescribing_response.status_code == 200:
                        prescribing_data = prescribing_response.json()
                        if isinstance(prescribing_data, list) and len(prescribing_data) > 0:
                            return prescribing_data[0].get('prescribing_txt', 'No restriction text available')
                
                # If no prescribing text, return what we can from the restriction
                return restriction.get('restriction_text', 'No restriction text available')
            return None
        return None
    except Exception as e:
        st.warning(f"Could not fetch restriction details: {str(e)}")
        return None

def get_item_by_code(item_code):
    """Fetch PBS item by code - returns (item_data, schedule_code) tuple"""
    try:
        # First get the latest schedule
        schedule_url = f"{api_base}/schedules"
        schedule_response = requests.get(schedule_url, headers=get_headers(), timeout=30)
        
        if schedule_response.status_code != 200:
            st.error(f"Failed to get schedule info. Status: {schedule_response.status_code}")
            st.error(f"Response: {schedule_response.text[:500]}")
            return None, None
        
        try:
            schedules_resp = schedule_response.json()
        except Exception as e:
            st.error(f"Could not parse schedule response as JSON: {str(e)}")
            return None, None
        
        # Extract the data array from the response
        if isinstance(schedules_resp, dict) and 'data' in schedules_resp:
            schedules = schedules_resp['data']
        else:
            st.error(f"Unexpected schedule response structure")
            return None, None
            
        if not schedules or len(schedules) == 0:
            st.error("No schedules available")
            return None, None
        
        # Get the latest schedule code (highest schedule_code number)
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
            try:
                items_resp = response.json()
            except:
                st.error(f"Could not parse items response as JSON: {response.text[:500]}")
                return None, None
            
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
                st.error(f"Unexpected items response structure")
                return None, None
        else:
            st.error(f"API Error (Status {response.status_code})")
            st.error(f"Response: {response.text[:500]}")
            return None, None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The PBS API may be slow or unavailable.")
        return None, None
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None

def search_items(drug_name=None):
    """Search PBS items by drug name"""
    try:
        # First get the latest schedule
        schedule_url = f"{api_base}/schedules"
        schedule_response = requests.get(schedule_url, headers=get_headers(), timeout=30)
        
        if schedule_response.status_code != 200:
            st.error(f"Failed to get schedule info. Status: {schedule_response.status_code}")
            return None
        
        try:
            schedules_resp = schedule_response.json()
        except:
            st.error(f"Could not parse schedule response as JSON")
            return None
        
        # Extract the data array from the response
        if isinstance(schedules_resp, dict) and 'data' in schedules_resp:
            schedules = schedules_resp['data']
        else:
            st.error(f"Unexpected schedule response structure")
            return None
            
        if not schedules or len(schedules) == 0:
            st.error("No schedules available")
            return None
        
        # Get the latest schedule code
        latest_schedule = sorted(schedules, key=lambda x: x.get('schedule_code', 0), reverse=True)[0]
        schedule_code = latest_schedule.get('schedule_code')
        
        st.info(f"Using schedule: {schedule_code} (Effective: {latest_schedule.get('effective_date')})")
        
        url = f"{api_base}/items"
        params = {
            'schedule_code': schedule_code,
            'limit': 200
        }
        
        # Try searching with drug name filter
        if drug_name:
            params['filter'] = f"li_drug_name:like:{drug_name}"
        
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        
        if response.status_code == 200:
            try:
                items_resp = response.json()
            except:
                st.error(f"Could not parse response as JSON")
                return None
            
            # Extract items from data array
            if isinstance(items_resp, dict) and 'data' in items_resp:
                items = items_resp['data']
                
                # Filter by drug name in results if the API filter didn't work
                if drug_name:
                    filtered = []
                    for item in items:
                        item_drug = (item.get('li_drug_name', '') or 
                                   item.get('drug_name', '') or 
                                   item.get('name', '') or '').lower()
                        if drug_name.lower() in item_drug:
                            filtered.append(item)
                    return {'items': filtered if filtered else items, 'schedule_code': schedule_code}
                return {'items': items, 'schedule_code': schedule_code}
            else:
                st.error(f"Unexpected items response structure")
                return None
        else:
            st.error(f"API Error (Status {response.status_code})")
            st.error(f"Response: {response.text[:500]}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The PBS API may be slow or unavailable.")
        return None
    except Exception as e:
        st.error(f"Error searching: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
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
    
    # Extract relevant information - PBS API v3 field names
    item_code = (item_data.get('pbs_code') or 
                 item_data.get('code') or 
                 item_data.get('item_code') or
                 'N/A')
    
    # Get drug name - check multiple possible fields
    drug_name = (item_data.get('li_drug_name') or
                 item_data.get('drug_name') or 
                 item_data.get('name') or 
                 item_data.get('li_item_id') or
                 'N/A')
    
    # Get restriction code and fetch actual text
    restriction_code = item_data.get('restriction_code')
    restrictions = "No restrictions"
    
    if restriction_code and schedule_code:
        with st.spinner("Fetching restriction details..."):
            restriction_text = get_restriction_text(restriction_code, schedule_code)
            if restriction_text:
                restrictions = restriction_text
            else:
                restrictions = f"Restriction Code: {restriction_code}\nSee PBS website for full details"
    elif restriction_code:
        restrictions = f"Restriction Code: {restriction_code}\nSee PBS website for full details"
    
    # Determine authority type based on PBS API fields
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
        if restriction_code:
            st.write(f"**Restriction Code:** {restriction_code}")
    
    with col2:
        st.subheader("Additional Details")
        st.write(f"**Program:** {item_data.get('program_code', 'N/A')}")
        st.write(f"**Benefit Type:** {benefit_type_code or 'N/A'}")
        
        # Show raw data for debugging
        with st.expander("View all item data"):
            st.json(item_data)
    
    # Show restrictions
    if restrictions and restrictions != "No restrictions":
        st.divider()
        st.subheader("Restrictions")
        st.text_area("", value=restrictions, height=300, disabled=True, key=f"restrictions_{item_code}")
    
    # If authority required, show formatted application
    if benefit_type_code in ['A', 'S']:
        st.divider()
        st.subheader("Authority Application")
        
        application_text = format_authority_application(item_code, restrictions, provider_number)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area(
                "Copy the text below for your authority application:",
                value=application_text,
                height=250,
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
                result = get_item_by_code(item_code_input)
                if result and result[0]:  # Check if we got a valid tuple
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
                        
                        # Show selection dropdown
                        if len(items) > 1:
                            item_options = {}
                            for item in items:
                                pbs_code = (item.get('pbs_code') or item.get('code') or 'N/A')
                                drug = (item.get('li_drug_name') or item.get('drug_name') or item.get('name') or 'Unknown')
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
                            # Only one result, display it
                            display_item_details(items[0], schedule_code)
                    else:
                        st.warning(f"No items found for '{drug_name_input}'")
                else:
                    st.error("No results found. Please try a different search term.")
        else:
            st.warning("Please enter a drug name")

# Footer and API Information
st.divider()
st.caption("Data sourced from PBS Public Data API | For healthcare professional use")

# Add API connection status indicator in sidebar
with st.sidebar:
    st.divider()
    st.subheader("ℹ️ API Information")
    st.info("""
    **Note:** The PBS Public API may require:
    - A subscription key (get from PBS Developer Portal)
    - Access through the Postman collection
    
    If searches return no results, try:
    1. Adding a subscription key in settings above
    2. Checking the PBS website directly
    3. Using exact PBS item codes
    """)
    
    st.markdown("""
    **Useful Links:**
    - [PBS Website](https://www.pbs.gov.au/)
    - [PBS Developer Portal](https://data-api-portal.health.gov.au/)
    - [PBS Data Documentation](https://data.pbs.gov.au/)
    """)
