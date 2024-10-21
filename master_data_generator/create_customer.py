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

def generate_customer_code(is_company):
    prefix = "CUST-B2B-" if is_company else "CUST-B2C-"
    return f"{prefix}{random.randint(1000, 9999)}"

def generate_email(name):
    clean_name = ''.join(e.lower() for e in name if e.isalnum())
    return f"{clean_name}@example.com"

def load_customer_groups():
    with open(os.path.join(Config.INPUT_DIR, 'customer_groups.csv'), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['Customer Group Name']: row for row in reader}


def generate_b2b_customer():
    company_name = fake.company()
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


def main():
    num_b2b_customers = 2
    created_b2b_customers = create_b2b_customers(num_b2b_customers)
    print(f"Created {len(created_b2b_customers)} B2B customers")


if __name__ == "__main__":
    main()
