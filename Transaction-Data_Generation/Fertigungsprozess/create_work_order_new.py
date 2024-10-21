import csv
import os
import random
from datetime import datetime, timedelta
import logging
import json
from typing import List, Dict, Tuple
from api.work_order_api import WorkOrderAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2023, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    PRODUCTION_WAREHOUSE = "Lager Stuttgart - B"
    FINISHED_GOODS_WAREHOUSE = "Lager Stuttgart - B"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_bom_data() -> Dict[str, Dict]:
    bom_data = {}
    for filename in ['bom_bike.csv', 'bom_ebike.csv']:
        with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
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


def generate_work_orders(num_orders: int, bom_data: Dict[str, Dict]) -> List[Dict]:
    work_orders = []
    for _ in range(num_orders):
        wo_date = random_date(Config.START_DATE, Config.END_DATE)
        bom_id, bom = random.choice(list(bom_data.items()))
        work_order = {
            "BOM No": bom_id,
            "Company": "Velo GmbH",
            "Item To Manufacture": bom['Item'],
            "Planned Start Date": wo_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Qty To Manufacture": random.randint(1, 10),
            "Series": "MFG-WO-.YYYY.-",
            "Status": "Not Started",
            "Has Batch No": 0,
            "Has Serial No": 1,
            "Work-in-Progress Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Source Warehouse": Config.PRODUCTION_WAREHOUSE,
            "Target Warehouse": Config.FINISHED_GOODS_WAREHOUSE,
            "docstatus": 1  # 0 = Draft; 1 = Submitted
        }
        work_orders.append(work_order)
    return work_orders


def map_csv_to_api_fields(work_order: Dict) -> Dict:
    field_mapping = {
        "BOM No": "bom_no",
        "Company": "company",
        "Item To Manufacture": "production_item",
        "Planned Start Date": "planned_start_date",
        "Qty To Manufacture": "qty",
        "Series": "naming_series",
        "Status": "status",
        "Has Batch No": "has_batch_no",
        "Has Serial No": "has_serial_no",
        "Work-in-Progress Warehouse": "wip_warehouse",
        "Source Warehouse": "source_warehouse",
        "Target Warehouse": "fg_warehouse",
        "docstatus": "docstatus"
    }
    return {field_mapping.get(k, k): v for k, v in work_order.items()}


def upload_work_order_to_api(work_order: Dict) -> Tuple[bool, str, Dict]:
    api = WorkOrderAPI()
    mapped_work_order = map_csv_to_api_fields(work_order)
    try:
        response = api.create(mapped_work_order)
        content = response['data']
        # data = json.loads(content)

        if 'name' in content:
            system_id = content['name']
            logging.info(f"Successfully uploaded Work Order. ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        logging.error(f"Failed to upload Work Order: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    fieldnames = data[0].keys() if data else []
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logging.info(f"Saved {len(data)} records to {filename}")


def main(num_work_orders: int):
    bom_data = load_bom_data()
    logging.info(f"Loaded {len(bom_data)} BOMs")

    work_orders = generate_work_orders(num_work_orders, bom_data)
    logging.info(f"Generated {len(work_orders)} work orders")

    successful_uploads = []
    for wo in work_orders:
        success, system_id, response_data = upload_work_order_to_api(wo)
        if success:
            wo['ID'] = system_id
            wo['Status'] = response_data.get('status', '')
            wo['Actual Qty'] = response_data.get('qty', 0)
            wo['Planned Start Date'] = response_data.get('planned_start_date', '')
            successful_uploads.append(wo)
        else:
            logging.error(f"Failed to upload work order: {wo}")

    # Save successfully uploaded work orders to a separate CSV
    save_to_csv(successful_uploads, 'uploaded_work_orders.csv')

    logging.info(f"Successfully uploaded {len(successful_uploads)} out of {len(work_orders)} work orders")


if __name__ == "__main__":
    main(num_work_orders=100)
