import csv
import random
from faker import Faker

fake_de = Faker('de_DE')
fake_at = Faker('de_AT')
fake_ch = Faker('de_CH')


def load_companies(filename):
    companies = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            companies.append(row)
    return companies


def load_campaigns(filename):
    campaigns = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            campaigns.append(row["ID"])
    return campaigns


def load_sales_persons(filename):
    sales_persons = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            sales_persons.append(row["Sales Person Name"])
    return sales_persons


def load_sources(filename):
    sources = []
    with open(filename, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            sources.append(row["Source Name"])
    return sources


def generate_fake_data(country):
    if country == "Germany":
        return {
            "City": fake_de.city(),
            "Email": fake_de.email(),
            "Full Name": fake_de.name(),
            "Mobile No": fake_de.phone_number(),
            "Phone": fake_de.phone_number()
        }
    elif country == "Austria":
        return {
            "City": fake_at.city(),
            "Email": fake_at.email(),
            "Full Name": fake_at.name(),
            "Mobile No": fake_at.phone_number(),
            "Phone": fake_at.phone_number()
        }
    elif country == "Switzerland":
        return {
            "City": fake_ch.city(),
            "Email": fake_ch.email(),
            "Full Name": fake_ch.name(),
            "Mobile No": fake_ch.phone_number(),
            "Phone": fake_ch.phone_number()
        }
    else:
        return generate_fake_data("Germany")  # Default to German


def generate_leads(num_leads, companies, campaigns, sales_persons, sources):
    leads = []
    statuses = ["Lead", "Open", "Replied", "Opportunity", "Interested", "Converted", "Do Not Contact"]
    lead_types = ["Client", "Channel Partner", "Consultant"]
    employee_ranges = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]

    industries = [
        "Retail & Wholesale", "Manufacturing", "Consumer Products", "Sports",
        "Transportation", "Technology", "Service", "Entertainment & Leisure",
        "Online Auctions", "Health Care", "Education"
    ]

    # First, create a lead for each company
    for i, company in enumerate(companies):
        fake_data = generate_fake_data(company["Country"])
        lead = {
            "ID": f"LEAD-{i + 1:04d}",
            "Status": random.choice(statuses),
            "Annual Revenue": random.randint(100000, 10000000),
            "Campaign": random.choice(campaigns),
            "City": fake_data["City"],
            "Company": company["Company"],
            "Country": company["Country"],
            "Email": company["Email"],
            "Full Name": fake_data["Full Name"],
            "Industry": random.choice(industries),
            "Lead Owner": random.choice(sales_persons),
            "Lead Type": random.choice(lead_types),
            "Mobile No": fake_data["Mobile No"],
            "No of Employees": random.choice(employee_ranges),
            "Phone": company["Phone No"],
            "Qualification Status": random.choice(["Unqualified", "In Process", "Qualified"]),
            "Source": random.choice(sources),
            "Territory": company["Country"],
            "Website": company["Website"]
        }
        leads.append(lead)

    # Then, create additional individual leads
    for i in range(num_leads - len(companies)):
        country = random.choice(["Germany", "Austria", "Switzerland"])
        fake_data = generate_fake_data(country)
        lead = {
            "ID": f"LEAD-{len(companies) + i + 1:04d}",
            "Status": random.choice(statuses),
            "Campaign": random.choice(campaigns),
            "City": fake_data["City"],
            "Country": country,
            "Email": fake_data["Email"],
            "Full Name": fake_data["Full Name"],
            "Industry": random.choice(industries),
            "Lead Owner": random.choice(sales_persons),
            "Lead Type": random.choice(lead_types),
            "Mobile No": fake_data["Mobile No"],
            "Phone": fake_data["Phone"],
            "Qualification Status": random.choice(["Unqualified", "In Process", "Qualified"]),
            "Source": random.choice(sources),
            "Territory": country
        }
        leads.append(lead)

    return leads


def save_to_csv(leads, filename):
    fieldnames = [
        "ID", "Status", "Annual Revenue", "Campaign", "City", "Company", "Country",
        "Email", "Full Name", "Industry", "Lead Owner", "Lead Type",
        "Mobile No", "No of Employees", "Phone", "Qualification Status", "Source",
        "Territory", "Website"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, '') for k in fieldnames})


def main():
    # Load necessary data
    companies = load_companies('../master_data_csv/companies.csv')
    campaigns = load_campaigns('../master_data_csv/campaigns.csv')
    sales_persons = load_sales_persons('../master_data_csv/sales_directors.csv') + \
                    load_sales_persons('../master_data_csv/sales_managers.csv') + \
                    load_sales_persons('../master_data_csv/sales_reps.csv')
    sources = load_sources('../master_data_csv/source_data.csv')

    # Generate leads for all companies plus additional individual leads
    total_leads = 70  # Adjust this number as needed
    leads = generate_leads(total_leads, companies, campaigns, sales_persons, sources)
    save_to_csv(leads, '../Generated_CSV/leads.csv')
    print(f"Generated {len(leads)} leads and saved to leads.csv")


if __name__ == "__main__":
    main()