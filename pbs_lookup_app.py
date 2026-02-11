import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# Set page config
st.set_page_config(
    page_title="PBS Authority Application Tool",
    page_icon="💊",
    layout="wide"
)

st.title("💊 PBS Authority Application Tool")

# Sidebar
st.sidebar.header("Settings")
provider_number = st.sidebar.text_input(
    "Hospital Provider Number",
    value="000000",
    max_chars=6,
    help="Enter your 6-digit hospital provider number"
)

subscription_key = "2384af7c667342ceb5a736fe29f1dc6b"

# Main interface
st.header("Search by Medication")

def scrape_pbs_item(item_code):
    """Scrape PBS website for item details and restrictions"""
    try:
        url = f"https://www.pbs.gov.au/medicine/item/{item_code}"
        
        st.write(f"DEBUG: Fetching from {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract drug name
        drug_name = None
        h1 = soup.find('h1')
        if h1:
            drug_name = h1.get_text(strip=True)
        
        # Find all restriction sections
        restrictions = []
        
        # Look for restriction content - PBS uses various div structures
        restriction_divs = soup.find_all(['div', 'section'], class_=re.compile('restriction|criteria|authority', re.I))
        
        if not restriction_divs:
            # Try finding by heading text
            headings = soup.find_all(['h2', 'h3', 'h4'], string=re.compile('restriction|criteria|authority', re.I))
            for heading in headings:
                # Get the content after the heading
                content = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        break
                    content.append(sibling.get_text(strip=True))
                if content:
                    restrictions.append({
                        'title': heading.get_text(strip=True),
                        'text': '\n'.join(content)
                    })
        else:
            for div in restriction_divs:
                text = div.get_text(separator='\n', strip=True)
                if len(text) > 50:  # Only keep substantial content
                    title = div.find(['h3', 'h4', 'strong'])
                    title_text = title.get_text(strip=True) if title else "Restriction"
                    restrictions.append({
                        'title': title_text,
                        'text': text
                    })
        
        # Try to get all text if no structured restrictions found
        if not restrictions:
            all_text = soup.get_text(separator='\n')
            st.write("DEBUG: Full page text (first 2000 chars):")
            st.code(all_text[:2000])
        
        return {
            'drug_name': drug_name,
            'restrictions': restrictions,
            'url': url
        }
        
    except Exception as e:
        st.error(f"Error scraping PBS website: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def format_authority_application(item_code, criteria, provider_num):
    """Format the authority application text"""
    return f"""Hospital Provider Number [{provider_num}]
{item_code}
{criteria}"""

# Search input
medication_name = st.text_input(
    "Enter medication name",
    placeholder="e.g., pembrolizumab, nivolumab, lenalidomide",
    help="Enter the medication name to search"
)

item_code_manual = st.text_input(
    "Or enter PBS item code directly",
    placeholder="e.g., 12119W",
    help="Enter PBS item code if you know it"
)

if st.button("Search", type="primary"):
    if item_code_manual:
        # Direct item code lookup
        with st.spinner(f"Fetching details for {item_code_manual}..."):
            result = scrape_pbs_item(item_code_manual)
            
            if result:
                st.success(f"Found: {result['drug_name'] or item_code_manual}")
                
                st.subheader("Item Details")
                st.write(f"**Item Code:** {item_code_manual}")
                st.write(f"**Drug Name:** {result['drug_name']}")
                st.write(f"**PBS Link:** [{result['url']}]({result['url']})")
                
                if result['restrictions']:
                    st.divider()
                    st.subheader("Restriction Criteria")
                    
                    if len(result['restrictions']) > 1:
                        # Multiple restrictions - show dropdown
                        restriction_options = {r['title']: r['text'] for r in result['restrictions']}
                        
                        selected_title = st.selectbox(
                            "Select indication/treatment phase:",
                            options=list(restriction_options.keys())
                        )
                        
                        selected_text = restriction_options[selected_title]
                    else:
                        # Single restriction
                        selected_text = result['restrictions'][0]['text']
                    
                    st.text_area(
                        "Restriction criteria:",
                        value=selected_text,
                        height=300,
                        disabled=True
                    )
                    
                    st.divider()
                    st.subheader("Authority Application")
                    
                    application_text = format_authority_application(
                        item_code_manual,
                        selected_text,
                        provider_number
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text_area(
                            "Copy the text below:",
                            value=application_text,
                            height=300
                        )
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("📋 Copy"):
                            st.code(application_text)
                            st.success("Text ready to copy!")
                else:
                    st.warning("No restriction criteria found on PBS website. The page may have a different structure.")
                    st.info(f"Please visit the PBS website directly: {result['url']}")
                    
                    # Provide manual entry option
                    manual_criteria = st.text_area(
                        "Paste criteria from PBS website:",
                        height=300,
                        placeholder="Copy and paste the restriction criteria here..."
                    )
                    
                    if manual_criteria:
                        st.divider()
                        st.subheader("Authority Application")
                        
                        application_text = format_authority_application(
                            item_code_manual,
                            manual_criteria,
                            provider_number
                        )
                        
                        st.text_area(
                            "Copy the text below:",
                            value=application_text,
                            height=300
                        )
            else:
                st.error(f"Could not fetch details for item {item_code_manual}")
                
    elif medication_name:
        st.info("Medication name search coming soon. For now, please use the PBS item code.")
        st.write("""
        To find your PBS item code:
        1. Go to [pbs.gov.au](https://www.pbs.gov.au/)
        2. Search for your medication
        3. Find the item code (e.g., 12119W)
        4. Enter it above
        """)
    else:
        st.warning("Please enter a medication name or PBS item code")

# Footer
st.divider()
st.caption("Data sourced from PBS website | For healthcare professional use")
