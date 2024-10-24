import csv
import random
from faker import Faker
from datetime import datetime, timedelta
"""
Für uns irrelevant:

Unterscheidung zwischen Company und Customer:
"Company" repräsentiert in ERPNext typischerweise Ihr eigenes Unternehmen oder Tochtergesellschaften.
"Customer" wird für Ihre Kunden verwendet, unabhängig davon, ob es sich um Einzelpersonen oder Unternehmen handelt.
"""
# Initialize Faker for German locale
fake = Faker('de_DE')

def load_territories(filename):
    territories = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            territories.append(row['Territory Name'])
    return territories

def generate_company_name():
    bike_related_words = ["Bike", "Cycle", "Pedal", "Wheel", "Gear", "Chain", "Spoke", "Frame", "Ride", "Velocity"]
    company_types = ["GmbH", "AG", "KG", "OHG", "e.K.", "GbR"]
    return f"{random.choice(bike_related_words)} {fake.last_name()} {random.choice(company_types)}"

def generate_companies(num_companies, territories):
    companies = []
    for i in range(1, num_companies + 1):
        territory = random.choice(territories)
        company = {
            "Abbr": f"COMP{i:04d}",
            "Company": generate_company_name(),
            "Country": get_country_for_territory(territory),
            "Default Currency": get_currency_for_territory(territory),
            "Company Description": generate_company_description(),
            "Domain": fake.domain_name(),
            "Email": fake.company_email(),
            "Phone No": fake.phone_number(),
            "Fax": fake.phone_number(),
            "Tax ID": generate_tax_id(territory),
            "Website": fake.url(),
            "Date of Incorporation": (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime("%Y-%m-%d"),
            "Enable Perpetual Inventory": 1,
            "Credit Limit": random.randint(10000, 1000000),
        }
        companies.append(company)
    return companies

def get_country_for_territory(territory):
    country_map = {
        "Germany": "Germany",
        "Austria": "Austria",
        "Switzerland": "Switzerland"
    }
    return country_map.get(territory, "Germany")  # Default to Germany if territory is not found

def get_currency_for_territory(territory):
    currency_map = {
        "Germany": "EUR",
        "Austria": "EUR",
        "Switzerland": "CHF"
    }
    return currency_map.get(territory, "EUR")  # Default to EUR if territory is not found

def generate_tax_id(territory):
    if territory == "Germany":
        return fake.numerify(text="DE###########")
    elif territory == "Austria":
        return fake.numerify(text="ATU########")
    elif territory == "Switzerland":
        return fake.numerify(text="CHE-###.###.###")
    else:
        return fake.numerify(text="??##########")

def generate_company_description():
    activities = [
        "Specializing in high-performance bicycles",
        "Focusing on urban commuter bikes",
        "Producing premium e-bikes",
        "Manufacturing bicycle components",
        "Offering comprehensive bike repair services",
        "Distributing cycling accessories",
        "Designing custom bicycles",
        "Providing bike rental services",
        "Organizing cycling tours and events",
        "Developing innovative cycling technologies"
    ]
    return f"{random.choice(activities)} for the {random.choice(['local', 'national', 'international'])} market."

def save_to_csv(companies, filename):
    fieldnames = [
        "Abbr", "Company", "Country", "Default Currency", "Company Description",
        "Domain", "Email", "Phone No", "Fax", "Tax ID", "Website",
        "Date of Incorporation", "Enable Perpetual Inventory", "Credit Limit"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for company in companies:
            writer.writerow(company)

def main():
    """
    Für die Erstellung der Unternehmen werden die Gebiete aus der territories.csv Datei verwendet.
    :return: csv Datei mit {num_companies} 50 Unternehmen
    """
    territories = load_territories('../master/territories.csv')
    num_companies = 50  # Adjust this number as needed
    companies = generate_companies(num_companies, territories)
    save_to_csv(companies, '../generated/companies.csv')
    print(f"Generated {len(companies)} companies and saved to companies.csv")

if __name__ == "__main__":
    main()