import csv
import os
from datetime import datetime
import logging
from typing import List, Dict, Tuple
from api.stock_entry_api import StockEntryAPI
import uuid
import time
from copy import deepcopy

class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    MASTER_DATA_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    WORK_ORDERS_FILE = 'uploaded_work_orders.csv'
    BATCH_NUMBERS_FILE = 'batch_numbers.csv'
    BOM_FILES = ['bom_bike.csv', 'bom_ebike.csv']
    PRODUCTION_WAREHOUSE = "Lager Stuttgart - B"
    WIP_WAREHOUSE = "Lager Stuttgart - B"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_csv_data(filename: str, directory: str = Config.INPUT_DIR) -> List[Dict]:
    with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_batch_numbers() -> Dict[str, str]:
    batch_data = load_csv_data(Config.BATCH_NUMBERS_FILE, Config.MASTER_DATA_DIR)
    return {batch['Item']: batch['Batch ID'] for batch in batch_data}


def load_bom_data() -> Dict[str, Dict]:
    bom_data = {}
    for filename in Config.BOM_FILES:
        with open(os.path.join(Config.MASTER_DATA_DIR, filename), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            bom_info = rows[0]
            bom_id = bom_info['ID']
            items = [row for row in rows if row['Item Code (Items)'].strip()]  # Only include rows with an Item Code
            bom_data[bom_id] = {
                'ID': bom_id,
                'Item': bom_info['Item'],
                'Item Name': bom_info['Item Name'],
                'Items': items
            }
    return bom_data


def generate_stock_entries(work_orders: List[Dict], bom_data: Dict[str, Dict], batch_numbers: Dict[str, str]) -> List[Dict]:
    stock_entries = []
    for wo in work_orders:
        bom = bom_data[wo['BOM No']]
        posting_date = datetime.now().strftime("%Y-%m-%d")
        posting_time = datetime.now().strftime("%H:%M:%S")
        stock_entry = {
            "name": f"MAT-STE-{uuid.uuid4().hex[:8].upper()}",  # Generiere eine eindeutige ID
            "doctype": "Stock Entry",
            "naming_series": "MAT-STE-.YYYY.-",
            "stock_entry_type": "Material Transfer for Manufacture",
            "purpose": "Material Transfer for Manufacture",
            "company": wo['Company'],
            "posting_date": posting_date,
            "posting_time": posting_time,
            "from_bom": 1,
            "use_multi_level_bom": 1,
            "bom_no": wo['BOM No'],
            "work_order": wo['ID'],
            "fg_completed_qty": float(wo['Qty To Manufacture']),
            "from_warehouse": Config.PRODUCTION_WAREHOUSE,
            "to_warehouse": Config.WIP_WAREHOUSE,
            "docstatus": 1,
            "items": []
        }

        total_outgoing_value = 0
        for item in bom['Items']:
            qty = float(item['Qty (Items)']) * float(wo['Qty To Manufacture'])
            rate = float(item.get('Rate (Items)', 0))
            amount = round(qty * rate, 2)
            total_outgoing_value += amount

            stock_entry["items"].append({
                "item_code": item['Item Code (Items)'],
                "description": f"{item['Item Code (Items)']}: Hochwertige Komponente für optimale Leistung.",
                "s_warehouse": Config.PRODUCTION_WAREHOUSE,
                "t_warehouse": Config.WIP_WAREHOUSE,
                "qty": qty,
                "transfer_qty": qty,
                "uom": item['UOM (Items)'],
                "stock_uom": item['UOM (Items)'],
                "conversion_factor": 1.0,
                "basic_rate": rate,
                "basic_amount": amount,
                "amount": amount,
                "batch_no": batch_numbers.get(item['Item Code (Items)'], ""),
                "expense_account": "Herstellungskosten: Schwund - B",
                "cost_center": "Main - B"
            })

        stock_entry["total_outgoing_value"] = total_outgoing_value
        stock_entry["total_incoming_value"] = total_outgoing_value
        stock_entry["value_difference"] = 0.0
        stock_entry["total_additional_costs"] = 0.0

        stock_entries.append(stock_entry)
    return stock_entries


def upload_stock_entry_to_api(stock_entry: Dict) -> Tuple[bool, Dict]:
    api = StockEntryAPI()
    try:
        response = api.create(stock_entry)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            logging.info(f"Successfully uploaded Stock Entry. System ID: {system_id}")
            return True, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        logging.error(f"Failed to upload Stock Entry: {str(e)}")
        return False, {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        logging.warning(f"No data to save to {filename}")
        return

    fieldnames = list(data[0].keys())

    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    logging.info(f"Saved {len(data)} records to {filename}")


def generate_manufacture_stock_entry(original_entry: Dict) -> Dict:
    manufacture_entry = deepcopy(original_entry)
    manufacture_entry["stock_entry_type"] = "Manufacture"
    manufacture_entry["purpose"] = "Manufacture"
    manufacture_entry["docstatus"] = 1
    if 'name' in manufacture_entry:
        del manufacture_entry['name']
        del manufacture_entry["purpose"]
    return manufacture_entry


def generate_manufacture_stock_entry(original_entry: Dict, work_order: Dict, bom_data: Dict) -> Dict:
    manufacture_entry = deepcopy(original_entry)
    manufacture_entry["stock_entry_type"] = "Manufacture"
    manufacture_entry["purpose"] = "Manufacture"
    if 'name' in manufacture_entry:
        del manufacture_entry['name']

    # Finden Sie das BOM für dieses Work Order
    bom = bom_data[work_order['BOM No']]

    # Fügen Sie das fertige Produkt (Fahrrad) hinzu
    finished_item = {
        "t_warehouse": Config.PRODUCTION_WAREHOUSE,
        "item_code": bom['Item'],
        "item_name": bom['Item Name'],
        "is_finished_item": 1,
        "description": f"Fertig montiertes Fahrrad: {bom['Item Name']}",
        "item_group": "Fahrräder",
        "qty": float(work_order['Qty To Manufacture']),
        "transfer_qty": float(work_order['Qty To Manufacture']),
        "uom": "Nos",
        "stock_uom": "Nos",
        "conversion_factor": 1.0,
        "basic_rate": sum(
            float(item.get('basic_rate', 0)) * float(item.get('qty', 0)) for item in manufacture_entry['items']),
        "expense_account": "5000 - Aufwendungen f. Roh-, Hilfs- und Betriebsstoffe und f. bezogene Waren - B",
        "cost_center": "Main - B",
        "bom_no": work_order['BOM No']
    }

    # Berechnen Sie den Gesamtbetrag
    finished_item['basic_amount'] = finished_item['basic_rate'] * finished_item['qty']
    finished_item['amount'] = finished_item['basic_amount']

    manufacture_entry['items'].append(finished_item)

    return manufacture_entry


def process_stock_entries(stock_entries: List[Dict], work_orders: List[Dict], bom_data: Dict) -> Tuple[
    List[Dict], List[Dict]]:
    all_entries = []
    successful_uploads = []

    # Erste Runde: Ursprüngliche Stock Entries
    for se, wo in zip(stock_entries, work_orders):
        success, content = upload_stock_entry_to_api(se)
        if success:
            se['name'] = content['name']
            successful_uploads.append(se)
        else:
            se['name'] = "Upload fehlgeschlagen"
        all_entries.append(se)

    logging.info(f"Uploaded {len(stock_entries)} original stock entries. Waiting 10 seconds...")
    time.sleep(10)  # Warte 10 Sekunden

    # Zweite Runde: Manufacture Stock Entries
    for original_se, wo in zip(stock_entries, work_orders):
        manufacture_entry = generate_manufacture_stock_entry(original_se, wo, bom_data)
        success, content = upload_stock_entry_to_api(manufacture_entry)
        if success:
            manufacture_entry['name'] = content['name']
            successful_uploads.append(manufacture_entry)
        else:
            manufacture_entry['name'] = "Upload fehlgeschlagen"
        all_entries.append(manufacture_entry)

    return all_entries, successful_uploads


def main():
    work_orders = load_csv_data(Config.WORK_ORDERS_FILE)
    logging.info(f"Loaded {len(work_orders)} work orders")

    bom_data = load_bom_data()
    logging.info(f"Loaded BOM data for {len(bom_data)} BOMs")

    batch_numbers = load_batch_numbers()
    logging.info(f"Loaded {len(batch_numbers)} batch numbers")

    stock_entries = generate_stock_entries(work_orders, bom_data, batch_numbers)
    logging.info(f"Generated {len(stock_entries)} stock entries")

    all_entries, successful_uploads = process_stock_entries(stock_entries, work_orders, bom_data)

    # Speichern Sie alle Stock Entries in CSV
    save_to_csv(all_entries, 'all_stock_entries.csv')

    # Speichern Sie nur erfolgreich hochgeladene Stock Entries
    save_to_csv(successful_uploads, 'uploaded_stock_entries.csv')

    logging.info(f"Successfully uploaded {len(successful_uploads)} out of {len(all_entries)} stock entries")


if __name__ == "__main__":
    main()