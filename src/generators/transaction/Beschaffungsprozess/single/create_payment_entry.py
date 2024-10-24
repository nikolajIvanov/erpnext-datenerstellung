import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict, Tuple
from src.api.endpoints.payment_entry_api import PaymentEntryAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'generated')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'generated')
    LOG_DIR = os.path.join(BASE_DIR, 'process_logs', 'payment_entries')
    PAYMENT_DELAY = (0, 30)  # Payment 0-30 days after invoice


# Create process_logs directory if it doesn't exist
os.makedirs(Config.LOG_DIR, exist_ok=True)

# Configure file logger
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, f'payment_entry_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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


def load_purchase_invoices() -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, 'purchase_invoices.csv'), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_payment_entries(purchase_invoices: List[Dict]) -> List[Dict]:
    payment_entries = []
    for pi in purchase_invoices:
        pi_date = datetime.strptime(pi['Date'], "%Y-%m-%d")
        payment_date = pi_date + timedelta(days=random.randint(*Config.PAYMENT_DELAY))

        # Convert amount string to float
        if isinstance(pi['Amount (Company Currency) (Items)'], str):
            amount = float(pi['Amount (Company Currency) (Items)'].replace(',', '.'))
        else:
            amount = float(pi['Amount (Company Currency) (Items)'])

        payment = {
            "doctype": "Payment Entry",
            "naming_series": "ACC-PAY-.YYYY.-",
            "payment_type": "Pay",
            "posting_date": payment_date.strftime("%Y-%m-%d"),
            "company": "Velo GmbH",
            "party_type": "Supplier",
            "party": pi['Supplier'],
            "party_name": pi['Supplier'],
            "paid_from": "1800 - Bank - B",
            "paid_to": "3500 - Sonstige Verb. - B",
            "paid_amount": amount,
            "source_exchange_rate": 1.0,
            "target_exchange_rate": 1.0,
            "paid_to_account_currency": "EUR",
            "paid_from_account_currency": "EUR",
            "references": [{
                "reference_doctype": "Purchase Invoice",
                "reference_name": pi['ID'],
                "total_amount": amount,
                "allocated_amount": amount
            }],
            "taxes": [{
                "account_head": "1406 - Abziehbare Vorsteuer 19 % - B",
                "add_deduct_tax": "Add",
                "category": "Total",
                "charge_type": "Actual",
                "description": "Abziehbare Vorsteuer 19 %"
            }],
            "docstatus": 1
        }
        payment_entries.append(payment)
    return payment_entries


def upload_payment_entry_to_api(payment_entry: Dict) -> Tuple[bool, str, Dict]:
    api = PaymentEntryAPI()
    try:
        response = api.create(payment_entry)
        content = response['data']

        if 'name' in content:
            system_id = content['name']
            console_logger.info(f"Successfully uploaded Payment Entry. ID: {system_id}")
            file_logger.info(f"Successfully created Payment Entry with ID: {system_id}")
            return True, system_id, content
        else:
            raise ValueError("API response did not contain expected data structure")
    except Exception as e:
        file_logger.error(f"Failed to upload Payment Entry: {str(e)}")
        return False, "", {}


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        file_logger.warning("No data to save to CSV.")
        return

    flattened_data = []
    for pe in data:
        reference = pe['references'][0]
        row = {
            "ID": pe['name'],
            "Account Currency (From)": pe['paid_from_account_currency'],
            "Account Currency (To)": pe['paid_to_account_currency'],
            "Account Paid From": pe['paid_from'],
            "Account Paid To": pe['paid_to'],
            "Company": pe['company'],
            "Paid Amount": f"{pe['paid_amount']:.2f}".replace('.', ','),
            "Paid Amount (Company Currency)": f"{pe['paid_amount']:.2f}".replace('.', ','),
            "Payment Type": pe['payment_type'],
            "Posting Date": pe['posting_date'],
            "Received Amount": f"{pe['paid_amount']:.2f}".replace('.', ','),
            "Received Amount (Company Currency)": f"{pe['paid_amount']:.2f}".replace('.', ','),
            "Series": pe['naming_series'],
            "Source Exchange Rate": "1,00",
            "Target Exchange Rate": "1,00",
            "ID (Payment References)": reference.get('name', ''),
            "Type (Payment References)": reference['reference_doctype'],
            "Name (Payment References)": reference['reference_name'],
            "ID (Advance Taxes and Charges)": pe['taxes'][0].get('name', ''),
            "Account Head (Advance Taxes and Charges)": pe['taxes'][0]['account_head'],
            "Add Or Deduct (Advance Taxes and Charges)": pe['taxes'][0]['add_deduct_tax'],
            "Description (Advance Taxes and Charges)": pe['taxes'][0]['description'],
            "Party Type": pe['party_type'],
            "Party": pe['party'],
            "Cheque/Reference Date": pe['posting_date'],
            "Cheque/Reference No": random.randint(1, 1000),
            "Type (Advance Taxes and Charges)": pe['taxes'][0]['charge_type']
        }
        flattened_data.append(row)

    fieldnames = flattened_data[0].keys()
    with open(os.path.join(Config.OUTPUT_DIR, filename), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)


def main():
    purchase_invoices = load_purchase_invoices()
    payment_entries = generate_payment_entries(purchase_invoices)

    successful_uploads = []
    for pe in payment_entries:
        success, system_id, response_data = upload_payment_entry_to_api(pe)
        if success:
            pe['name'] = system_id
            if 'references' in response_data:
                for i, ref in enumerate(pe['references']):
                    ref['name'] = response_data['references'][i]['name']
            if 'taxes' in response_data:
                for i, tax in enumerate(pe['taxes']):
                    tax['name'] = response_data['taxes'][i]['name']
            successful_uploads.append(pe)

    save_to_csv(successful_uploads, 'payment_entries.csv')


if __name__ == "__main__":
    main()