import csv
import os
import random
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Tuple
from api.purchase_order_api import PurchaseOrderAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2023, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    NUM_ORDERS = 10
    TARGET_WAREHOUSE = "Lager Stuttgart - B"
    MAPPING_FILE = 'item_supplier_mapping.csv'


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_item_supplier_mapping() -> Dict[str, str]:
    mapping = {}
    mapping_file = os.path.join(Config.INPUT_DIR, Config.MAPPING_FILE)
    with open(mapping_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row['Item Code']] = row['Supplier ID']
    return mapping


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def generate_purchase_orders(num_orders: int, suppliers: List[Dict], items: List[Dict],
                             item_supplier_mapping: Dict[str, str]) -> List[Dict]:
    purchase_orders = []
    for _ in range(num_orders):
        po_date = random_date(Config.START_DATE, Config.END_DATE)

        # Select a random item and its corresponding supplier
        item = random.choice(items)
        supplier_id = item_supplier_mapping.get(item['Item Code'])
        supplier = next((s for s in suppliers if s['ID'] == supplier_id), None)

        if not supplier:
            logging.warning(f"No supplier found for item {item['Item Code']}. Skipping this order.")
            continue

        purchase_order = {
            "title": f"Purchase Order for {supplier['Supplier Name']}",
            "naming_series": "PUR-ORD-.YYYY.-",
            "supplier": supplier['ID'],
            "transaction_date": po_date.strftime("%Y-%m-%d"),
            "schedule_date": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            "company": "Velo GmbH",
            "currency": "EUR",
            "conversion_rate": 1.0,
            "buying_price_list": "Standard Buying",
            "price_list_currency": "EUR",
            "plc_conversion_rate": 1.0,
            "set_warehouse": Config.TARGET_WAREHOUSE,
            "items": [{
                "item_code": item['Item Code'],
                "item_name": item['Item Name'],
                "description": item['Description'],
                "qty": random.randint(1, 100),
                "uom": item['Default Unit of Measure'],
                "rate": float(item['Valuation Rate']),
                "warehouse": Config.TARGET_WAREHOUSE
            }],
            "status": "Draft",
            "docstatus": 1  # 0 = Draft; 1 = Submitted
        }
        purchase_orders.append(purchase_order)
    return purchase_orders


def map_csv_to_api_fields(purchase_order: Dict) -> Dict:
    # The field mapping is already correct in this case
    return purchase_order


def upload_purchase_order_to_api(purchase_order: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseOrderAPI()
    mapped_purchase_order = map_csv_to_api_fields(purchase_order)
    try:
        response = api.create(mapped_purchase_order)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            logging.info(f"Successfully uploaded Purchase Order. ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        logging.error(f"Failed to upload Purchase Order: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        logging.warning("No data to save to CSV.")
        return

    fieldnames = list(data[0].keys())
    if 'name' not in fieldnames:
        fieldnames.append('name')  # Ensure 'name' field is included

    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    logging.info(f"Saved {len(data)} records to {filename}")


def main():
    suppliers = load_csv_data('suppliers.csv')
    items = load_csv_data('items.csv')
    item_supplier_mapping = load_item_supplier_mapping()
    logging.info(
        f"Loaded {len(suppliers)} suppliers, {len(items)} items, and {len(item_supplier_mapping)} item-supplier mappings")

    purchase_orders = generate_purchase_orders(Config.NUM_ORDERS, suppliers, items, item_supplier_mapping)
    logging.info(f"Generated {len(purchase_orders)} purchase orders")

    successful_uploads = []
    for po in purchase_orders:
        success, system_id, _ = upload_purchase_order_to_api(po)
        if success:
            po['name'] = system_id  # Add the system-generated ID to the original data
            successful_uploads.append(po)
        else:
            logging.error(f"Failed to upload purchase order: {po}")

    # Remove 'title' field if present
    for po in successful_uploads:
        po.pop('title', None)

    # Save successfully uploaded purchase orders to a separate CSV
    save_to_csv(successful_uploads, 'uploaded_purchase_orders.csv')

    logging.info(f"Successfully uploaded {len(successful_uploads)} out of {len(purchase_orders)} purchase orders")


if __name__ == "__main__":
    main()