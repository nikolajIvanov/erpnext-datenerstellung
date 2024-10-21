import csv
import os
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict
import uuid
from api.sales_order_api import SalesOrderAPI
from api.delivery_note_api import DeliveryNoteAPI
from api.sales_invoice_api import SalesInvoiceAPI
from api.payment_entry_api import PaymentEntryAPI


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INPUT_DIR = os.path.join(BASE_DIR, 'Master-Data_Processed_CSV')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')
    START_DATE = datetime(2024, 1, 1)
    END_DATE = datetime(2024, 12, 31)
    MAIN_WAREHOUSE = "Lager Stuttgart - B"

    # Anzahl der zu generierenden Aufträge pro Verkaufskanal
    NUM_ORDERS_B2B = 1
    NUM_ORDERS_B2C_ONLINE = 0
    NUM_ORDERS_B2C_FILIALE = 0


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialisierung der API-Klassen
sales_order_api = SalesOrderAPI()
delivery_note_api = DeliveryNoteAPI()
sales_invoice_api = SalesInvoiceAPI()
payment_entry_api = PaymentEntryAPI()


def load_csv_data(filename: str) -> List[Dict]:
    with open(os.path.join(Config.INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )


def load_customers() -> Dict[str, List[Dict]]:
    customers = load_csv_data('customers.csv')
    return {
        'B2B': [c for c in customers if c['Customer Group'] in ['Wholesale', 'B2B']],
        'B2C': [c for c in customers if c['Customer Group'] in ['Retail', 'B2C']]
    }


def load_products() -> List[Dict]:
    return load_csv_data('items.csv')


def load_price_lists() -> Dict[str, Dict]:
    price_lists = load_csv_data('price_lists.csv')
    return {pl['Price List Name']: pl for pl in price_lists}


def generate_sales_order(customers: Dict[str, List[Dict]], products: List[Dict], price_lists: Dict[str, Dict],
                         sales_channel: str) -> Dict:
    customer = random.choice(customers['B2B' if sales_channel == 'B2B' else 'B2C'])
    order_date = random_date(Config.START_DATE, Config.END_DATE)

    price_list = price_lists['Wholesale Price'] if sales_channel == 'B2B' else price_lists['Standard Selling']

    order_items = []
    total_amount = 0.0
    for _ in range(random.randint(1, 5)):  # 1 bis 5 Produkte pro Auftrag
        product = random.choice(products)
        qty = random.randint(1, 10)
        rate = float(product['Standard Selling Rate'])
        amount = round(qty * rate, 2)
        total_amount += amount

        order_items.append({
            "item_code": product['Item Code'],
            "item_name": product['Item Name'],
            "qty": qty,
            "rate": rate,
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
        "selling_price_list": price_list['Price List Name'],
        "currency": "EUR",
        "conversion_rate": 1.0,
        "price_list_currency": "EUR",
        "grand_total": total_amount,
        "total": total_amount,
        "items": order_items,
        "sales_channel": sales_channel
    }


def generate_delivery_note(sales_order: Dict) -> Dict:
    delivery_date = datetime.strptime(sales_order['delivery_date'], "%Y-%m-%d")
    return {
        "doctype": "Delivery Note",
        "naming_series": "DN-.YYYY.-",
        "posting_date": delivery_date.strftime("%Y-%m-%d"),
        "customer": sales_order['customer'],
        "customer_group": sales_order['customer_group'],
        "territory": sales_order['territory'],
        "currency": sales_order['currency'],
        "selling_price_list": sales_order['selling_price_list'],
        "items": sales_order['items'],
        "sales_order": sales_order['name']
    }


def generate_sales_invoice(sales_order: Dict, delivery_note: Dict) -> Dict:
    invoice_date = datetime.strptime(delivery_note['posting_date'], "%Y-%m-%d") + timedelta(days=random.randint(0, 3))
    return {
        "doctype": "Sales Invoice",
        "naming_series": "INV-.YYYY.-",
        "posting_date": invoice_date.strftime("%Y-%m-%d"),
        "customer": sales_order['customer'],
        "customer_group": sales_order['customer_group'],
        "territory": sales_order['territory'],
        "currency": sales_order['currency'],
        "selling_price_list": sales_order['selling_price_list'],
        "items": sales_order['items'],
        "sales_order": sales_order['name'],
        "delivery_note": delivery_note['name'],
        "grand_total": sales_order['grand_total'],
        "total": sales_order['total']
    }


def generate_payment_entry(sales_invoice: Dict) -> Dict:
    payment_date = datetime.strptime(sales_invoice['posting_date'], "%Y-%m-%d") + timedelta(days=random.randint(0, 30))
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


def main():
    customers = load_customers()
    products = load_products()
    price_lists = load_price_lists()

    sales_channels = {
        'B2B': Config.NUM_ORDERS_B2B,
        'B2C Online': Config.NUM_ORDERS_B2C_ONLINE,
        'B2C Filiale': Config.NUM_ORDERS_B2C_FILIALE
    }

    for channel, num_orders in sales_channels.items():
        logging.info(f"Generating {num_orders} orders for {channel} channel")
        for _ in range(num_orders):
            # Generiere Verkaufsauftrag
            sales_order = generate_sales_order(customers, products, price_lists, channel)
            so_response = sales_order_api.create(sales_order)
            if so_response.get('data'):
                sales_order['name'] = so_response['data']['name']
                logging.info(f"Created Sales Order: {sales_order['name']}")

                # Generiere Lieferschein
                delivery_note = generate_delivery_note(sales_order)
                dn_response = delivery_note_api.create(delivery_note)
                if dn_response.get('data'):
                    delivery_note['name'] = dn_response['data']['name']
                    logging.info(f"Created Delivery Note: {delivery_note['name']}")

                    # Generiere Rechnung
                    sales_invoice = generate_sales_invoice(sales_order, delivery_note)
                    si_response = sales_invoice_api.create(sales_invoice)
                    if si_response.get('data'):
                        sales_invoice['name'] = si_response['data']['name']
                        logging.info(f"Created Sales Invoice: {sales_invoice['name']}")

                        # Generiere Zahlungseingang
                        payment_entry = generate_payment_entry(sales_invoice)
                        pe_response = payment_entry_api.create(payment_entry)
                        if pe_response.get('data'):
                            payment_entry['name'] = pe_response['data']['name']
                            logging.info(f"Created Payment Entry: {payment_entry['name']}")
                            logging.info(f"Completed full sales cycle for {channel} order {sales_order['name']}")
                        else:
                            logging.error(f"Failed to create Payment Entry for invoice {sales_invoice['name']}")
                    else:
                        logging.error(f"Failed to create Sales Invoice for delivery note {delivery_note['name']}")
                else:
                    logging.error(f"Failed to create Delivery Note for sales order {sales_order['name']}")
            else:
                logging.error(f"Failed to create Sales Order for {channel}")


if __name__ == "__main__":
    main()