import pdfplumber
import re
import pandas as pd

def extract_po_data(pdf_path):
    data = []
    current_po = {}
    
    with pdfplumber.open(pdf_path) as pdf:
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
                            'Store Name': current_po.get('Store Name', ''),
                            'Store ID': current_po.get('Store ID', ''),
                            'Order Date': current_po.get('Order Date', ''),
                            'Delivery Date': current_po.get('Delivery Date', ''),
                            'Item#': parts[0],
                            'Ordered Qty': ordered_qty,
                            'Price': price
                        })
    
    return data

# Process all PDFs
all_data = []
pdf_files = [
    'ATiara Mail Document (37).PDF',
    'ATiara Mail Document (38).PDF',
    'ATiara Mail Document (39).PDF',
    'ATiara Mail Document (40).PDF'
]

for pdf_file in pdf_files:
    all_data.extend(extract_po_data(pdf_file))

# Create DataFrame and sort
df = pd.DataFrame(all_data)
df['Store ID'] = df['Store ID'].astype(int)  # Convert to integer for proper sorting
df['PO No.'] = df['PO No.'].astype(int)
df = df.sort_values(by=['Store ID', 'PO No.'], ascending=[True, True])

# Save to CSV
df.to_csv('sorted_purchase_orders.csv', index=False)
print("Sorted CSV generated: sorted_purchase_orders.csv")
