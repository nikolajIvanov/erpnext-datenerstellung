import csv
import random
from faker import Faker
import os
from api.customer_api import CustomerAPI

# Initialize Faker for German locale
fake = Faker('de_DE')

# Initialize CustomerAPI
customer_api = CustomerAPI()


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, 'master_data_csv')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'Generated_CSV')


def generate_b2b_customer_name():
    bike_related_words = [
        "Fahrrad", "Bike", "Zweirad", "Velo", "Rad", "Cycle", "Pedal",
        "Sattel", "Kette", "Speiche", "Lenker", "Bremse", "Schaltung"
    ]
    business_types = [
        "Großhandel", "Handel", "Vertrieb", "Import", "Export", "Logistik",
        "Versand", "Service", "Reparatur", "Werkstatt", "Shop", "Store"
    ]
    suffixes = ["GmbH", "AG", "KG", "OHG", "GmbH & Co. KG", "e.K."]

    name_parts = [
        random.choice(bike_related_words),
        random.choice(business_types),
        fake.last_name(),
        random.choice(suffixes)
    ]
    return " ".join(name_parts)


def generate_b2b_customer():
    company_name = generate_b2b_customer_name()
    return {
        "doctype": "Customer",
        "naming_series": "CUST-.YYYY.-",
        "customer_name": company_name,
        "customer_type": "Company",
        "customer_group": "B2B",
        "language": "de"
    }


def generate_b2c_customer():
    customer_name = fake.name()
    return {
        "doctype": "Customer",
        "naming_series": "CUST-.YYYY.-",
        "customer_name": customer_name,
        "customer_type": "Individual",
        "customer_group": "B2C"
    }


def create_b2b_customers(num_customers):
    created_customers = []
    for _ in range(num_customers):
        customer_data = generate_b2b_customer()
        response = customer_api.create(customer_data)
        if response.get('data'):
            created_customers.append(response['data'])
            print(f"Created B2B customer: {response['data']['name']}")
        else:
            print(f"Failed to create B2B customer: {response}")
    return created_customers


def create_b2c_customer():
    customer_data = generate_b2c_customer()
    response = customer_api.create(customer_data)
    if response.get('data'):
        print(f"Created B2C customer: {response['data']['name']}")
        return response['data']
    else:
        print(f"Failed to create B2C customer: {response}")
        return None


def save_customers_to_csv(customers, filename):
    if not customers:
        print("No customers to save.")
        return

    fieldnames = customers[0].keys()
    filepath = os.path.join(Config.OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for customer in customers:
            writer.writerow(customer)

    print(f"Saved {len(customers)} customers to {filepath}")


def main():
    num_b2b_customers = 10
    created_b2b_customers = create_b2b_customers(num_b2b_customers)
    print(f"Created {len(created_b2b_customers)} B2B customers")

    # Save B2B customers to CSV
    save_customers_to_csv(created_b2b_customers, 'b2b_customers.csv')


if __name__ == "__main__":
    main()
