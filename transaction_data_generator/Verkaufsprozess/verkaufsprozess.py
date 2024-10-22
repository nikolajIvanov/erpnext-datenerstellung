import csv
import os
from datetime import datetime, timedelta
import random
import logging
import json
from typing import List, Dict
import uuid
from api.sales_order_api import SalesOrderAPI
from api.delivery_note_api import DeliveryNoteAPI
from api.sales_invoice_api import SalesInvoiceAPI
from api.payment_entry_api import PaymentEntryAPI
from master_data_generator.create_customer import create_b2c_customer


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    JSON_DIR = os.path.join(BASE_DIR, 'api_payloads')  # New directory for JSON payloads
    START_DATE = datetime.now() - timedelta(days=5*365)  # 5 Jahre zurück
    END_DATE = datetime.now()
    MAIN_WAREHOUSE = "Lager Stuttgart - B"
    B2B_CUSTOMERS_FILE = 'b2b_customers.csv'
    B2C_CUSTOMERS_FILE = 'b2c_customers.csv'

    # Number of orders to generate per sales channel
    NUM_ORDERS_B2B = 1
    NUM_ORDERS_B2C_ONLINE = 0
    NUM_ORDERS_B2C_FILIALE = 0

    # Markup factors for different customer groups
    B2B_MARKUP = 1.3  # 30% markup for B2B
    B2C_MARKUP = 1.5  # 50% markup for B2C

    DELIVERY_DELAY = (1, 7)   # Lieferung 1-7 Tage nach Bestellung
    INVOICE_DELAY = (0, 3)    # Rechnung 0-3 Tage nach Lieferung
    PAYMENT_DELAY = (0, 30)   # Zahlung 0-30 Tage nach Rechnungsstellung


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize API classes
sales_order_api = SalesOrderAPI()
delivery_note_api = DeliveryNoteAPI()
sales_invoice_api = SalesInvoiceAPI()
payment_entry_api = PaymentEntryAPI()

# Ensure JSON directory exists
os.makedirs(Config.JSON_DIR, exist_ok=True)

def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_b2b_customers() -> List[Dict]:
    b2b_customers = []
    b2b_file_path = os.path.join(Config.INPUT_DIR, Config.B2B_CUSTOMERS_FILE)
    if os.path.exists(b2b_file_path):
        with open(b2b_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            b2b_customers = [{"Customer Name": row['name'], "Customer Group": "B2B", "Territory": "Germany"} for row in reader]
    return b2b_customers


def save_b2c_customers(customers: List[Dict]):
    file_path = os.path.join(Config.OUTPUT_DIR, Config.B2C_CUSTOMERS_FILE)
    fieldnames = customers[0].keys() if customers else []
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)
    logging.info(f"B2C customers saved to {file_path}")


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_products() -> List[Dict]:
    return load_csv_data('items.csv')


def calculate_selling_rate(base_rate: float, sales_channel: str) -> float:
    """Calculate selling rate based on valuation rate and customer type"""
    markup = Config.B2B_MARKUP if sales_channel == 'B2B' else Config.B2C_MARKUP
    return round(float(base_rate) * markup, 2)


def save_api_payload(payload: Dict, prefix: str, identifier: str):
    """Save API payload to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{identifier}_{timestamp}.json"
    filepath = os.path.join(Config.JSON_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved {prefix} payload to {filepath}")
    return filepath

def generate_sales_order(b2b_customers: List[Dict], products: List[Dict], sales_channel: str) -> Dict:
    if sales_channel == 'B2B':
        customer = random.choice(b2b_customers)
    else:
        customer = create_b2c_customer()
        if not customer:
            raise ValueError("Failed to create new B2C customer.")
        customer.update({"Customer Group": "B2C", "Territory": "Germany"})

    order_date = random_date(Config.START_DATE, Config.END_DATE)

    order_items = []
    total_amount = 0.0
    for _ in range(random.randint(1, 5)):  # 1 to 5 products per order
        product = random.choice(products)
        qty = random.randint(1, 10)
        base_rate = float(product['Valuation Rate'])
        selling_rate = calculate_selling_rate(base_rate, sales_channel)
        amount = round(qty * selling_rate, 2)
        total_amount += amount

        order_items.append({
            "item_code": product['Item Code'],
            "item_name": product.get('Item Name', product['Item Code']),
            "qty": qty,
            "rate": selling_rate,
            "amount": amount,
            "warehouse": Config.MAIN_WAREHOUSE if sales_channel != 'B2C Filiale' else f"Filiale {random.randint(1, 10)}"
        })

    return {
        "doctype": "Sales Order",
        "naming_series": "SO-.YYYY.-",
        "transaction_date": order_date.strftime("%Y-%m-%d"),
        "delivery_date": (order_date + timedelta(days=7)).strftime("%Y-%m-%d"),
        "customer": customer['Customer Name'],
        "customer_group": customer['Customer Group'],
        "territory": customer['Territory'],
        "currency": "EUR",
        "conversion_rate": 1.0,
        "grand_total": total_amount,
        "total": total_amount,
        "items": order_items,
        "sales_channel": sales_channel
    }


def generate_delivery_note(sales_order: Dict) -> Dict:
    so_date = datetime.strptime(sales_order['transaction_date'], "%Y-%m-%d")
    delivery_date = so_date + timedelta(days=random.randint(*Config.DELIVERY_DELAY))
    return {
        "doctype": "Delivery Note",
        "naming_series": "DN-.YYYY.-",
        "posting_date": delivery_date.strftime("%Y-%m-%d"),
        "customer": sales_order['customer'],
        "customer_group": sales_order['customer_group'],
        "territory": sales_order['territory'],
        "currency": sales_order['currency'],
        "items": sales_order['items'],
        "sales_order": sales_order['name']
    }


def generate_sales_invoice(sales_order: Dict, delivery_note: Dict) -> Dict:
    dn_date = datetime.strptime(delivery_note['posting_date'], "%Y-%m-%d")
    invoice_date = dn_date + timedelta(days=random.randint(*Config.INVOICE_DELAY))
    return {
        "doctype": "Sales Invoice",
        "naming_series": "INV-.YYYY.-",
        "posting_date": invoice_date.strftime("%Y-%m-%d"),
        "customer": sales_order['customer'],
        "customer_group": sales_order['customer_group'],
        "territory": sales_order['territory'],
        "currency": sales_order['currency'],
        "items": sales_order['items'],
        "sales_order": sales_order['name'],
        "delivery_note": delivery_note['name'],
        "grand_total": sales_order['grand_total'],
        "total": sales_order['total']
    }


def generate_payment_entry(sales_invoice: Dict) -> Dict:
    si_date = datetime.strptime(sales_invoice['posting_date'], "%Y-%m-%d")
    payment_date = si_date + timedelta(days=random.randint(*Config.PAYMENT_DELAY))
    return {
        "doctype": "Payment Entry",
        "naming_series": "PE-.YYYY.-",
        "payment_type": "Receive",
        "posting_date": payment_date.strftime("%Y-%m-%d"),
        "party_type": "Customer",
        "party": sales_invoice['customer'],
        "paid_amount": sales_invoice['grand_total'],
        "received_amount": sales_invoice['grand_total'],
        "reference_no": f"Payment for {sales_invoice['name']}",
        "reference_date": payment_date.strftime("%Y-%m-%d")
    }


def process_sales_cycle(sales_order: Dict, channel: str) -> bool:
    """Process complete sales cycle with payload logging"""
    try:
        # Save and create Sales Order
        so_filepath = save_api_payload(sales_order, "sales_order", sales_order['customer'])
        so_response = sales_order_api.create(sales_order)

        if so_response.get('data'):
            sales_order['name'] = so_response['data']['name']
            logging.info(f"Sales Order created: {sales_order['name']}")

            # Generate and save Delivery Note
            delivery_note = generate_delivery_note(sales_order)
            dn_filepath = save_api_payload(delivery_note, "delivery_note", sales_order['name'])
            dn_response = delivery_note_api.create(delivery_note)

            if dn_response.get('data'):
                delivery_note['name'] = dn_response['data']['name']
                logging.info(f"Delivery Note created: {delivery_note['name']}")

                # Generate and save Invoice
                sales_invoice = generate_sales_invoice(sales_order, delivery_note)
                si_filepath = save_api_payload(sales_invoice, "sales_invoice", delivery_note['name'])
                si_response = sales_invoice_api.create(sales_invoice)

                if si_response.get('data'):
                    sales_invoice['name'] = si_response['data']['name']
                    logging.info(f"Invoice created: {sales_invoice['name']}")

                    # Generate and save Payment Entry
                    payment_entry = generate_payment_entry(sales_invoice)
                    pe_filepath = save_api_payload(payment_entry, "payment_entry", sales_invoice['name'])
                    pe_response = payment_entry_api.create(payment_entry)

                    if pe_response.get('data'):
                        logging.info(f"Payment Entry created: {pe_response['data']['name']}")
                        logging.info(f"Complete sales cycle for {channel} order {sales_order['name']} finished")
                        return True
                    else:
                        logging.error(f"Error creating payment entry for invoice {sales_invoice['name']}")
                        logging.error(f"Payment Entry payload saved at: {pe_filepath}")
                else:
                    logging.error(f"Error creating invoice for delivery note {delivery_note['name']}")
                    logging.error(f"Sales Invoice payload saved at: {si_filepath}")
            else:
                logging.error(f"Error creating delivery note for sales order {sales_order['name']}")
                logging.error(f"Delivery Note payload saved at: {dn_filepath}")
        else:
            logging.error(f"Error creating sales order")
            logging.error(f"Sales Order payload saved at: {so_filepath}")

        return False
    except Exception as e:
        logging.error(f"Error in sales cycle: {str(e)}")
        return False


def main():
    b2b_customers = load_b2b_customers()
    products = load_products()
    created_b2c_customers = []

    sales_channels = {
        'B2B': Config.NUM_ORDERS_B2B,
        'B2C Online': Config.NUM_ORDERS_B2C_ONLINE,
        'B2C Filiale': Config.NUM_ORDERS_B2C_FILIALE
    }

    for channel, num_orders in sales_channels.items():
        logging.info(f"Generating {num_orders} orders for channel {channel}")
        for _ in range(num_orders):
            try:
                sales_order = generate_sales_order(b2b_customers, products, channel)
                if channel != 'B2B':
                    created_b2c_customers.append(sales_order['customer'])

                process_sales_cycle(sales_order, channel)

            except ValueError as e:
                logging.error(f"Error generating order for {channel}: {str(e)}")
                continue

    save_b2c_customers(created_b2c_customers)
    logging.info("Sales process completed.")


if __name__ == "__main__":
    main()

