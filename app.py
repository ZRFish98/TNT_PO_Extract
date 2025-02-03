import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO

def extract_po_data(pdf_file):
    data = []
    current_po = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            for line in lines:
                # Extract PO Number
                if po_match := re.search(r'PO No\.:\s*(\d+)', line):
                    current_po['PO No.'] = po_match.group(1)
                
                # Extract Store Name
                if store_match := re.search(r'Store :\s*(.*?)(?=\s*-|\s+GROCERY|$)', line):
                    current_po['Store Name'] = store_match.group(1).strip()
                
                # Extract Order Date
                if order_date_match := re.search(r'Order Date :\s*(\d{2}/\d{2}/\d{4})', line):
                    current_po['Order Date'] = order_date_match.group(1)
                
                # Extract Delivery Date
                if delivery_date_match := re.search(r'Delivery Date \(on or before\) :\s*(\d{2}/\d{2}/\d{4})', line):
                    current_po['Delivery Date'] = delivery_date_match.group(1)
                
                # Detect item table start (look for "Item#" header)
                if re.match(r'Item#', line):
                    in_item_section = True
                    continue
                
                # Parse item lines (lines starting with a 6-digit number)
                if 'PO No.' in current_po and re.match(r'^\d{6}\b', line.strip()):
                    parts = line.strip().split()
                    item = {
                        'Item#': parts[0],
                        'Ordered Qty': None,
                        'Price': None
                    }
                    
                    # Extract numeric values
                    numeric_values = [
                        part for part in parts 
                        if re.match(r'^\d+\.\d{2}$', part)
                    ]
                    
                    if len(numeric_values) >= 3:
                        item['Ordered Qty'] = float(numeric_values[-3])
                        item['Price'] = float(numeric_values[-2])
                    
                    data.append({
                        'PO No.': current_po['PO No.'],
                        'Store Name': current_po.get('Store Name', ''),
                        'Order Date': current_po.get('Order Date', ''),
                        'Delivery Date': current_po.get('Delivery Date', ''),
                        **item
                    })
    
    return data

# Streamlit UI
st.title("T&T Purchase Order Extractor 🛒")
uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        data = extract_po_data(BytesIO(uploaded_file.getvalue()))
        all_data.extend(data)
    
    df = pd.DataFrame(all_data)
    
    # Show preview
    st.write("Preview of Extracted Data:")
    st.dataframe(df.head())
    
    # Download Excel
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.download_button(
        label="Download Excel Sheet",
        data=excel_buffer.getvalue(),
        file_name="purchase_orders.xlsx",
        mime="application/vnd.ms-excel"
    )