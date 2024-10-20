import os
import csv
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
from api.purchase_receipt_api import PurchaseReceiptAPI


@dataclass
class Config:
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR: str = os.path.join(BASE_DIR, 'Beschaffungsprozess Demo')
    MASTER_DATA_DIR: str = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR: str = os.path.join(BASE_DIR, 'Beschaffungsprozess Demo')
    ERROR_DIR: str = os.path.join(BASE_DIR, 'Import Error')
    TARGET_WAREHOUSE: str = "Lager Stuttgart - B"
    PO_FILE: str = 'generated_purchase_orders.csv'
    ITEMS_FILE: str = 'items.csv'


config = Config()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_csv_data(filename: str, directory: str) -> List[Dict[str, Any]]:
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return []


def load_purchase_orders() -> List[Dict[str, Any]]:
    return load_csv_data(config.PO_FILE, config.INPUT_DIR)


def load_items() -> Dict[str, Dict[str, Any]]:
    items = load_csv_data(config.ITEMS_FILE, config.MASTER_DATA_DIR)
    return {item['Item Code']: item for item in items}


def generate_id(prefix: str, date: datetime) -> str:
    year = date.year
    number = random.randint(1, 99999)
    return f"{prefix}-{year}-{number:05d}"


def generate_purchase_receipts(purchase_orders: List[Dict[str, Any]], items: Dict[str, Dict[str, Any]]) -> List[
    Dict[str, Any]]:
    purchase_receipts = []
    for po in purchase_orders:
        pr_date = datetime.strptime(po['transaction_date'], "%Y-%m-%d") + timedelta(days=random.randint(1, 7))

        item_code = po['Item Code (Items)']
        item = items.get(item_code)

        if not item:
            logging.warning(f"Item with code {item_code} not found in items data. Skipping this PO.")
            continue

        pr = {
            "ID": generate_id("MAT-PRE", pr_date),
            "Company": po['company'],
            "Currency": po['currency'],
            "Date": pr_date.strftime("%Y-%m-%d"),
            "Exchange Rate": po['conversion_rate'],
            "Net Total (Company Currency)": po['Amount (Items)'],
            "Posting Time": pr_date.strftime("%H:%M:%S.%f"),
            "Series": "MAT-PRE-.YYYY.-",
            "Status": "Draft",
            "Supplier": po['supplier'],
            "ID (Items)": generate_id("PRITEM", pr_date),
            "Conversion Factor (Items)": "1,00",
            "Item Code (Items)": item_code,
            "Item Name (Items)": item['Item Name'],
            "Rate (Company Currency) (Items)": po['Rate (Items)'],
            "Received Quantity (Items)": po['Quantity (Items)'],
            "Stock UOM (Items)": item['Default Unit of Measure'],
            "UOM (Items)": item['Default Unit of Measure'],
            "Purchase Order (Items)": po['name'],
            "Purchase Order Item (Items)": po['ID (Items)'],
            "Accepted Warehouse (Items)": config.TARGET_WAREHOUSE,
            "Tax Rate (Purchase Taxes and Charges)": "19,00",
            "Account Head (Purchase Taxes and Charges)": "1406 - Abziehbare Vorsteuer 19 % - B",
            "Accepted Quantity (Items)": po['Quantity (Items)'],
            "Description (Purchase Taxes and Charges)": "Abziehbare Vorsteuer 19 %",
            "Type (Purchase Taxes and Charges)": "On Net Total",
            "Add or Deduct (Purchase Taxes and Charges)": "Add",
            "Consider Tax or Charge for (Purchase Taxes and Charges)": "Total",
            "Batch No (Items)": ""  # We don't have batch information
        }
        purchase_receipts.append(pr)
    return purchase_receipts


def save_to_csv(data: List[Dict[str, Any]], filename: str, directory: str) -> None:
    filepath = os.path.join(directory, filename)
    if not data:
        logging.warning(f"No data to save to {filepath}")
        return

    fieldnames = data[0].keys()
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data saved to {filepath}")
    except IOError as e:
        logging.error(f"Error saving to CSV: {str(e)}")


def main() -> None:
    purchase_orders = load_purchase_orders()
    logging.info(f"Loaded {len(purchase_orders)} purchase orders")

    if not purchase_orders:
        logging.warning("No purchase orders found. Check the input file.")
        return

    items = load_items()
    logging.info(f"Loaded {len(items)} items")

    purchase_receipts = generate_purchase_receipts(purchase_orders, items)
    logging.info(f"Generated {len(purchase_receipts)} purchase receipts")

    pr_api = PurchaseReceiptAPI()
    successful_receipts = []
    failed_receipts = []

    for pr in purchase_receipts:
        try:
            logging.info(f"Sending Purchase Receipt for PO {pr['Purchase Order (Items)']} to API...")
            result = pr_api.create(pr)
            logging.info(f"Successfully created Purchase Receipt: {result.get('name', 'Unknown')}")
            successful_receipts.append(pr)
        except Exception as e:
            logging.error(f"Failed to create Purchase Receipt. Error: {str(e)}")
            failed_receipts.append(pr)

    save_to_csv(successful_receipts, 'successful_purchase_receipts.csv', config.OUTPUT_DIR)
    save_to_csv(failed_receipts, 'failed_purchase_receipts.csv', config.ERROR_DIR)

    logging.info("Process completed.")


if __name__ == "__main__":
    main()