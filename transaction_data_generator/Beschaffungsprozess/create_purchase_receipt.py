import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict, Tuple
from api.purchase_receipt_api import PurchaseReceiptAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    MASTER_DATA_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    LOG_DIR = os.path.join(BASE_DIR, 'logs', 'purchase_receipts')
    TARGET_WAREHOUSE = "Lager Stuttgart - B"
    RECEIPT_DELAY = (1, 14)  # Receipt 1-14 days after order


# Create logs directory if it doesn't exist
os.makedirs(Config.LOG_DIR, exist_ok=True)

# Configure file logger
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, f'purchase_receipt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
)
file_handler.setFormatter(logging.Formatter('%(message)s'))
file_logger.addHandler(file_handler)

# Configure console logger
console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
console_logger.addHandler(console_handler)

# Prevent loggers from propagating to root logger
file_logger.propagate = False
console_logger.propagate = False


def load_purchase_orders() -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, 'purchase_orders.csv'), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_item_batch_info() -> Dict[str, bool]:
    with open(os.path.join(Config.MASTER_DATA_DIR, 'items.csv'), 'r', encoding='utf-8') as f:
        items = list(csv.DictReader(f))
        return {item['Item Code']: item.get('Has Batch No', '0') == '1' for item in items}


def load_batch_numbers() -> Dict[str, str]:
    batch_numbers = {}
    with open(os.path.join(Config.MASTER_DATA_DIR, 'batch_numbers.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch_numbers[row['Item']] = row['Batch ID']
    return batch_numbers


def generate_purchase_receipts(purchase_orders: List[Dict], item_batch_info: Dict[str, bool],
                             batch_numbers: Dict[str, str]) -> List[Dict]:
    purchase_receipts = []
    for po in purchase_orders:
        po_date = datetime.strptime(po['Date'], "%Y-%m-%d")
        pr_date = po_date + timedelta(days=random.randint(*Config.RECEIPT_DELAY))
        item_code = po['Item Code (Items)']
        batch_no = batch_numbers.get(item_code, "") if item_batch_info.get(item_code, False) else ""

        receipt = {
            "doctype": "Purchase Receipt",
            "naming_series": "MAT-PRE-.YYYY.-",
            "company": po['Company'],
            "currency": po['Currency'],
            "posting_date": pr_date.strftime("%Y-%m-%d"),
            "posting_time": pr_date.strftime("%H:%M:%S.%f"),
            "conversion_rate": 1.0,
            "supplier": po['Supplier'],
            "items": [{
                "item_code": item_code,
                "item_name": po['Item Name (Items)'],
                "description": f"Receipt for {po['Item Name (Items)']}",
                "received_qty": float(po['Quantity (Items)']),
                "qty": float(po['Quantity (Items)']),
                "rate": float(po['Rate (Items)']),
                "amount": float(po['Amount (Items)']),
                "uom": po['UOM (Items)'],
                "stock_uom": po['Stock UOM (Items)'],
                "conversion_factor": 1.0,
                "batch_no": batch_no,
                "purchase_order": po['ID'],
                "purchase_order_item": po['ID (Items)'],
                "warehouse": Config.TARGET_WAREHOUSE
            }],
            "taxes": [{
                "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                "charge_type": "On Net Total",
                "description": "Abziehbare Vorsteuer 19 %",
                "rate": 19.0,
                "tax_amount": float(po['Total Taxes and Charges'].replace(',', '.')),
                "total": float(po['Grand Total'].replace(',', '.'))
            }],
            "status": "To Bill",
            "docstatus": 1
        }
        purchase_receipts.append(receipt)
    return purchase_receipts


def upload_purchase_receipt_to_api(purchase_receipt: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseReceiptAPI()
    try:
        response = api.create(purchase_receipt)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            console_logger.info(f"Successfully uploaded Purchase Receipt. ID: {system_id}")
            file_logger.info(f"Successfully created Purchase Receipt with ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        file_logger.error(f"Failed to upload Purchase Receipt: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        file_logger.warning("No data to save to CSV.")
        return

    flattened_data = []
    for pr in data:
        for item in pr['items']:
            row = {
                "ID": pr['name'],
                "Company": pr['company'],
                "Currency": pr['currency'],
                "Date": pr['posting_date'],
                "Exchange Rate": "1,00",
                "Net Total (Company Currency)": item['amount'],
                "Posting Time": pr['posting_time'],
                "Series": pr['naming_series'],
                "Status": pr['status'],
                "Supplier": pr['supplier'],
                "ID (Items)": item.get('name', ''),
                "Conversion Factor (Items)": item['conversion_factor'],
                "Item Code (Items)": item['item_code'],
                "Item Name (Items)": item['item_name'],
                "Rate (Company Currency) (Items)": item['rate'],
                "Received Quantity (Items)": item['received_qty'],
                "Stock UOM (Items)": item['stock_uom'],
                "UOM (Items)": item['uom'],
                "Purchase Order (Items)": item['purchase_order'],
                "Purchase Order Item (Items)": item['purchase_order_item'],
                "Accepted Warehouse (Items)": item['warehouse'],
                "Tax Rate (Purchase Taxes and Charges)": pr['taxes'][0]['rate'],
                "Account Head (Purchase Taxes and Charges)": pr['taxes'][0]['account_head'],
                "Accepted Quantity (Items)": item['qty'],
                "Description (Purchase Taxes and Charges)": pr['taxes'][0]['description'],
                "Type (Purchase Taxes and Charges)": pr['taxes'][0]['charge_type'],
                "Add or Deduct (Purchase Taxes and Charges)": "Add",
                "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
                "Batch No (Items)": item['batch_no']
            }
            flattened_data.append(row)

    fieldnames = flattened_data[0].keys()
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)


def main():
    purchase_orders = load_purchase_orders()
    item_batch_info = load_item_batch_info()
    batch_numbers = load_batch_numbers()
    purchase_receipts = generate_purchase_receipts(purchase_orders, item_batch_info, batch_numbers)

    successful_uploads = []
    for pr in purchase_receipts:
        success, system_id, response_data = upload_purchase_receipt_to_api(pr)
        if success:
            pr['name'] = system_id
            if 'items' in response_data:
                for i, item in enumerate(pr['items']):
                    item['name'] = response_data['items'][i]['name']
            successful_uploads.append(pr)

    save_to_csv(successful_uploads, 'purchase_receipts.csv')


if __name__ == "__main__":
    main()
