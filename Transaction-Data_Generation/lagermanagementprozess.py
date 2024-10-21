import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict
from api.stock_entry_api import StockEntryAPI
import uuid


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2024, 1, 1)
    END_DATE = datetime(2024, 12, 31)
    MAIN_WAREHOUSE = "Lager Stuttgart - B"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_warehouses() -> List[str]:
    warehouses = load_csv_data('Warehouse.csv')
    return [w['Warehouse Name'] for w in warehouses if w['Warehouse Name'] != Config.MAIN_WAREHOUSE]


def load_items() -> List[Dict]:
    return load_csv_data('items.csv')


def generate_stock_entry(warehouses: List[str], items: List[Dict]) -> Dict:
    transfer_date = random_date(Config.START_DATE, Config.END_DATE)
    target_warehouse = random.choice(warehouses)

    stock_entry = {
        "name": generate_id("MAT-STE"),
        "doctype": "Stock Entry",
        "naming_series": "MAT-STE-.YYYY.-",
        "stock_entry_type": "Material Transfer",
        "purpose": "Material Transfer",
        "add_to_transit": 1,
        "company": "Velo GmbH",
        "posting_date": transfer_date.strftime("%Y-%m-%d"),
        "posting_time": datetime.now().strftime("%H:%M:%S"),
        "set_posting_time": 0,
        "from_warehouse": Config.MAIN_WAREHOUSE,
        "to_warehouse": target_warehouse,
        "total_outgoing_value": 0.0,
        "total_incoming_value": 0.0,
        "value_difference": 0.0,
        "total_additional_costs": 0.0,
        "docstatus": 1,
        "items": []
    }

    total_amount = 0.0
    for _ in range(random.randint(1, 5)):
        item = random.choice(items)
        qty = random.randint(1, 10)
        rate = float(item['Valuation Rate'])
        amount = round(qty * rate, 2)
        total_amount += amount

        stock_entry["items"].append({
            "doctype": "Stock Entry Detail",
            "s_warehouse": Config.MAIN_WAREHOUSE,
            "t_warehouse": target_warehouse,
            "item_code": item['Item Code'],
            "item_name": item['Item Name'],
            "description": item.get('Description', ''),
            "item_group": item.get('Item Group', ''),
            "qty": qty,
            "transfer_qty": qty,
            "uom": item['Default Unit of Measure'],
            "stock_uom": item['Default Unit of Measure'],
            "conversion_factor": 1.0,
            "basic_rate": rate,
            "valuation_rate": rate,
            "basic_amount": amount,
            "amount": amount,
            "expense_account": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B",
            "cost_center": "Main - B"
        })

    stock_entry["total_outgoing_value"] = total_amount
    stock_entry["total_incoming_value"] = total_amount
    stock_entry["total_amount"] = total_amount

    return stock_entry


def upload_stock_entry_to_api(stock_entry: Dict) -> bool:
    api = StockEntryAPI()
    try:
        response = api.create(stock_entry)
        if response.get('name'):
            logging.info(f"Successfully uploaded Stock Entry: {response['name']}")
            return True
        else:
            logging.error(f"Failed to upload Stock Entry: {response}")
            return False
    except Exception as e:
        logging.error(f"Error uploading Stock Entry: {str(e)}")
        return False


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        logging.warning(f"No data to save to {filename}")
        return

    fieldnames = list(data[0].keys())
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logging.info(f"Saved {len(data)} records to {filename}")


def main(num_transfers: int = 10):
    warehouses = load_warehouses()
    items = load_items()

    successful_uploads = []
    failed_uploads = []

    for _ in range(num_transfers):
        stock_entry = generate_stock_entry(warehouses, items)
        if upload_stock_entry_to_api(stock_entry):
            successful_uploads.append(stock_entry)
        else:
            failed_uploads.append(stock_entry)

    save_to_csv(successful_uploads, 'successful_stock_entries.csv')
    save_to_csv(failed_uploads, 'failed_stock_entries.csv')

    logging.info(f"Total transfers: {num_transfers}")
    logging.info(f"Successful uploads: {len(successful_uploads)}")
    logging.info(f"Failed uploads: {len(failed_uploads)}")


if __name__ == "__main__":
    main()