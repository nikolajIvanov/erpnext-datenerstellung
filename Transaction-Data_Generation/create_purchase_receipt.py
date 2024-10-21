import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict, Tuple
from api.purchase_receipt_api import PurchaseReceiptAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2023, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    TARGET_WAREHOUSE = "Lager Stuttgart - B"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_purchase_orders(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def generate_purchase_receipts(purchase_orders: List[Dict]) -> List[Dict]:
    purchase_receipts = []
    for po in purchase_orders:
        pr_date = datetime.strptime(po['transaction_date'], "%Y-%m-%d") + timedelta(days=random.randint(1, 7))

        purchase_receipt = {
            "doctype": "Purchase Receipt",
            "naming_series": "MAT-PRE-.YYYY.-",
            "supplier": po['supplier'],
            "posting_date": pr_date.strftime("%Y-%m-%d"),
            "posting_time": pr_date.strftime("%H:%M:%S"),
            "company": po['company'],
            "currency": po['currency'],
            "conversion_rate": float(po['conversion_rate']),
            "buying_price_list": po['buying_price_list'],
            "price_list_currency": po['price_list_currency'],
            "plc_conversion_rate": float(po['plc_conversion_rate']),
            "set_warehouse": Config.TARGET_WAREHOUSE,
            "is_return": 0,
            "apply_putaway_rule": 0,
            "status": "To Bill",
            "set_posting_time": 1,
            "docstatus": 1  # 1 = Submitted
        }
        purchase_receipts.append(purchase_receipt)
    return purchase_receipts


def upload_purchase_receipt_to_api(purchase_receipt: Dict) -> Tuple[bool, str, Dict]:
    api = PurchaseReceiptAPI()
    try:
        response = api.create(purchase_receipt)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            logging.info(f"Successfully uploaded Purchase Receipt. ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        logging.error(f"Failed to upload Purchase Receipt: {str(e)}")
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
    purchase_orders = load_purchase_orders('uploaded_purchase_orders.csv')
    logging.info(f"Loaded {len(purchase_orders)} purchase orders")

    purchase_receipts = generate_purchase_receipts(purchase_orders)
    logging.info(f"Generated {len(purchase_receipts)} purchase receipts")

    successful_uploads = []
    for pr in purchase_receipts:
        success, system_id, response_data = upload_purchase_receipt_to_api(pr)
        if success:
            pr['name'] = system_id
            successful_uploads.append(pr)
        else:
            logging.error(f"Failed to upload purchase receipt: {pr}")

    save_to_csv(successful_uploads, 'uploaded_purchase_receipts.csv')
    logging.info(f"Successfully uploaded {len(successful_uploads)} out of {len(purchase_receipts)} purchase receipts")


if __name__ == "__main__":
    main()