import csv
import random
from faker import Faker
import re

# Initialisierung des Faker-Generators für deutschsprachige Daten
fake = Faker('de_DE')


def generate_supplier_code():
    return f"SUP-{random.randint(1000, 9999)}"


def generate_company_email(company_name):
    clean_name = re.sub(r'[^\w\s-]', '', company_name.lower())
    domain_name = re.sub(r'\s+', '.', clean_name)
    aliases = ['info', 'kontakt', 'verkauf', 'einkauf', 'support']
    alias = random.choice(aliases)
    return f"{alias}@{domain_name}.de"


def generate_company_website(company_name):
    clean_name = re.sub(r'[^\w\s-]', '', company_name.lower())
    domain_name = clean_name.replace(' ', '-')
    return f"www.{domain_name}.de"


def generate_suppliers(num_suppliers):
    suppliers = []
    supplier_types = ["Company", "Individual", "Proprietorship", "Partnership"]
    supplier_groups = [
        "Local", "Raw Material", "Hardware", "Distributor",
        "Component Manufacturer", "Raw Material Supplier"
    ]

    group_weights = [0.3, 0.1, 0.2, 0.1, 0.2, 0.1]

    for i in range(num_suppliers):
        supplier_group = random.choices(supplier_groups, weights=group_weights)[0]
        company_name = fake.company()

        supplier = {
            "ID": generate_supplier_code(),
            "Supplier Name": company_name,
            "Supplier Type": random.choice(supplier_types),
            "Country": "Germany",
            "Supplier Group": supplier_group,
            "Email Id": generate_company_email(company_name),
            "Mobile No": fake.phone_number(),
            "Supplier Details": fake.bs(),
            "Website": generate_company_website(company_name),
            "Is Frozen": 0,
            "Is Internal Supplier": 0,
            "Disabled": 0,
            "Allow Purchase Invoice Creation Without Purchase Order": 1 if random.random() < 0.3 else 0,
            "Allow Purchase Invoice Creation Without Purchase Receipt": 1 if random.random() < 0.3 else 0,
        }
        suppliers.append(supplier)
    return suppliers


def save_to_csv(suppliers, filename):
    fieldnames = [
        "ID", "Supplier Name", "Supplier Type", "Country", "Supplier Group",
        "Email Id", "Mobile No", "Supplier Details", "Website", "Is Frozen",
        "Is Internal Supplier", "Disabled",
        "Allow Purchase Invoice Creation Without Purchase Order",
        "Allow Purchase Invoice Creation Without Purchase Receipt"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for supplier in suppliers:
            writer.writerow({k: supplier.get(k, '') for k in fieldnames})


def main():
    num_suppliers = 50  # Anzahl der zu generierenden Lieferanten
    suppliers = generate_suppliers(num_suppliers)
    save_to_csv(suppliers, 'velo_gmbh_suppliers.csv')
    print(f"Generated {len(suppliers)} suppliers and saved to velo_gmbh_suppliers.csv")


if __name__ == "__main__":
    main()