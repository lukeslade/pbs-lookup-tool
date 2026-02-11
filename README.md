# PBS Item Lookup & Authority Application Tool

A Streamlit web application for looking up PBS (Pharmaceutical Benefits Scheme) items and generating formatted authority applications.

## Features

- **Search by Item Code**: Direct lookup using PBS item codes
- **Search by Drug Name**: Search the PBS database by drug name with dropdown selection for multiple results
- **Item Details Display**: Shows item code, drug name, restrictions, and authority type
- **Authority Application Generator**: Automatically formats authority applications with:
  - Hospital provider number (editable in sidebar)
  - Item code
  - Restriction criteria
  - Copy-ready text output

## How to Use

1. **Set Your Provider Number**: Enter your 6-digit hospital provider number in the sidebar (defaults to 000000)

2. **Search for Items**:
   - **By Item Code**: Enter the PBS item code and click "Search by Code"
   - **By Drug Name**: Enter a drug name and click "Search by Name", then select from results if multiple items found

3. **View Details**: The app displays:
   - Item code
   - Drug name
   - Authority type (Streamlined Authority, Phone Authority, or No authority required)
   - Restriction text

4. **Copy Authority Application**: For items requiring authority:
   - View the formatted application text
   - Click "Copy to Clipboard" to prepare text for copying
   - Paste into your authority application system

## Technical Details

- Built with Streamlit
- Uses PBS Public Data API (https://api.pbs.gov.au)
- Requires Python 3.8+

## Deployment

This app is designed to be deployed on Streamlit Community Cloud.

## Data Source

All data is sourced from the official PBS Public Data API. For healthcare professional use only.
