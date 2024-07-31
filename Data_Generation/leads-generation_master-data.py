import csv
import random
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker for German locale
fake = Faker('de_DE')

def generate_lead_id():
    return f"LEAD-{random.randint(10000, 99999)}"

def generate_leads(num_leads):
    leads = []
    statuses = ["Lead", "Open", "Replied", "Opportunity", "Interested", "Converted", "Do Not Contact"]
    sources = ["Advertisement", "Campaign", "Cold Calling", "Employee Referral", "Exhibition", "Existing Customer", "Mass Mailing", "Supplier Referral", "Walk In"]
    territories = ["Germany", "Austria", "Switzerland"]
    industry_types = [
        "Retail & Wholesale", "Sports", "Manufacturing", "Transportation",
        "Technology", "Service", "Consumer Products", "Automotive",
        "Health Care", "Entertainment & Leisure", "Energy", "Electronics", "Education"
    ]

    for _ in range(num_leads):
        company_name = fake.company()
        lead = {
            "ID": generate_lead_id(),
            "Status": random.choice(statuses),
            "Annual Revenue": random.randint(100000, 10000000),
            "Blog Subscriber": random.choice(["0", "1"]),
            "Campaign Name": f"Campaign-{random.randint(1000, 9999)}",
            "City": fake.city(),
            "Company": company_name,
            "Country": "Germany",
            "Disabled": "0",
            "Email": fake.company_email(),
            "Fax": fake.phone_number(),
            "First Name": fake.first_name(),
            "Last Name": fake.last_name(),
            "Full Name": fake.name(),
            "Gender": random.choice(["Male", "Female", "Other"]),
            "Industry": random.choice(industry_types),
            "Job Title": fake.job(),
            "Lead Owner": fake.name(),
            "Lead Type": "B2B",
            "Market Segment": random.choice(["Lower Income", "Middle Income", "High Income"]),
            "Mobile No": fake.phone_number(),
            "No of Employees": random.randint(10, 1000),
            "Organization Name": company_name,
            "Phone": fake.phone_number(),
            "Phone Ext.": str(random.randint(100, 999)),
            "Qualification Status": random.choice(["Unqualified", "In Process", "Qualified"]),
            "Qualified By": fake.name(),
            "Qualified on": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "Request Type": random.choice(["Product Enquiry", "Request for Information", "Suggestion", "Other"]),
            "Salutation": random.choice(["Mr", "Mrs", "Ms", "Dr", "Prof"]),
            "Source": random.choice(sources),
            "State": fake.state(),
            "Territory": random.choice(territories),
            "Title": fake.job(),
            "Unsubscribed": random.choice(["0", "1"]),
            "Website": fake.domain_name(),
            "WhatsApp": fake.phone_number()
        }
        leads.append(lead)
    return leads

def save_to_csv(leads, filename):
    fieldnames = [
        "ID", "Status", "Annual Revenue", "Blog Subscriber", "Campaign Name", "City",
        "Company", "Country", "Disabled", "Email", "Fax", "First Name", "Last Name",
        "Full Name", "Gender", "Industry", "Job Title", "Lead Owner", "Lead Type",
        "Market Segment", "Mobile No", "No of Employees", "Organization Name", "Phone",
        "Phone Ext.", "Qualification Status", "Qualified By", "Qualified on", "Request Type",
        "Salutation", "Source", "State", "Territory", "Title", "Unsubscribed", "Website", "WhatsApp"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

def main():
    num_leads = 100  # Adjust this number as needed
    leads = generate_leads(num_leads)
    save_to_csv(leads, '../Generated_CSV/leads.csv')
    print(f"Generated {len(leads)} leads and saved to leads.csv")

if __name__ == "__main__":
    main()