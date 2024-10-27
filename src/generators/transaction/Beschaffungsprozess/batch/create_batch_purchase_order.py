# src/generators/transaction/Beschaffungsprozess/batch/create_batch_purchase_order.py

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import random
import logging

from src.api.endpoints.purchase_order_api import PurchaseOrderAPI
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE, TARGET_WAREHOUSE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class BatchPurchaseOrderGenerator:
    """Generator for purchase orders in batch mode, controlled by master controller."""

    def __init__(self):
        self.logger = logging.getLogger('BatchPurchaseOrderGenerator')
        self.api = PurchaseOrderAPI()
        self.start_date = None
        self.end_date = None
        self.num_orders = None
        self._initialize_logging()

        # Store successful orders in memory
        self.successful_orders = []

    def _initialize_logging(self):
        """Initialize logging configuration"""
        self.logger = logging.getLogger(self.__class__.__name__)

        # Clear any existing handlers
        self.logger.handlers = []

        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        log_dir = OUTPUT_DIR / 'logs' / f'batch_{self.__class__.__name__.lower()}'
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f'batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def configure(self, start_date: datetime, end_date: datetime, num_orders: int):
        """Configure the generator with parameters from master controller"""
        self.start_date = start_date
        self.end_date = end_date
        self.num_orders = num_orders
        self.logger.info(f"Configured batch generator for period: {start_date.date()} to {end_date.date()}, "
                         f"generating {num_orders} orders")

    def load_master_data(self) -> Tuple[List[Dict], Dict[str, str]]:
        """Load all required master data"""
        try:
            # Load products and filter components
            products = self.load_csv_data('items.csv')
            components = [p for p in products if p['Item Group'] == 'Fahrradkomponenten']

            # Load supplier mapping
            mapping = {}
            mapping_file = MASTER_DATA_DIR / 'mappings' / 'item_supplier_mapping.csv'
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        mapping[row['Item Code']] = row['Supplier ID']

            return components, mapping
        except Exception as e:
            self.logger.error(f"Error loading master data: {str(e)}")
            raise

    def load_csv_data(self, filename: str) -> List[Dict]:
        """Load data from a CSV file"""
        try:
            filepath = MASTER_DATA_DIR / 'base' / filename
            self.logger.debug(f"Loading CSV file: {filepath}")

            if not filepath.exists():
                raise FileNotFoundError(f"File not found: {filepath}")

            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.error(f"Error loading CSV file {filename}: {str(e)}")
            raise

    def random_date(self) -> datetime:
        """Generate a random date within the configured date range"""
        if not all([self.start_date, self.end_date]):
            raise ValueError("Date range not configured")

        time_between = self.end_date - self.start_date
        days_between = time_between.days
        random_days = random.randint(0, max(0, days_between))
        return self.start_date + timedelta(days=random_days)

    def create_purchase_order(self, product: Dict, supplier_id: str, po_date: datetime) -> Dict:
        """Create a single purchase order document"""
        quantity = 500  # Fixed quantity for now, could be made variable
        rate = float(product['Valuation Rate'])
        net_amount = round(quantity * rate, 2)
        tax_rate = 19.0
        tax_amount = round(net_amount * (tax_rate / 100), 2)
        gross_amount = net_amount + tax_amount

        return {
            "doctype": "Purchase Order",
            "naming_series": "PUR-ORD-.YYYY.-",
            "company": COMPANY,
            "currency": CURRENCY,
            "transaction_date": po_date.strftime("%Y-%m-%d"),
            "schedule_date": (po_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            "conversion_rate": CONVERSION_RATE,
            "supplier": supplier_id,
            "supplier_name": f"Purchase Order for {supplier_id}",
            "items": [{
                "item_code": product['Item Code'],
                "item_name": product['Item Name'],
                "description": product.get('Description', ''),
                "qty": quantity,
                "rate": rate,
                "amount": net_amount,
                "uom": product['Default Unit of Measure'],
                "stock_uom": product['Default Unit of Measure'],
                "conversion_factor": 1.0,
                "warehouse": TARGET_WAREHOUSE
            }],
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                "description": "Abziehbare Vorsteuer 19 %",
                "rate": tax_rate
            }],
            "total_taxes_and_charges": tax_amount,
            "grand_total": gross_amount,
            "rounded_total": round(gross_amount),
            "status": "Draft",
            "docstatus": 1
        }

    def generate_and_upload(self) -> List[Dict]:
        """Generate and upload purchase orders in batch"""
        if not all([self.start_date, self.end_date, self.num_orders]):
            raise ValueError("Generator not configured. Call configure() first.")

        self.successful_orders = []  # Reset successful orders
        try:
            components, supplier_mapping = self.load_master_data()

            if not components:
                raise ValueError("No components found to generate purchase orders")

            for i in range(self.num_orders):
                try:
                    product = random.choice(components)
                    supplier_id = supplier_mapping.get(product['Item Code'])

                    if not supplier_id:
                        self.logger.warning(f"No supplier found for item {product['Item Code']}, skipping...")
                        continue

                    po_date = self.random_date()
                    po_doc = self.create_purchase_order(product, supplier_id, po_date)

                    response = self.api.create(po_doc)

                    if response and 'data' in response:
                        content = response['data']
                        if 'name' in content:
                            po_doc['name'] = content['name']
                            po_doc['api_response'] = content  # Store complete API response
                            if 'items' in content:
                                for idx, item in enumerate(po_doc['items']):
                                    item['name'] = content['items'][idx]['name']
                            self.successful_orders.append(po_doc)
                            self.logger.info(f"Successfully created PO {content['name']} ({i + 1}/{self.num_orders})")

                except Exception as e:
                    self.logger.error(f"Error processing order {i + 1}: {str(e)}")
                    continue

            self.logger.info(f"Completed batch with {len(self.successful_orders)} successful uploads "
                             f"out of {self.num_orders} attempts")
            return self.successful_orders

        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            raise

    def get_successful_orders(self) -> List[Dict]:
        """Return the list of successful orders for next process step"""
        return self.successful_orders

    def save_to_csv(self, filename: str = 'batch_purchase_orders.csv'):
        """Save batch results to CSV"""
        if not self.successful_orders:
            self.logger.warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename

            rows = []
            for po in self.successful_orders:
                for item in po['items']:
                    row = {
                        "ID": po['name'],
                        "Company": po['company'],
                        "Currency": po['currency'],
                        "Date": po['transaction_date'],
                        "Exchange Rate": "1,00",
                        "Series": po['naming_series'],
                        "Status": po['status'],
                        "Supplier": po['supplier'],
                        "Title": po['supplier_name'],
                        "ID (Items)": item.get('name', ''),
                        "Amount (Items)": item['amount'],
                        "Item Code (Items)": item['item_code'],
                        "Item Name (Items)": item['item_name'],
                        "Quantity (Items)": item['qty'],
                        "Rate (Items)": item['rate'],
                        "Required By (Items)": po['schedule_date'],
                        "Stock UOM (Items)": item['stock_uom'],
                        "UOM (Items)": item['uom'],
                        "UOM Conversion Factor (Items)": item['conversion_factor'],
                        "Set Target Warehouse": item['warehouse'],
                        "Net Total": f"{item['amount']:.2f}".replace('.', ','),
                        "Total Taxes and Charges": f"{po['total_taxes_and_charges']:.2f}".replace('.', ','),
                        "Grand Total": f"{po['grand_total']:.2f}".replace('.', ','),
                        "Rounded Total": f"{po['rounded_total']:.2f}".replace('.', ','),
                    }
                    rows.append(row)

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            self.logger.info(f"Successfully saved {len(rows)} records to {filename}")

        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self) -> bool:
        """Main batch processing method called by master controller"""
        try:
            self.logger.info(f"Starting batch purchase order process for period: "
                             f"{self.start_date.date()} to {self.end_date.date()}")

            # Generate and upload orders
            self.generate_and_upload()

            # Save results if any successful uploads
            if self.successful_orders:
                self.save_to_csv()
                return True
            else:
                self.logger.warning("No successful orders to save.")
                return False

        except Exception as e:
            self.logger.error(f"Batch process failed: {str(e)}")
            return False
