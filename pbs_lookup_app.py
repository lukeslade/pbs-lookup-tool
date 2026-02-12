import streamlit as st
import re

# Set page config
st.set_page_config(
    page_title="PBS Authority Application Tool",
    page_icon="💊",
    layout="wide"
)

st.title("💊 PBS Authority Application Tool")

st.info("""
**Quick Workflow:**
1. Enter the PBS item code (find it on pbs.gov.au)
2. Paste the restriction criteria from the PBS website
3. Get your formatted authority application
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

# Main form
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Item Code")
    item_code = st.text_input(
        "PBS Item Code",
        placeholder="e.g., 12119W, 10763L",
        help="The PBS item code for your medication",
        label_visibility="collapsed"
    )
    
    if item_code:
        pbs_url = f"https://www.pbs.gov.au/medicine/item/{item_code}"
        st.markdown(f"[📋 Open PBS page for {item_code}]({pbs_url})")

with col2:
    st.subheader("Common Medications Quick Links")
    
    common_meds = {
        "Pembrolizumab (Keytruda)": {
            "Initial NSCLC": "12119W",
            "Continuing NSCLC": "12119W",
            "Melanoma": "11198E",
        },
        "Nivolumab (Opdivo)": {
            "NSCLC": "11072K",
            "Melanoma": "11036W",
        },
        "Bendamustine": {
            "CLL/NHL": "10763L",
        },
        "Lenalidomide": {
            "Multiple Myeloma": "5650K",
        }
    }
    
    selected_med = st.selectbox(
        "Or select a common medication:",
        [""] + list(common_meds.keys()),
        label_visibility="collapsed"
    )
    
    if selected_med:
        indications = common_meds[selected_med]
        if len(indications) == 1:
            item_code = list(indications.values())[0]
            st.success(f"Item code: **{item_code}**")
        else:
            indication = st.selectbox(
                "Select indication:",
                list(indications.keys())
            )
            if indication:
                item_code = indications[indication]
                st.success(f"Item code: **{item_code}**")

st.divider()

# Restriction criteria input
st.subheader("Restriction Criteria")

st.markdown("""
**Instructions:** 
1. Visit the PBS page for your item code (link above)
2. Click the red "Authority Required (STREAMLINED)" or "Authority Required" button
3. Copy ALL the text from the expanded section including:
   - Treatment phase (if applicable)
   - Clinical criteria  
   - All bullet points and conditions
4. Paste it in the box below
""")

restriction_text = st.text_area(
    "Paste restriction criteria here:",
    height=300,
    placeholder="""Example:
Treatment Phase: Initial treatment - 6 weekly treatment regimen

Clinical criteria:
• Patient must not have previously been treated for this condition in the metastatic setting
• The condition must have progressed after treatment with only one of: (i) tepotinib, (ii) selpercatinib, (iii) dabrafenib in combination with trametinib
• Patient must not have received prior treatment with a programmed cell death-1 (PD-1) inhibitor
• Patient must have a WHO performance status of 0 or 1
• The condition must not have evidence of an activating epidermal growth factor receptor (EGFR) gene
• The treatment must not exceed a total of 4 doses under this restriction

Note: In the first few months after start of immunotherapy, some patients can have a transient tumour flare with subsequent disease response.""",
    key="restriction_input"
)

# Generate application
if item_code and restriction_text:
    st.divider()
    st.subheader("✅ Authority Application")
    
    # Format the application
    application_text = f"""Hospital Provider Number [{provider_number}]
{item_code}
{restriction_text}"""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.text_area(
            "Your formatted authority application:",
            value=application_text,
            height=400,
            help="Copy this text and paste it into your authority application system"
        )
    
    with col2:
        st.write("")
        st.write("")
        st.write("")
        
        # Copy button (visual only)
        if st.button("📋 Show Copyable", type="primary"):
            st.code(application_text, language=None)
            st.success("✓ Text displayed above - select all and copy")
        
        # Download option
        st.download_button(
            label="💾 Download",
            data=application_text,
            file_name=f"authority_{item_code}.txt",
            mime="text/plain"
        )
        
        # Clear button
        if st.button("🗑️ Clear"):
            st.rerun()

# Preview section
if item_code and restriction_text:
    with st.expander("📊 Preview Application Format"):
        st.markdown(f"""
        **Hospital Provider Number:** `{provider_number}`  
        **PBS Item Code:** `{item_code}`  
        **Criteria Length:** {len(restriction_text)} characters  
        **Lines:** {len(restriction_text.splitlines())} lines
        """)

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
