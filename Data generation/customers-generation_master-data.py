import csv
import random
from faker import Faker

# Initialize Faker for German locale
fake = Faker('de_DE')


def generate_customer_code(is_company):
    prefix = "CUST-B2B-" if is_company else "CUST-B2C-"
    return f"{prefix}{random.randint(1000, 9999)}"


def generate_email(name):
    clean_name = ''.join(e.lower() for e in name if e.isalnum())
    return f"{clean_name}@example.com"


def generate_customers(num_b2b, num_b2c):
    customers = []

    customer_groups = ["Wholesale", "Retail", "B2B", "B2C"]
    territories = ["Germany", "Austria", "Switzerland"]
    price_lists = ["Standard Selling", "Wholesale Price"]
    salutations = ["Mr", "Mrs", "Ms", "Dr", "Prof"]

    # B2B Customers
    for i in range(num_b2b):
        company_name = fake.company()
        customer = {
            "ID": generate_customer_code(True),
            "Customer Name": company_name,
            "Customer Type": "Company",
            "Customer Group": random.choice(["Wholesale", "B2B"]),
            "Territory": random.choice(territories),
            "Mobile No": fake.phone_number(),
            "Email Id": generate_email(company_name),
            "Default Price List": random.choice(price_lists),
            "Billing Currency": "EUR",
            "From Lead": fake.random_element(elements=(True, False)),
            "Industry": fake.job(),
            "Website": fake.domain_name(),
            "Tax ID": fake.numerify(text="DE###########"),
            "Customer POS id": fake.numerify(text="POS-####"),
            "Salutation": "",  # Empty for companies
        }
        customers.append(customer)

    # B2C Customers
    for i in range(num_b2c):
        customer_name = fake.name()
        customer = {
            "ID": generate_customer_code(False),
            "Customer Name": customer_name,
            "Customer Type": "Individual",
            "Customer Group": random.choice(["Retail", "B2C"]),
            "Territory": random.choice(territories),
            "Mobile No": fake.phone_number(),
            "Email Id": generate_email(customer_name),
            "Default Price List": "Standard Selling",
            "Billing Currency": "EUR",
            "From Lead": fake.random_element(elements=(True, False)),
            "Gender": random.choice(["Male", "Female", "Other"]),
            "Salutation": random.choice(salutations),
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
    num_b2b_customers = 10  # Number of B2B customers
    num_b2c_customers = 100  # Number of B2C customers
    customers = generate_customers(num_b2b_customers, num_b2c_customers)
    save_to_csv(customers, '../new csv/customers.csv')
    print(f"Generated {len(customers)} customers and saved to customers.csv")


if __name__ == "__main__":
    main()