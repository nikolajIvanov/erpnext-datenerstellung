import csv
from datetime import datetime, timedelta
import random
from typing import List, Dict, Tuple
from src.api.endpoints.payment_entry_api import PaymentEntryAPI
from src.core.base_transaction import BaseConfig
from src.core.logging import ProcessLogger
from src.config.settings import (
    COMPANY, CURRENCY, CONVERSION_RATE,
    OUTPUT_DIR
)


class PaymentEntryConfig(BaseConfig):
    """Configuration specific to payment entry process."""

    def __init__(self):
        super().__init__('payment_entry')

        # Process-specific settings
        self.PAYMENT_DELAY = (0, 30)  # Payment 0-30 days after invoice


class PaymentEntryGenerator:
    def __init__(self):
        self.config = PaymentEntryConfig()
        self.logger = ProcessLogger(self.config)
        self.api = PaymentEntryAPI()
        self.original_data = {}  # Store original data with generated IDs

    def upload_payment_entry_to_api(self, payment_entry: Dict) -> Tuple[bool, str, Dict]:
        """Upload payment entry to API with improved error handling."""
        try:
            response = self.api.create(payment_entry)

            if not response or 'data' not in response:
                return False, "", {}

            content = response['data']

            if isinstance(content, dict) and 'name' in content:
                system_id = content['name']
                self.original_data[system_id] = payment_entry  # Store original data
                self.logger.log_info(f"Successfully created Payment Entry with ID: {system_id}")
                return True, system_id, content

            return False, "", {}

        except Exception as e:
            self.logger.log_error(f"Failed to upload Payment Entry: {str(e)}")
            return False, "", {}

    def load_csv_data(self, filename: str) -> List[Dict]:
        """Load data from a CSV file."""
        try:
            filepath = OUTPUT_DIR / filename
            self.logger.log_info(f"Loading CSV file from: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.logger.log_error(f"Error loading CSV file {filename}: {str(e)}")
            raise

    def generate_payment_entries(self, purchase_invoices: List[Dict]) -> List[Dict]:
        """Generate payment entry documents."""
        payment_entries = []
        for pi in purchase_invoices:
            try:
                pi_date = datetime.strptime(pi['Date'], "%Y-%m-%d")
                payment_date = pi_date + timedelta(days=random.randint(*self.config.PAYMENT_DELAY))

                # Convert amount string to float
                if isinstance(pi['Amount (Company Currency) (Items)'], str):
                    amount = float(pi['Amount (Company Currency) (Items)'].replace(',', '.'))
                else:
                    amount = float(pi['Amount (Company Currency) (Items)'])

                # Calculate tax amount
                tax_rate = 19.0
                tax_amount = amount * (tax_rate / 100)
                total_amount = amount + tax_amount

                payment = {
                    "doctype": "Payment Entry",
                    "naming_series": "ACC-PAY-.YYYY.-",
                    "payment_type": "Pay",
                    "payment_order_status": "Initiated",
                    "posting_date": payment_date.strftime("%Y-%m-%d"),
                    "company": COMPANY,
                    "party_type": "Supplier",
                    "party": pi['Supplier'],
                    "party_name": pi['Supplier'],
                    "paid_from": "Bank Account - B",
                    "paid_to": "3500 - Sonstige Verb. - B",
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
                    "reference_no": str(random.randint(1, 1000)),
                    "reference_date": payment_date.strftime("%Y-%m-%d"),
                    "references": [{
                        "reference_doctype": "Purchase Invoice",
                        "reference_name": pi['ID'],
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
                        "rate": tax_rate,
                        "tax_amount": tax_amount,
                        "total": total_amount
                    }],
                    "base_total_taxes_and_charges": tax_amount,
                    "total_taxes_and_charges": tax_amount,
                    "docstatus": 1
                }
                payment_entries.append(payment)

            except Exception as e:
                self.logger.log_error(f"Error generating payment entry for invoice {pi.get('ID', 'unknown')}: {str(e)}")
                continue

        return payment_entries

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save payment entries to CSV file."""
        if not data:
            self.logger.log_warning("No data to save to CSV.")
            return

        try:
            fieldnames = [
                "ID", "Account Currency (From)", "Account Currency (To)",
                "Account Paid From", "Account Paid To", "Company",
                "Paid Amount", "Paid Amount (Company Currency)",
                "Payment Type", "Posting Date",
                "Received Amount", "Received Amount (Company Currency)",
                "Series", "Source Exchange Rate", "Target Exchange Rate",
                "ID (Payment References)", "Type (Payment References)",
                "Name (Payment References)",
                "ID (Advance Taxes and Charges)",
                "Account Head (Advance Taxes and Charges)",
                "Add Or Deduct (Advance Taxes and Charges)",
                "Description (Advance Taxes and Charges)",
                "Party Type", "Party",
                "Cheque/Reference Date", "Cheque/Reference No",
                "Type (Advance Taxes and Charges)"
            ]

            flattened_data = []
            for uploaded_pe in data:
                pe_id = uploaded_pe.get('name')
                original_pe = self.original_data.get(pe_id)

                if not original_pe:
                    self.logger.log_warning(f"No original data found for uploaded PE: {pe_id}")
                    continue

                try:
                    reference = original_pe['references'][0]
                    tax = original_pe['taxes'][0] if original_pe.get('taxes') else {
                        'name': '',
                        'account_head': "1406 - Abziehbare Vorsteuer 19 % - B",
                        'add_deduct_tax': "Add",
                        'description': "Abziehbare Vorsteuer 19 %",
                        'charge_type': "Actual"
                    }

                    row = {
                        "ID": pe_id,
                        "Account Currency (From)": original_pe['paid_from_account_currency'],
                        "Account Currency (To)": original_pe['paid_to_account_currency'],
                        "Account Paid From": original_pe['paid_from'],
                        "Account Paid To": original_pe['paid_to'],
                        "Company": original_pe['company'],
                        "Paid Amount": f"{original_pe['paid_amount']:.2f}".replace('.', ','),
                        "Paid Amount (Company Currency)": f"{original_pe['base_paid_amount']:.2f}".replace('.', ','),
                        "Payment Type": original_pe['payment_type'],
                        "Posting Date": original_pe['posting_date'],
                        "Received Amount": f"{original_pe['received_amount']:.2f}".replace('.', ','),
                        "Received Amount (Company Currency)": f"{original_pe['base_received_amount']:.2f}".replace('.',
                                                                                                                   ','),
                        "Series": original_pe['naming_series'],
                        "Source Exchange Rate": f"{original_pe['source_exchange_rate']:.2f}".replace('.', ','),
                        "Target Exchange Rate": f"{original_pe['target_exchange_rate']:.2f}".replace('.', ','),
                        "ID (Payment References)": reference.get('name', ''),
                        "Type (Payment References)": reference['reference_doctype'],
                        "Name (Payment References)": reference['reference_name'],
                        "ID (Advance Taxes and Charges)": tax.get('name', ''),
                        "Account Head (Advance Taxes and Charges)": tax['account_head'],
                        "Add Or Deduct (Advance Taxes and Charges)": tax['add_deduct_tax'],
                        "Description (Advance Taxes and Charges)": tax['description'],
                        "Party Type": original_pe['party_type'],
                        "Party": original_pe['party'],
                        "Cheque/Reference Date": original_pe['reference_date'],
                        "Cheque/Reference No": original_pe['reference_no'],
                        "Type (Advance Taxes and Charges)": tax['charge_type']
                    }
                    flattened_data.append(row)
                except KeyError as e:
                    self.logger.log_error(f"Missing key while flattening data for PE {pe_id}: {str(e)}")
                    continue
                except Exception as e:
                    self.logger.log_error(f"Error processing PE {pe_id}: {str(e)}")
                    continue

            output_path = OUTPUT_DIR / filename

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)

            self.logger.log_info(f"Successfully saved {len(flattened_data)} records to {filename}")

        except Exception as e:
            self.logger.log_error(f"Error saving to CSV: {str(e)}")
            raise

    def process(self):
        """Main process for generating and uploading payment entries."""
        try:
            # Load and prepare data
            purchase_invoices = self.load_csv_data('purchase_invoices.csv')
            self.logger.log_info(f"Loaded {len(purchase_invoices)} purchase invoices")

            # Generate payment entries
            payment_entries = self.generate_payment_entries(purchase_invoices)
            self.logger.log_info(f"Generated {len(payment_entries)} payment entries")

            # Upload and track successful uploads
            successful_uploads = []
            for pe in payment_entries:
                success, system_id, response_data = self.upload_payment_entry_to_api(pe)
                if success:
                    response_data['name'] = system_id
                    successful_uploads.append(response_data)

            # Save results
            if successful_uploads:
                self.save_to_csv(successful_uploads, 'payment_entries.csv')
            else:
                self.logger.log_warning("No successful uploads to save to CSV.")

        except Exception as e:
            self.logger.log_error(f"Process Error: {str(e)}")
            raise


def main():
    generator = PaymentEntryGenerator()
    generator.process()


if __name__ == "__main__":
    main()
