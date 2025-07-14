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
                
                # Extract Store Name and Store ID (e.g., "Store - 011")
                if store_match := re.search(r'Store :\s*(.*?)\s*-\s*(\d{3})\b', line):
                    current_po['Store Name'] = store_match.group(1).strip()
                    current_po['Store ID'] = store_match.group(2)
                
                # Extract Dates
                if order_date_match := re.search(r'Order Date :\s*(\d{2}/\d{2}/\d{4})', line):
                    current_po['Order Date'] = order_date_match.group(1)
                if delivery_date_match := re.search(r'Delivery Date \(on or before\) :\s*(\d{2}/\d{2}/\d{4})', line):
                    current_po['Delivery Date'] = delivery_date_match.group(1)
                
                # Parse item lines
                if 'PO No.' in current_po and re.match(r'^\d{6}\b', line.strip()):
                    parts = line.strip().split()
                    numeric_values = [part for part in parts if re.match(r'^\d+\.\d{2}$', part)]
                    
                    if len(numeric_values) >= 3:
                        ordered_qty = float(numeric_values[-3])
                        price = float(numeric_values[-2])
                        data.append({
                            'PO No.': current_po['PO No.'],
                            'Store ID': current_po.get('Store ID', ''),
                            'Store Name': current_po.get('Store Name', ''),
                            'Order Date': current_po.get('Order Date', ''),
                            'Delivery Date': current_po.get('Delivery Date', ''),
                            'Internal Reference': parts[0],
                            'Ordered Qty': ordered_qty,
                            'Price': price
                        })
    
    return data

# Streamlit UI
st.title("T&T Purchase Order Processor 🛒")
uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        data = extract_po_data(BytesIO(uploaded_file.getvalue()))
        all_data.extend(data)
    
    if all_data:
        # Create DataFrame and sort
        df = pd.DataFrame(all_data)
        
        # Convert to numeric for proper sorting
        df['Store ID'] = pd.to_numeric(df['Store ID'], errors='coerce')
        df['PO No.'] = pd.to_numeric(df['PO No.'], errors='coerce')
        
        # Sort by Store ID and PO No.
        df = df.sort_values(by=['Store ID', 'PO No.'], ascending=[True, True])
        
        # Reorder columns
        df = df[['Store ID', 'Store Name', 'PO No.', 'Order Date', 'Delivery Date',
                'Internal Reference', 'Ordered Qty', 'Price']]

        # Show preview
        st.write("Preview of Extracted Data:")
        st.dataframe(df.head())
        
        # Download Excel
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        st.download_button(
            label="Download Excel Sheet",
            data=excel_buffer.getvalue(),
            file_name="purchase_orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No valid purchase order data found in the uploaded files.")
else:
    st.info("Please upload PDF files to get started")
