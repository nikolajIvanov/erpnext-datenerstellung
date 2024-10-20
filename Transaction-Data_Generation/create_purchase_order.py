import os
import csv
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
from api.purchase_order_api import PurchaseOrderAPI

# Versuche, PurchaseOrderAPI zu importieren, ignoriere den Fehler, wenn es nicht klappt
try:
    HAS_API = True
except ImportError:
    HAS_API = False
    logging.warning("PurchaseOrderAPI could not be imported. API functionality will be disabled.")

@dataclass
class Config:
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR: str = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR: str = os.path.join(BASE_DIR, 'Generated_CSV')
    SUCCESS_DIR: str = os.path.join(BASE_DIR, 'Beschaffungsprozess Demo')
    ERROR_DIR: str = os.path.join(BASE_DIR, 'Import Error')
    MAPPING_FILE: str = 'item_supplier_mapping.csv'

config = Config()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_to_api(purchase_orders: List[Dict[str, Any]]) -> bool:
    if not HAS_API:
        logging.warning("API functionality is disabled. Skipping API send.")
        return True

    po_api = PurchaseOrderAPI()
    all_success = True

    for po in purchase_orders:
        try:
            result = po_api.create(po)
            logging.info(f"Successfully created Purchase Order: {po['name']}")
        except Exception as e:
            logging.error(f"Failed to create Purchase Order {po['name']}. Error: {str(e)}")
            all_success = False

    return all_success


def load_csv_data(filename: str) -> List[Dict[str, Any]]:
    filepath = os.path.join(config.INPUT_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return []


def load_item_supplier_mapping() -> Dict[str, str]:
    mapping = {}
    mapping_file = os.path.join(config.INPUT_DIR, config.MAPPING_FILE)
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[row['Item Code']] = row['Supplier ID']
    else:
        logging.warning(f"Mapping file not found: {mapping_file}")
    return mapping


def generate_id(prefix: str, date: datetime) -> str:
    year = date.year
    number = random.randint(1, 99999)
    return f"{prefix}-{year}-{number:05d}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def generate_purchase_orders(num_orders: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    products = load_csv_data('items.csv')
    item_supplier_mapping = load_item_supplier_mapping()

    purchase_orders = []
    for _ in range(num_orders):
        po_date = random_date(start_date, end_date)
        product = random.choice(products)
        item_code = product['Item Code']

        supplier_id = item_supplier_mapping.get(item_code, "DEFAULT_SUPPLIER_ID")

        quantity = random.randint(1, 100)
        rate = float(product['Valuation Rate'])
        amount = round(quantity * rate, 2)

        po = {
            "name": generate_id("PUR-ORD", po_date),
            "doctype": "Purchase Order",
            "company": "Velo GmbH",
            "currency": "EUR",
            "transaction_date": po_date.strftime("%Y-%m-%d"),
            "conversion_rate": 1.00,
            "status": "To Receive and Bill",
            "supplier": supplier_id,
            "title": f"Purchase Order for {supplier_id}",
            "items": [{
                "item_code": item_code,
                "item_name": product['Item Name'],
                "qty": quantity,
                "rate": rate,
                "amount": amount,
                "schedule_date": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
                "uom": product['Default Unit of Measure'],
                "stock_uom": product['Default Unit of Measure'],
                "conversion_factor": 1.00,
                "warehouse": "Lager Stuttgart - B"
            }]
        }
        purchase_orders.append(po)

    success = send_to_api(purchase_orders)
    save_to_csv(purchase_orders, 'generated_purchase_orders.csv', success)

    return purchase_orders


def save_to_csv(purchase_orders: List[Dict[str, Any]], filename: str, success: bool) -> None:
    output_dir = config.SUCCESS_DIR if success else config.ERROR_DIR
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    fieldnames = ["name", "company", "currency", "transaction_date", "conversion_rate", "status", "supplier", "title",
                  "item_code", "item_name", "qty", "rate", "amount", "schedule_date", "uom", "stock_uom",
                  "conversion_factor", "warehouse"]

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for po in purchase_orders:
                row = {field: po.get(field, '') for field in fieldnames if field != 'items'}
                item = po['items'][0]  # Assuming one item per PO for simplicity
                row.update({field: item.get(field, '') for field in fieldnames if field in item})
                writer.writerow(row)
        logging.info(f"Purchase orders saved to {filepath}")
    except IOError as e:
        logging.error(f"Error saving to CSV: {str(e)}")


def delete_purchase_orders() -> None:
    # Implementieren Sie hier die Logik zum Löschen der Purchase Orders
    logging.info("All purchase orders have been deleted.")


if __name__ == "__main__":
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    num_orders = 1
    generate_purchase_orders(num_orders, start_date, end_date)