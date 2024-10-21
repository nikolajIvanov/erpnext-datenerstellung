import csv
import random
from faker import Faker
"""
Diese Datei funktioniert nur in Kombination mit der Datei "leads-generation_master-data.py"
Die künstlichen Leads, die aus diesem Skrpit erstellt werden, dienen als Vorlage zur Erstellung von Kunden
"""
# Initialize Faker for German locale
fake = Faker('de_DE')

def generate_customer_code(is_company):
    prefix = "CUST-B2B-" if is_company else "CUST-B2C-"
    return f"{prefix}{random.randint(1000, 9999)}"

def generate_email(name):
    clean_name = ''.join(e.lower() for e in name if e.isalnum())
    return f"{clean_name}@example.com"

def load_leads(filename):
    leads = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            leads.append(row)
    return leads

def generate_customers(num_b2b, num_b2c, leads):
    customers = []

    # B2B Customers (converted from leads)
    for lead in random.sample(leads, min(num_b2b, len(leads))):
        customer = {
            "ID": generate_customer_code(True),
            "Customer Name": lead['Company'],
            "Customer Type": "Company",
            "Customer Group": random.choice(["Wholesale", "B2B"]),
            "Territory": lead['Territory'],
            "Mobile No": lead['Mobile No'],
            "Email Id": lead['Email'],
            "Default Price List": random.choice(["Standard Selling", "Wholesale Price"]),
            "Billing Currency": "EUR",
            "From Lead": lead['ID'],
            "Industry": lead['Industry'],
            "Website": lead['Website'],
            "Tax ID": fake.numerify(text="DE###########"),
            "Customer POS id": fake.numerify(text="POS-####"),
            "Salutation": "",  # Empty for companies
        }
        customers.append(customer)

    # B2C Customers (not from leads)
    for i in range(num_b2c):
        customer_name = fake.name()
        customer = {
            "ID": generate_customer_code(False),
            "Customer Name": customer_name,
            "Customer Type": "Individual",
            "Customer Group": random.choice(["Retail", "B2C"]),
            "Territory": random.choice(["Germany", "Austria", "Switzerland"]),
            "Mobile No": fake.phone_number(),
            "Email Id": generate_email(customer_name),
            "Default Price List": "Standard Selling",
            "Billing Currency": "EUR",
            "From Lead": "",
            "Gender": random.choice(["Male", "Female", "Other"]),
            "Salutation": random.choice(["Mr", "Mrs", "Ms", "Dr", "Prof"]),
        }
        customers.append(customer)

    return customers

def save_to_csv(customers, filename):
    fieldnames = [
        "ID", "Customer Name", "Customer Type", "Customer Group", "Territory",
        "Mobile No", "Email Id", "Default Price List", "Billing Currency",
        "From Lead", "Industry", "Website", "Tax ID", "Customer POS id",
        "Salutation", "Gender"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for customer in customers:
            writer.writerow({k: customer.get(k, '') for k in fieldnames})

def main():
    num_b2b_customers = 50
    num_b2c_customers = 200
    leads = load_leads('../Generated_CSV/leads.csv')
    customers = generate_customers(num_b2b_customers, num_b2c_customers, leads)
    save_to_csv(customers, '../Generated_CSV/customers.csv')
    print(f"Generated {len(customers)} customers and saved to customers.csv")

if __name__ == "__main__":
    main()