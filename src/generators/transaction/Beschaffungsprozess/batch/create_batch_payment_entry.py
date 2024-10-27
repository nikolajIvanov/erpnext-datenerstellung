# src/generators/transaction/Beschaffungsprozess/batch/create_batch_payment_entry.py

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import random
import logging

from src.api.endpoints.payment_entry_api import PaymentEntryAPI
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE,
    MASTER_DATA_DIR, OUTPUT_DIR
)


class BatchPaymentEntryGenerator:
    """Generator for payment entries in batch mode, controlled by master controller."""

    def __init__(self):
        self.logger = logging.getLogger('BatchPaymentEntryGenerator')
        self.api = PaymentEntryAPI()
        self.start_date = None
        self.end_date = None
        self.purchase_invoices = None
        self._initialize_logging()

        # Store successful payments in memory
        self.successful_payments = []

        # Payment specific configurations
        self.PAYMENT_DELAY_MIN = 0  # Minimum days after invoice
        self.PAYMENT_DELAY_MAX = 30  # Maximum days after invoice

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

    def configure(self, start_date: datetime, end_date: datetime, purchase_invoices: List[Dict]):
        """Configure the generator with parameters and purchase invoices from master controller"""
        self.start_date = start_date
        self.end_date = end_date
        self.purchase_invoices = purchase_invoices
        self.logger.info(f"Configured batch generator for period: {start_date.date()} to {end_date.date()}, "
                         f"processing {len(purchase_invoices)} purchase invoices")

    def calculate_payment_date(self, invoice_date: str, due_date: str) -> datetime:
        """Calculate payment date based on invoice date and due date"""
        base_date = datetime.strptime(invoice_date, "%Y-%m-%d")
        max_date = min(
            datetime.strptime(due_date, "%Y-%m-%d"),
            base_date + timedelta(days=self.PAYMENT_DELAY_MAX)
        )

        delay_days = random.randint(self.PAYMENT_DELAY_MIN,
                                    (max_date - base_date).days)
        payment_date = base_date + timedelta(days=delay_days)

        # Ensure payment date is within configured period
        if payment_date > self.end_date:
            payment_date = self.end_date

        return payment_date

    def create_payment_entry(self, pi: Dict, payment_date: datetime) -> Dict:
        """Create a single payment entry document from purchase invoice"""
        # Calculate total amount including taxes
        tax_amount = float(pi['taxes'][0]['tax_amount'])
        total_amount = float(pi['items'][0]['amount']) + tax_amount

        payment = {
            "doctype": "Payment Entry",
            "naming_series": "ACC-PAY-.YYYY.-",
            "payment_type": "Pay",
            "payment_order_status": "Initiated",
            "posting_date": payment_date.strftime("%Y-%m-%d"),
            "company": COMPANY,
            "party_type": "Supplier",
            "party": pi['supplier'],
            "party_name": pi['supplier'],
            "paid_from": "Bank Account - B",
            "paid_to": pi['credit_to'],
            "paid_amount": total_amount,
            "paid_amount_after_tax": total_amount,
            "source_exchange_rate": CONVERSION_RATE,
            "base_paid_amount": total_amount,
            "base_paid_amount_after_tax": total_amount,
            "received_amount": total_amount,
            "received_amount_after_tax": total_amount,
            "target_exchange_rate": CONVERSION_RATE,
            "base_received_amount": total_amount,
            "base_received_amount_after_tax": total_amount,
            "paid_to_account_currency": CURRENCY,
            "paid_from_account_currency": CURRENCY,
            "reference_no": f"REF-{payment_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "reference_date": payment_date.strftime("%Y-%m-%d"),
            "references": [{
                "reference_doctype": "Purchase Invoice",
                "reference_name": pi['name'],
                "total_amount": total_amount,
                "allocated_amount": total_amount,
                "exchange_rate": CONVERSION_RATE
            }],
            "taxes": [{
                "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                "add_deduct_tax": "Add",
                "category": "Total",
                "charge_type": "Actual",
                "description": "Abziehbare Vorsteuer 19 %",
                "rate": float(pi['taxes'][0]['rate']),
                "tax_amount": tax_amount,
                "total": total_amount
            }],
            "base_total_taxes_and_charges": tax_amount,
            "total_taxes_and_charges": tax_amount,
            "docstatus": 1
        }

        # Add reference to original documents
        payment['purchase_invoice_reference'] = pi['name']
        if 'purchase_receipt_reference' in pi:
            payment['purchase_receipt_reference'] = pi['purchase_receipt_reference']

        return payment

    def generate_and_upload(self) -> List[Dict]:
        """Generate and upload payment entries in batch"""
        if not all([self.start_date, self.end_date, self.purchase_invoices]):
            raise ValueError("Generator not configured. Call configure() first.")

        self.successful_payments = []  # Reset successful payments
        try:
            if not self.purchase_invoices:
                raise ValueError("No purchase invoices provided to process")

            # Generate and upload payments
            for i, pi in enumerate(self.purchase_invoices, 1):
                try:
                    payment_date = self.calculate_payment_date(pi['posting_date'], pi['due_date'])
                    payment_doc = self.create_payment_entry(pi, payment_date)

                    response = self.api.create(payment_doc)

                    if response and 'data' in response:
                        content = response['data']
                        if 'name' in content:
                            payment_doc['name'] = content['name']
                            payment_doc['api_response'] = content  # Store complete API response
                            self.successful_payments.append(payment_doc)
                            self.logger.info(
                                f"Successfully created Payment Entry {content['name']} "
                                f"({i}/{len(self.purchase_invoices)})")

                except Exception as e:
                    self.logger.error(f"Error processing payment {i}: {str(e)}")
                    continue

            self.logger.info(f"Completed batch with {len(self.successful_payments)} successful uploads "
                             f"out of {len(self.purchase_invoices)} attempts")
            return self.successful_payments

        except Exception as e:
            self.logger.error(f"Batch processing error: {str(e)}")
            raise

    def get_successful_payments(self) -> List[Dict]:
        """Return the list of successful payments"""
        return self.successful_payments

    def save_to_csv(self, filename: str = 'batch_payment_entries.csv'):
        """Save batch results to CSV"""
        if not self.successful_payments:
            self.logger.warning("No data to save to CSV.")
            return

        try:
            output_path = OUTPUT_DIR / filename

            rows = []
            for pe in self.successful_payments:
                row = {
                    "ID": pe['name'],
                    "Account Currency (From)": pe['paid_from_account_currency'],
                    "Account Currency (To)": pe['paid_to_account_currency'],
                    "Account Paid From": pe['paid_from'],
                    "Account Paid To": pe['paid_to'],
                    "Company": pe['company'],
                    "Paid Amount": f"{pe['paid_amount']:.2f}".replace('.', ','),
                    "Paid Amount (Company Currency)": f"{pe['base_paid_amount']:.2f}".replace('.', ','),
                    "Payment Type": pe['payment_type'],
                    "Posting Date": pe['posting_date'],
                    "Received Amount": f"{pe['received_amount']:.2f}".replace('.', ','),
                    "Received Amount (Company Currency)": f"{pe['base_received_amount']:.2f}".replace('.', ','),
                    "Series": pe['naming_series'],
                    "Source Exchange Rate": f"{pe['source_exchange_rate']:.2f}".replace('.', ','),
                    "Target Exchange Rate": f"{pe['target_exchange_rate']:.2f}".replace('.', ','),
                    "ID (Payment References)": pe['references'][0].get('name', ''),
                    "Type (Payment References)": pe['references'][0]['reference_doctype'],
                    "Name (Payment References)": pe['references'][0]['reference_name'],
                    "ID (Advance Taxes and Charges)": f"ADTAX-{pe['name']}",
                    "Account Head (Advance Taxes and Charges)": pe['taxes'][0]['account_head'],
                    "Add Or Deduct (Advance Taxes and Charges)": pe['taxes'][0]['add_deduct_tax'],
                    "Description (Advance Taxes and Charges)": pe['taxes'][0]['description'],
                    "Party Type": pe['party_type'],
                    "Party": pe['party'],
                    "Cheque/Reference Date": pe['reference_date'],
                    "Cheque/Reference No": pe['reference_no'],
                    "Type (Advance Taxes and Charges)": pe['taxes'][0]['charge_type']
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
            self.logger.info(f"Starting batch payment entry process for period: "
                             f"{self.start_date.date()} to {self.end_date.date()}")

            # Generate and upload payments
            self.generate_and_upload()

            # Save results if any successful uploads
            if self.successful_payments:
                self.save_to_csv()
                return True
            else:
                self.logger.warning("No successful payments to save.")
                return False

        except Exception as e:
            self.logger.error(f"Batch process failed: {str(e)}")
            return False