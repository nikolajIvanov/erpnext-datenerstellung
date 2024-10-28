from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import time
import uuid
from copy import deepcopy

from src.api.endpoints.stock_entry_api import StockEntryAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (
    COMPANY, TARGET_WAREHOUSE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class StockEntryConfig(BaseConfig):
    """Configuration specific to stock entry process."""

    def __init__(self):
        super().__init__('stock_entries')

        # Process-specific settings
        self.WORK_ORDERS_FILE = 'uploaded_work_orders.csv'
        self.BATCH_NUMBERS_FILE = 'batch_numbers.csv'
        self.BOM_FILES = ['bom_bike.csv', 'bom_ebike.csv']


class StockEntryGenerator:
    """Generator for stock entries in manufacturing process."""

    def __init__(self):
        self.config = StockEntryConfig()
        self.logger = ProcessLogger(self.config)
        self.api = StockEntryAPI()

    def load_csv_data(self, filename: str, directory: Path = OUTPUT_DIR) -> List[Dict]:
        """Load data from CSV file."""
        try:
            filepath = directory / filename
            self.logger.log_info(f"Loading CSV file from: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.log_error(f"Error loading CSV file {filename}: {str(e)}")
            raise

    def load_batch_numbers(self) -> Dict[str, str]:
        """Load batch number mappings."""
        try:
            batch_data = self.load_csv_data(self.config.BATCH_NUMBERS_FILE, MASTER_DATA_DIR / 'base')
            return {batch['Item']: batch['Batch ID'] for batch in batch_data}
        except Exception as e:
            self.logger.log_error(f"Error loading batch numbers: {str(e)}")
            raise

    def load_bom_data(self) -> Dict[str, Dict]:
        """Load BOM data from manufacturing directory."""
        bom_data = {}
        try:
            for filename in self.config.BOM_FILES:
                filepath = MASTER_DATA_DIR / 'manufacturing' / filename
                self.logger.log_info(f"Loading BOM file: {filepath}")

                with open(filepath, 'r', encoding='utf-8') as f:
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
        except Exception as e:
            self.logger.log_error(f"Error loading BOM data: {str(e)}")
            raise

    def generate_stock_entries(self, work_orders: List[Dict], bom_data: Dict[str, Dict],
                               batch_numbers: Dict[str, str]) -> List[Dict]:
        """Generate stock entry documents for material transfer."""
        stock_entries = []
        for wo in work_orders:
            try:
                bom = bom_data[wo['BOM No']]
                posting_date = datetime.now().strftime("%Y-%m-%d")
                posting_time = datetime.now().strftime("%H:%M:%S")

                # Basic mandatory fields
                stock_entry = {
                    "doctype": "Stock Entry",
                    "naming_series": "MAT-STE-.YYYY.-",
                    "company": COMPANY,
                    "stock_entry_type": "Material Transfer for Manufacture",  # This is the correct field name
                    "purpose": "Material Transfer for Manufacture",
                    "posting_date": posting_date,
                    "posting_time": posting_time,
                    "from_warehouse": TARGET_WAREHOUSE,
                    "to_warehouse": TARGET_WAREHOUSE,

                    # Additional fields for manufacturing
                    "from_bom": 1,
                    "use_multi_level_bom": 1,
                    "bom_no": wo['BOM No'],
                    "work_order": wo['ID'],
                    "fg_completed_qty": float(wo['Qty To Manufacture']),
                    "docstatus": 1,
                    "items": []
                }

                total_outgoing_value = 0
                for item in bom['Items']:
                    qty = float(item['Qty (Items)']) * float(wo['Qty To Manufacture'])
                    rate = float(item.get('Rate (Items)', 0))
                    amount = round(qty * rate, 2)
                    total_outgoing_value += amount

                    # Required fields for each item
                    stock_entry["items"].append({
                        "doctype": "Stock Entry Detail",
                        "item_code": item['Item Code (Items)'],
                        "qty": qty,
                        "basic_rate": rate,
                        "basic_amount": amount,
                        "amount": amount,
                        "s_warehouse": TARGET_WAREHOUSE,
                        "t_warehouse": TARGET_WAREHOUSE,
                        "transfer_qty": qty,
                        "conversion_factor": 1.0,
                        "stock_uom": item['UOM (Items)'],
                        "uom": item['UOM (Items)'],
                        "batch_no": batch_numbers.get(item['Item Code (Items)'], ""),
                        # Additional fields
                        "description": f"Component: {item['Item Code (Items)']}",
                        "allow_zero_valuation_rate": 0,
                        "expense_account": "5000 - Manufacturing Cost: Loss - B",
                        "cost_center": "Main - B"
                    })

                stock_entry["total_outgoing_value"] = total_outgoing_value
                stock_entry["total_incoming_value"] = total_outgoing_value
                stock_entry["value_difference"] = 0.0

                stock_entries.append(stock_entry)
                self.logger.log_info(f"Generated stock entry for work order {wo['ID']}")

            except Exception as e:
                self.logger.log_error(
                    f"Error generating stock entry for work order {wo.get('ID', 'unknown')}: {str(e)}")
                continue

        return stock_entries

    def generate_manufacture_entries(self, stock_entries: List[Dict], work_orders: List[Dict],
                                     bom_data: Dict[str, Dict]) -> List[Dict]:
        """Generate manufacture stock entries."""
        manufacture_entries = []
        for se, wo in zip(stock_entries, work_orders):
            try:
                manufacture_entry = deepcopy(se)
                manufacture_entry["stock_entry_type"] = "Manufacture"
                manufacture_entry["purpose"] = "Manufacture"

                # Remove any existing name
                if 'name' in manufacture_entry:
                    del manufacture_entry['name']

                bom = bom_data[wo['BOM No']]

                # Add finished item with all required fields
                finished_item = {
                    "doctype": "Stock Entry Detail",
                    "item_code": bom['Item'],
                    "is_finished_item": 1,
                    "qty": float(wo['Qty To Manufacture']),
                    "transfer_qty": float(wo['Qty To Manufacture']),
                    "conversion_factor": 1.0,
                    "stock_uom": "Nos",
                    "uom": "Nos",
                    "s_warehouse": "",  # Empty for manufactured item
                    "t_warehouse": TARGET_WAREHOUSE,
                    "basic_rate": sum(
                        float(item.get('basic_rate', 0)) * float(item.get('qty', 0))
                        for item in manufacture_entry['items']
                    ),
                    # Additional fields
                    "allow_zero_valuation_rate": 0,
                    "description": f"Manufactured Item: {bom['Item Name']}",
                    "item_name": bom['Item Name'],
                    "expense_account": "5000 - Cost of Goods Sold - B",
                    "cost_center": "Main - B",
                    "bom_no": wo['BOM No']
                }

                # Calculate amounts
                finished_item['basic_amount'] = finished_item['basic_rate'] * finished_item['qty']
                finished_item['amount'] = finished_item['basic_amount']

                # Update source warehouse for components
                for item in manufacture_entry['items']:
                    item['s_warehouse'] = TARGET_WAREHOUSE
                    item['t_warehouse'] = ""  # Empty for consumed items

                # Add finished item to the list
                manufacture_entry['items'].append(finished_item)
                manufacture_entries.append(manufacture_entry)

                self.logger.log_info(f"Generated manufacture entry for work order {wo['ID']}")

            except Exception as e:
                self.logger.log_error(
                    f"Error generating manufacture entry for work order {wo.get('ID', 'unknown')}: {str(e)}")
                continue

        return manufacture_entries

    def upload_stock_entry_to_api(self, stock_entry: Dict) -> Tuple[bool, Dict]:
        """Upload stock entry to API."""
        try:
            response = self.api.create(stock_entry)

            if not response or 'data' not in response:
                return False, {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.logger.log_info(f"Successfully created Stock Entry with ID: {system_id}")
                return True, content

            return False, {}

        except Exception as e:
            self.logger.log_error(f"Failed to upload Stock Entry: {str(e)}")
            return False, {}

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save stock entries to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            self.logger.log_info(f"Successfully saved {len(data)} records to {filename}")

        except Exception as e:
            self.logger.log_error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self):
        """Main process for generating and uploading stock entries."""
        try:
            # Load required data
            work_orders = self.load_csv_data(self.config.WORK_ORDERS_FILE)
            self.logger.log_info(f"Loaded {len(work_orders)} work orders")

            bom_data = self.load_bom_data()
            self.logger.log_info(f"Loaded {len(bom_data)} BOMs")

            batch_numbers = self.load_batch_numbers()
            self.logger.log_info(f"Loaded {len(batch_numbers)} batch numbers")

            # Generate stock entries
            stock_entries = self.generate_stock_entries(work_orders, bom_data, batch_numbers)
            self.logger.log_info(f"Generated {len(stock_entries)} stock entries")

            # Generate manufacture entries
            manufacture_entries = self.generate_manufacture_entries(stock_entries, work_orders, bom_data)
            self.logger.log_info(f"Generated {len(manufacture_entries)} manufacture entries")

            # Process and upload entries
            all_entries = []
            successful_uploads = []

            # Process Material Transfer entries
            for se in stock_entries:
                success, content = self.upload_stock_entry_to_api(se)
                if success:
                    se['name'] = content['name']
                    successful_uploads.append(se)
                all_entries.append(se)

            self.logger.log_info("Waiting 10 seconds before processing manufacture entries...")
            time.sleep(10)

            # Process Manufacture entries
            for me in manufacture_entries:
                success, content = self.upload_stock_entry_to_api(me)
                if success:
                    me['name'] = content['name']
                    successful_uploads.append(me)
                all_entries.append(me)

            # Save results
            self.save_to_csv(all_entries, 'all_stock_entries.csv')
            self.save_to_csv(successful_uploads, 'uploaded_stock_entries.csv')

            self.logger.log_info(f"Process completed. {len(successful_uploads)} out of {len(all_entries)} "
                                 f"entries successfully uploaded")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = StockEntryGenerator()
    generator.process()


if __name__ == "__main__":
    main()