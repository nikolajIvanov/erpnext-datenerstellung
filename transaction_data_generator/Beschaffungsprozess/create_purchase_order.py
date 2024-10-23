import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict, Tuple
from api.purchase_order_api import PurchaseOrderAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    LOG_DIR = os.path.join(BASE_DIR, 'logs', 'purchase_orders')
    START_DATE = datetime.now() - timedelta(days=5*365)
    END_DATE = datetime.now()
    NUM_ORDERS = 2
    TARGET_WAREHOUSE = "Lager Stuttgart - B"
    MAPPING_FILE = 'item_supplier_mapping.csv'


# Create logs directory if it doesn't exist
os.makedirs(Config.LOG_DIR, exist_ok=True)

# Configure file logger
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, f'purchase_order_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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


def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_item_supplier_mapping() -> Dict[str, str]:
    mapping = {}
    mapping_file = os.path.join(Config.INPUT_DIR, Config.MAPPING_FILE)
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[row['Item Code']] = row['Supplier ID']
    return mapping


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def calculate_taxes(net_amount: float, tax_rate: float = 19.0) -> Tuple[float, float]:
    tax_amount = net_amount * (tax_rate / 100)
    gross_amount = net_amount + tax_amount
    return round(tax_amount, 2), round(gross_amount, 2)


def filter_components(products: List[Dict]) -> List[Dict]:
    return [product for product in products if product['Item Group'] == 'Fahrradkomponenten']


def generate_purchase_orders(products: List[Dict], item_supplier_mapping: Dict[str, str]) -> List[Dict]:
    purchase_orders = []
    for _ in range(Config.NUM_ORDERS):
        po_date = random_date(Config.START_DATE, Config.END_DATE)
        product = random.choice(products)
        item_code = product['Item Code']

        supplier_id = item_supplier_mapping.get(item_code, "DEFAULT_SUPPLIER_ID")
        quantity = 500
        rate = float(product['Valuation Rate'])
        net_amount = round(quantity * rate, 2)
        tax_amount, gross_amount = calculate_taxes(net_amount)

        po = {
            "doctype": "Purchase Order",
            "naming_series": "PUR-ORD-.YYYY.-",
            "company": "Velo GmbH",
            "currency": "EUR",
            "transaction_date": po_date.strftime("%Y-%m-%d"),
            "schedule_date": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            "conversion_rate": 1.0,
            "supplier": supplier_id,
            "supplier_name": f"Purchase Order for {supplier_id}",
            "items": [{
                "item_code": item_code,
                "item_name": product['Item Name'],
                "description": product['Description'],
                "qty": quantity,
                "rate": rate,
                "amount": net_amount,
                "uom": product['Default Unit of Measure'],
                "stock_uom": product['Default Unit of Measure'],
                "conversion_factor": 1.0,
                "warehouse": Config.TARGET_WAREHOUSE
            }],
            "total_taxes_and_charges": tax_amount,
            "grand_total": gross_amount,
            "rounded_total": round(gross_amount),
            "status": "To Receive and Bill",
            "docstatus": 1
        }
        purchase_orders.append(po)
    return purchase_orders


def upload_purchase_order_to_api(purchase_order: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseOrderAPI()
    try:
        response = api.create(purchase_order)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            console_logger.info(f"Successfully uploaded Purchase Order. ID: {system_id}")
            file_logger.info(f"Successfully created Purchase Order with ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        file_logger.error(f"Failed to upload Purchase Order: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        file_logger.warning("No data to save to CSV.")
        return

    flattened_data = []
    for po in data:
        for item in po['items']:
            row = {
                "ID": po['name'],
                "Company": po['company'],
                "Currency": po['currency'],
                "Date": po['transaction_date'],
                "Exchange Rate": "1,00",
                "Series": po['naming_series'],
                "Status": po['status'],
                "Supplier": po['supplier'],
                "Title": po['supplier_name'],
                "ID (Items)": item.get('name', ''),
                "Amount (Items)": item['amount'],
                "Item Code (Items)": item['item_code'],
                "Item Name (Items)": item['item_name'],
                "Quantity (Items)": item['qty'],
                "Rate (Items)": item['rate'],
                "Required By (Items)": po['schedule_date'],
                "Stock UOM (Items)": item['stock_uom'],
                "UOM (Items)": item['uom'],
                "UOM Conversion Factor (Items)": item['conversion_factor'],
                "Set Target Warehouse": item['warehouse'],
                "Net Total": f"{item['amount']:.2f}".replace('.', ','),
                "Total Taxes and Charges": f"{po['total_taxes_and_charges']:.2f}".replace('.', ','),
                "Grand Total": f"{po['grand_total']:.2f}".replace('.', ','),
                "Rounded Total": f"{po['rounded_total']:.2f}".replace('.', ','),
            }
            flattened_data.append(row)

    fieldnames = flattened_data[0].keys()
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)


def main():
    products = load_csv_data('items.csv')
    components = filter_components(products)
    item_supplier_mapping = load_item_supplier_mapping()
    purchase_orders = generate_purchase_orders(components, item_supplier_mapping)

    successful_uploads = []
    for po in purchase_orders:
        success, system_id, response_data = upload_purchase_order_to_api(po)
        if success:
            po['name'] = system_id
            if 'items' in response_data:
                for i, item in enumerate(po['items']):
                    item['name'] = response_data['items'][i]['name']
            successful_uploads.append(po)

    save_to_csv(successful_uploads, 'purchase_orders.csv')


if __name__ == "__main__":
    main()
