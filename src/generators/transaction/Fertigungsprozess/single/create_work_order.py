from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import random
import logging

from src.api.endpoints.work_order_api import WorkOrderAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (COMPANY, TARGET_WAREHOUSE, MASTER_DATA_DIR, OUTPUT_DIR)


class WorkOrderConfig(BaseConfig):
    """Configuration specific to work order process."""

    def __init__(self):
        super().__init__('work_orders')

        # Process-specific settings
        self.START_DATE = datetime.now() - timedelta(days=5 * 365)
        self.END_DATE = datetime.now()
        self.NUM_ORDERS = 5
        self.BOM_FILES = ['bom_bike.csv', 'bom_ebike.csv']


class WorkOrderGenerator:
    def __init__(self):
        self.config = WorkOrderConfig()
        self.logger = ProcessLogger(self.config)
        self.api = WorkOrderAPI()

    def upload_work_order_to_api(self, work_order: Dict) -> Tuple[bool, str, Dict]:
        """Upload work order to API with improved error handling."""
        try:
            response = self.api.create(work_order)

            if not response or 'data' not in response:
                return False, "", {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.logger.log_info(f"Successfully created Work Order with ID: {system_id}")
                return True, system_id, content

            return False, "", {}

        except Exception as e:
            self.logger.log_error(f"Failed to upload Work Order: {str(e)}")
            return False, "", {}

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

    def random_date(self) -> datetime:
        """Generate random date between start and end date."""
        if not all([self.config.START_DATE, self.config.END_DATE]):
            raise ValueError("Date range not configured")

        time_between = self.config.END_DATE - self.config.START_DATE
        days_between = time_between.days
        random_days = random.randint(0, max(0, days_between))
        return self.config.START_DATE + timedelta(days=random_days)

    def generate_work_orders(self, bom_data: Dict[str, Dict]) -> List[Dict]:
        """Generate work order documents."""
        work_orders = []
        for _ in range(self.config.NUM_ORDERS):
            try:
                wo_date = self.random_date()
                bom_id, bom = random.choice(list(bom_data.items()))

                work_order = {
                    "doctype": "Work Order",
                    "naming_series": "MFG-WO-.YYYY.-",
                    "company": COMPANY,
                    "bom_no": bom_id,
                    "production_item": bom['Item'],
                    "qty": random.randint(1, 10),
                    "planned_start_date": wo_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Not Started",
                    "has_batch_no": 0,
                    "has_serial_no": 1,
                    "wip_warehouse": TARGET_WAREHOUSE,
                    "source_warehouse": TARGET_WAREHOUSE,
                    "fg_warehouse": TARGET_WAREHOUSE,
                    "docstatus": 1
                }
                work_orders.append(work_order)

            except Exception as e:
                self.logger.log_error(f"Error generating work order: {str(e)}")
                continue

        return work_orders

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save work orders to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename
            fieldnames = [
                "ID", "BOM No", "Company", "Item To Manufacture", "Planned Start Date",
                "Qty To Manufacture", "Series", "Status", "Has Batch No", "Has Serial No",
                "Work-in-Progress Warehouse", "Source Warehouse", "Target Warehouse"
            ]

            rows = []
            for wo in data:
                row = {
                    "ID": wo.get('name', ''),
                    "BOM No": wo['bom_no'],
                    "Company": wo['company'],
                    "Item To Manufacture": wo['production_item'],
                    "Planned Start Date": wo['planned_start_date'],
                    "Qty To Manufacture": wo['qty'],
                    "Series": wo['naming_series'],
                    "Status": wo['status'],
                    "Has Batch No": wo['has_batch_no'],
                    "Has Serial No": wo['has_serial_no'],
                    "Work-in-Progress Warehouse": wo['wip_warehouse'],
                    "Source Warehouse": wo['source_warehouse'],
                    "Target Warehouse": wo['fg_warehouse']
                }
                rows.append(row)

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            self.logger.log_info(f"Successfully saved {len(rows)} records to {filename}")

        except Exception as e:
            self.logger.log_error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self):
        """Main process for generating and uploading work orders."""
        try:
            # Load BOM data
            bom_data = self.load_bom_data()
            self.logger.log_info(f"Loaded {len(bom_data)} BOMs")

            # Generate work orders
            work_orders = self.generate_work_orders(bom_data)
            self.logger.log_info(f"Generated {len(work_orders)} work orders")

            # Upload and track successful uploads
            successful_uploads = []
            for wo in work_orders:
                success, system_id, response_data = self.upload_work_order_to_api(wo)
                if success:
                    wo['name'] = system_id
                    wo['status'] = response_data.get('status', '')
                    successful_uploads.append(wo)

            # Save results
            if successful_uploads:
                self.save_to_csv(successful_uploads, 'uploaded_work_orders.csv')
            else:
                self.logger.log_warning("No successful uploads to save to CSV.")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = WorkOrderGenerator()
    generator.process()


if __name__ == "__main__":
    main()
