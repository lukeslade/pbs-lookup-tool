import streamlit as st
import re

# Set page config
st.set_page_config(
    page_title="PBS Authority Application Tool",
    page_icon="💊",
    layout="wide"
)

st.title("💊 PBS Authority Application Tool")

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_item_code' not in st.session_state:
    st.session_state.selected_item_code = ""

st.info("""
**Quick Workflow:**
1. Search by medication name OR enter item code directly
2. Select the right indication and strength
3. Paste the restriction criteria from PBS website
4. Get your formatted authority application
""")

# Sidebar
st.sidebar.header("Settings")
provider_number = st.sidebar.text_input(
    "Hospital Provider Number",
    value="000000",
    max_chars=6,
    help="Enter your 6-digit hospital provider number"
)

st.sidebar.divider()
st.sidebar.subheader("How to use")
st.sidebar.markdown("""
1. Go to [pbs.gov.au](https://www.pbs.gov.au/)
2. Search for your medication
3. Click on the item code
4. Click the red "Authority Required" section
5. Copy the restriction criteria
6. Paste it below
""")

# Main search section
st.subheader("Step 1: Find Your Item Code")

tab1, tab2 = st.tabs(["🔍 Search by Medication Name", "⌨️ Enter Item Code Directly"])

with tab1:
    st.markdown("Search for a medication to see all PBS item codes with their indications and strengths")
    
    medication_search = st.text_input(
        "Medication name:",
        placeholder="e.g., lenalidomide, pembrolizumab, bendamustine",
        key="med_search"
    )
    
    if st.button("Search PBS", type="primary") and medication_search:
        with st.spinner("Searching PBS database..."):
            # Use the PBS API to search
            try:
                import requests
                api_base = "https://data-api.health.gov.au/pbs/api/v3"
                subscription_key = "2384af7c667342ceb5a736fe29f1dc6b"
                
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Subscription-Key": subscription_key
                }
                
                # Get latest schedule
                schedule_response = requests.get(f"{api_base}/schedules", headers=headers, timeout=30)
                
                if schedule_response.status_code == 200:
                    schedules_data = schedule_response.json()
                    if isinstance(schedules_data, dict) and 'data' in schedules_data:
                        schedules = schedules_data['data']
                        latest_schedule = sorted(schedules, key=lambda x: x.get('schedule_code', 0), reverse=True)[0]
                        schedule_code = latest_schedule.get('schedule_code')
                        
                        # Search items
                        items_url = f"{api_base}/items"
                        params = {
                            'schedule_code': schedule_code,
                            'limit': 500
                        }
                        
                        items_response = requests.get(items_url, headers=headers, params=params, timeout=30)
                        
                        if items_response.status_code == 200:
                            items_data = items_response.json()
                            if isinstance(items_data, dict) and 'data' in items_data:
                                all_items = items_data['data']
                                
                                # Filter by medication name
                                matching_items = []
                                for item in all_items:
                                    drug_name = (item.get('li_drug_name', '') or item.get('drug_name', '') or '').lower()
                                    if medication_search.lower() in drug_name:
                                        matching_items.append(item)
                                
                                if matching_items:
                                    st.session_state.search_results = matching_items
                                    st.success(f"Found {len(matching_items)} item code(s) for {medication_search}")
                                else:
                                    st.warning(f"No items found for '{medication_search}'. Try a different spelling or use generic name.")
                        else:
                            st.error("Could not fetch items from PBS API")
                else:
                    st.error("Could not connect to PBS API")
            except Exception as e:
                st.error(f"Error searching: {str(e)}")
    
    # Display search results
    if st.session_state.search_results:
        st.divider()
        st.subheader("Select Item Code")
        
        # Create a nice table/list of results
        for item in st.session_state.search_results:
            pbs_code = item.get('pbs_code', 'N/A')
            drug_name = item.get('li_drug_name', 'Unknown')
            program = item.get('program_code', '')
            benefit_type = item.get('benefit_type_code', '')
            
            # Create a readable label
            auth_type = ""
            if benefit_type == 'S':
                auth_type = "🟡 Streamlined"
            elif benefit_type == 'A':
                auth_type = "🔴 Phone Authority"
            elif benefit_type == 'U':
                auth_type = "🟢 Unrestricted"
            
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button(f"Select {pbs_code}", key=f"select_{pbs_code}"):
                    st.session_state.selected_item_code = pbs_code
                    st.rerun()
            
            with col2:
                st.write(f"**{drug_name}** - {program}")
            
            with col3:
                st.write(auth_type)

with tab2:
    st.markdown("If you already know the PBS item code, enter it directly:")
    
    manual_code = st.text_input(
        "PBS Item Code:",
        placeholder="e.g., 12119W, 10763L, 5650K",
        key="manual_code"
    )
    
    if manual_code:
        st.session_state.selected_item_code = manual_code.upper()

# Show selected item code
item_code = st.session_state.selected_item_code

if item_code:
    st.divider()
    st.success(f"✓ Selected Item Code: **{item_code}**")
    
    pbs_url = f"https://www.pbs.gov.au/medicine/item/{item_code}"
    st.markdown(f"**[📋 Click here to open PBS page for {item_code}]({pbs_url})** ← Open this, click the red Authority button, and copy the criteria")
    
    # Old main form content continues here...
    st.divider()
    
    # Restriction criteria input
    st.subheader("Step 2: Paste Restriction Criteria")
    
    st.markdown("""
    **Instructions:** 
    1. Visit the PBS page (link above)
    2. Click the red "Authority Required" button to expand
    3. Copy ALL the text including treatment phase and clinical criteria
    4. Paste it below
    """)
    
    restriction_text = st.text_area(
        "Paste restriction criteria here:",
        height=300,
        placeholder="""Example:
Treatment Phase: Initial treatment - 6 weekly treatment regimen

Clinical criteria:
• Patient must not have previously been treated for this condition in the metastatic setting
• Patient must have a WHO performance status of 0 or 1
• The treatment must not exceed a total of 4 doses under this restriction""",
        key="restriction_input"
    )
    
    # Generate application
    if restriction_text:
        st.divider()
        st.subheader("Step 3: ✅ Your Authority Application")
        
        # Format the application
        application_text = f"""Hospital Provider Number [{provider_number}]
{item_code}
{restriction_text}"""
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text_area(
                "Formatted authority application:",
                value=application_text,
                height=400,
                help="Copy this text for your authority application"
            )
        
        with col2:
            st.write("")
            st.write("")
            
            if st.button("📋 Show Copyable", type="primary"):
                st.code(application_text, language=None)
                st.success("✓ Ready to copy")
            
            st.download_button(
                label="💾 Download",
                data=application_text,
                file_name=f"authority_{item_code}.txt",
                mime="text/plain"
            )
            
            if st.button("🔄 New Search"):
                st.session_state.search_results = []
                st.session_state.selected_item_code = ""
                st.rerun()
else:
    st.info("👆 Search for a medication or enter an item code to get started")
# Footer
st.divider()
st.caption("""
**For healthcare professional use only** | Data from PBS website (pbs.gov.au)  
This tool formats authority applications - it does not submit them. Always verify criteria on the official PBS website.
""")

# Tips in sidebar
with st.sidebar:
    st.divider()
    st.subheader("💡 Tips")
    st.markdown("""
    - **Streamlined authority:** Can usually be processed immediately
    - **Phone authority:** Requires calling 1800 888 333
    - **Hospital provider number:** This is your facility's number, not your prescriber number
    - **Save time:** Bookmark common item codes
    """)
    
    with st.expander("Example Item Codes"):
        st.code("""
Pembrolizumab:
• 12119W - NSCLC
• 11198E - Melanoma
• 11876G - Head/neck cancer

Nivolumab:
• 11072K - NSCLC  
• 11036W - Melanoma

Bendamustine:
• 10763L - CLL/NHL

Rituximab:
• 5706G - NHL
• 5646F - CLL
        """)
