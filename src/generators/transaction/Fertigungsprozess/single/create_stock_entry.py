import csv
import os
from datetime import datetime
import logging
import json
from typing import List, Dict, Tuple
from src.api.endpoints.stock_entry_api import StockEntryAPI
import uuid
import time
from copy import deepcopy


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'generated')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'generated')
    API_PAYLOAD_DIR = os.path.join(BASE_DIR, 'api_payloads', 'stock_entry')
    LOG_DIR = os.path.join(BASE_DIR, 'process_logs', 'stock_entries')
    MASTER_DATA_DIR = os.path.join(BASE_DIR, 'master')
    WORK_ORDERS_FILE = 'uploaded_work_orders.csv'
    BATCH_NUMBERS_FILE = 'batch_numbers.csv'
    BOM_FILES = ['bom_bike.csv', 'bom_ebike.csv']
    PRODUCTION_WAREHOUSE = "Lager Stuttgart - B"
    WIP_WAREHOUSE = "Lager Stuttgart - B"


# Create necessary directories
os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.API_PAYLOAD_DIR, exist_ok=True)

# Configure file logger
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, f'stock_entry_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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
            items = [row for row in rows if row['Item Code (Items)'].strip()]
            bom_data[bom_id] = {
                'ID': bom_id,
                'Item': bom_info['Item'],
                'Item Name': bom_info['Item Name'],
                'Items': items
            }
    return bom_data


def generate_stock_entries(work_orders: List[Dict], bom_data: Dict[str, Dict], batch_numbers: Dict[str, str]) -> List[
    Dict]:
    stock_entries = []
    for wo in work_orders:
        bom = bom_data[wo['BOM No']]
        posting_date = datetime.now().strftime("%Y-%m-%d")
        posting_time = datetime.now().strftime("%H:%M:%S")
        stock_entry = {
            "name": f"MAT-STE-{uuid.uuid4().hex[:8].upper()}",
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


def generate_manufacture_stock_entry(original_entry: Dict, work_order: Dict, bom_data: Dict) -> Dict:
    manufacture_entry = deepcopy(original_entry)
    manufacture_entry["stock_entry_type"] = "Manufacture"
    manufacture_entry["purpose"] = "Manufacture"
    if 'name' in manufacture_entry:
        del manufacture_entry['name']

    bom = bom_data[work_order['BOM No']]
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

    finished_item['basic_amount'] = finished_item['basic_rate'] * finished_item['qty']
    finished_item['amount'] = finished_item['basic_amount']

    manufacture_entry['items'].append(finished_item)

    return manufacture_entry


def save_api_payload(transfer_entries: List[Dict], manufacture_entries: List[Dict]):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save Material Transfer entries
    transfer_filename = os.path.join(Config.API_PAYLOAD_DIR, f'stock_entry_transfer_{timestamp}.json')
    with open(transfer_filename, 'w', encoding='utf-8') as f:
        json.dump(transfer_entries, f, indent=2)
    print(f"Material Transfer Payloads gespeichert in: {transfer_filename}")

    # Save Manufacture entries
    manufacture_filename = os.path.join(Config.API_PAYLOAD_DIR, f'stock_entry_manufacture_{timestamp}.json')
    with open(manufacture_filename, 'w', encoding='utf-8') as f:
        json.dump(manufacture_entries, f, indent=2)
    print(f"Manufacture Payloads gespeichert in: {manufacture_filename}")


def upload_stock_entry_to_api(stock_entry: Dict) -> Tuple[bool, Dict]:
    api = StockEntryAPI()
    try:
        response = api.create(stock_entry)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            console_logger.info(f"Successfully uploaded Stock Entry. System ID: {system_id}")
            return True, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        file_logger.error(f"Failed to upload Stock Entry: {str(e)}")
        return False, {}


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


def process_stock_entries(stock_entries: List[Dict], work_orders: List[Dict], bom_data: Dict) -> Tuple[
    List[Dict], List[Dict]]:
    all_entries = []
    successful_uploads = []

    # Generate manufacture entries first
    manufacture_entries = []
    for se, wo in zip(stock_entries, work_orders):
        manufacture_entry = generate_manufacture_stock_entry(se, wo, bom_data)
        manufacture_entries.append(manufacture_entry)

    # Save API payloads before processing
    save_api_payload(stock_entries, manufacture_entries)

    # Process Material Transfer entries
    for se in stock_entries:
        success, content = upload_stock_entry_to_api(se)
        if success:
            se['name'] = content['name']
            successful_uploads.append(se)
        all_entries.append(se)

    logging.info(f"Uploaded {len(stock_entries)} original stock entries. Waiting 10 seconds...")
    time.sleep(10)

    # Process Manufacture entries
    for me in manufacture_entries:
        success, content = upload_stock_entry_to_api(me)
        if success:
            me['name'] = content['name']
            successful_uploads.append(me)
        all_entries.append(me)

    return all_entries, successful_uploads


def main():
    # Load work orders
    work_orders = load_csv_data(Config.WORK_ORDERS_FILE)
    print(f"Datengenerierung gestartet...")
    print(f"Geladene Workorders: {len(work_orders)}")

    # Load BOM data
    bom_data = load_bom_data()
    print(f"Geladene BOMs: {len(bom_data)}")

    # Load batch numbers
    batch_numbers = load_batch_numbers()
    print(f"Geladene Batch Numbers: {len(batch_numbers)}")

    # Generate stock entries
    stock_entries = generate_stock_entries(work_orders, bom_data, batch_numbers)
    print(f"Generierte Stock Entries: {len(stock_entries)}")

    # Generate manufacture entries
    manufacture_entries = []
    for se, wo in zip(stock_entries, work_orders):
        manufacture_entry = generate_manufacture_stock_entry(se, wo, bom_data)
        manufacture_entries.append(manufacture_entry)
    print(f"Generierte Manufacture Entries: {len(manufacture_entries)}")

    # Save API payloads
    print("Speichere API Payloads...")
    save_api_payload(stock_entries, manufacture_entries)

    # Process entries
    print("\nBeginne mit dem Upload der Stock Entries...")
    all_entries = []
    successful_uploads = []

    # Process Material Transfer entries
    print("\nVerarbeite Material Transfer Entries...")
    for i, se in enumerate(stock_entries, 1):
        success, content = upload_stock_entry_to_api(se)
        if success:
            se['name'] = content['name']
            successful_uploads.append(se)
            print(f"Stock Entry {i}/{len(stock_entries)} erfolgreich hochgeladen. ID: {content['name']}")
        else:
            print(f"Stock Entry {i}/{len(stock_entries)} fehlgeschlagen.")
        all_entries.append(se)

    print(f"\nWarte 10 Sekunden vor dem Upload der Manufacture Entries...")
    time.sleep(10)

    # Process Manufacture entries
    print("\nVerarbeite Manufacture Entries...")
    for i, me in enumerate(manufacture_entries, 1):
        success, content = upload_stock_entry_to_api(me)
        if success:
            me['name'] = content['name']
            successful_uploads.append(me)
            print(f"Manufacture Entry {i}/{len(manufacture_entries)} erfolgreich hochgeladen. ID: {content['name']}")
        else:
            print(f"Manufacture Entry {i}/{len(manufacture_entries)} fehlgeschlagen.")
        all_entries.append(me)

    # Save results to CSV
    print("\nSpeichere Ergebnisse...")
    save_to_csv(all_entries, 'all_stock_entries.csv')
    save_to_csv(successful_uploads, 'uploaded_stock_entries.csv')

    # Print final summary
    print("\nZusammenfassung:")
    print(f"Gesamt generierte Entries: {len(all_entries)}")
    print(f"Erfolgreich hochgeladene Entries: {len(successful_uploads)}")
    print(f"Fehlgeschlagene Entries: {len(all_entries) - len(successful_uploads)}")
    print("\nDatengenerierung abgeschlossen. Ausgabedateien wurden im Verzeichnis 'generated' gespeichert.")


if __name__ == "__main__":
    main()