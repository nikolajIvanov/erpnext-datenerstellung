import csv
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker for different locales
fake_de = Faker('en_GB')  # Using UK English for German cities
fake_at = Faker('en_GB')  # Using UK English for Austrian cities
fake_ch = Faker('en_GB')  # Using UK English for Swiss cities

# Set a fixed seed for reproducibility
Faker.seed(12345)
random.seed(12345)


# Load existing data
def load_csv(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


campaigns = load_csv('campaigns.csv')
companies = load_csv('companies.csv')
territories = load_csv('territories.csv')
sources = load_csv('source_data.csv')

# Load employees data
employees = load_csv('employees_level_0.csv') + load_csv('employees_level_1.csv') + load_csv('employees_level_2.csv')
sales_persons = [emp for emp in employees if emp['Department'] == 'Sales']

# Define constants
LEAD_STATUSES = ['Open', 'Replied', 'Opportunity', 'Interested', 'Quotation', 'Lost Quotation', 'Converted']
LEAD_TYPES = ['Client', 'Channel Partner', 'Consultant']
MARKET_SEGMENTS = ['Upper Income', 'Middle Income', 'Lower Income']
EMPLOYEE_RANGES = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']

JOB_TITLES = [
    "Purchasing Manager", "CEO", "Sales Director", "Store Manager",
    "Product Manager", "Logistics Manager", "Marketing Director", "E-Commerce Manager",
    "Operations Manager", "Fleet Manager", "Sustainability Manager"
]

RELEVANT_INDUSTRIES = [
    "Retail & Wholesale", "Sports", "Transportation", "Logistics", "Tourism",
    "Health Care", "Manufacturing", "Consumer Products", "E-commerce"
]

# Define major cities for each country
GERMAN_CITIES = ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig",
                 "Dortmund", "Essen"]
AUSTRIAN_CITIES = ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt", "Villach", "Wels", "St. Pölten",
                   "Dornbirn"]
SWISS_CITIES = ["Zurich", "Geneva", "Basel", "Lausanne", "Bern", "Winterthur", "Lucerne", "St. Gallen", "Lugano",
                "Biel"]


def get_city_for_country(country):
    if country == "Germany":
        return random.choice(GERMAN_CITIES)
    elif country == "Austria":
        return random.choice(AUSTRIAN_CITIES)
    elif country == "Switzerland":
        return random.choice(SWISS_CITIES)
    else:
        return fake_de.city()  # Default to a random city if country is unknown


def generate_lead_id(date):
    year = date.year
    sequence = random.randint(1, 99999)
    return f"L-{year}-{sequence:05d}"


def generate_lead(date):
    company = random.choice(companies)
    campaign = random.choice(campaigns)
    territory = random.choice(territories)
    sales_person = random.choice(sales_persons)

    status = random.choice(LEAD_STATUSES)

    lead = {
        "ID": generate_lead_id(date),
        "Creation Date": date.strftime("%Y-%m-%d"),
        "Status": status,
        "Annual Revenue": fake_de.random_number(digits=7),
        "Blog Subscriber": random.choice([0, 1]),
        "Campaign Name": campaign['ID'],
        "City": get_city_for_country(company['Country']),
        "Company": company['Company'],
        "Country": company['Country'],
        "Disabled": 0,
        "Email": fake_de.company_email(),
        "Fax": fake_de.phone_number(),
        "First Name": fake_de.first_name(),
        "From Customer": "",
        "Full Name": "",  # Will be filled later
        "Gender": random.choice(['Male', 'Female']),
        "Industry": random.choice(RELEVANT_INDUSTRIES),
        "Job Title": random.choice(JOB_TITLES),
        "Last Name": fake_de.last_name(),
        "Lead Owner": sales_person['Company Email'],
        "Lead Type": random.choice(LEAD_TYPES),
        "Market Segment": random.choice(MARKET_SEGMENTS),
        "Mobile No": fake_de.phone_number(),
        "No of Employees": random.choice(EMPLOYEE_RANGES),
        "Organization Name": company['Company'],
        "Phone": fake_de.phone_number(),
        "Print Language": "en",
        "Qualification Status": "Qualified" if status in ['Opportunity', 'Quotation', 'Converted'] else "Unqualified",
        "Qualified By": "",  # Will be filled if qualified
        "Qualified on": "",  # Will be filled if qualified
        "Request Type": "Product Enquiry",
        "Salutation": random.choice(['Mr', 'Mrs', 'Ms', 'Dr']),
        "Source": random.choice(sources)['Source Name'],
        "Territory": territory['Territory Name'],
        "Unsubscribed": 0,
        "Website": company['Website']
    }

    # Fill in Full Name
    lead['Full Name'] = f"{lead['Salutation']} {lead['First Name']} {lead['Last Name']}"

    # Fill in qualification details if applicable
    if lead['Qualification Status'] == "Qualified":
        lead['Qualified By'] = lead['Lead Owner']
        qualification_date = date + timedelta(days=random.randint(1, 30))
        lead['Qualified on'] = qualification_date.strftime("%Y-%m-%d")

    return lead


def generate_leads(num_leads):
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2023, 12, 31)
    date_range = (end_date - start_date).days

    leads = []
    for _ in range(num_leads):
        random_days = random.randint(0, date_range)
        lead_date = start_date + timedelta(days=random_days)
        leads.append(generate_lead(lead_date))

    # Sort leads by creation date
    leads.sort(key=lambda x: x['Creation Date'])

    return leads


def save_to_csv(leads, filename):
    fieldnames = [
        "ID", "Creation Date", "Status", "Annual Revenue", "Blog Subscriber", "Campaign Name", "City", "Company",
        "Country",
        "Disabled", "Email", "Fax", "First Name", "From Customer", "Full Name", "Gender", "Industry",
        "Job Title", "Last Name", "Lead Owner", "Lead Type", "Market Segment", "Mobile No", "No of Employees",
        "Organization Name", "Phone", "Print Language", "Qualification Status", "Qualified By", "Qualified on",
        "Request Type", "Salutation", "Source", "Territory", "Unsubscribed", "Website"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)


def main():
    num_leads = 1000  # You can adjust this number
    leads = generate_leads(num_leads)
    save_to_csv(leads, 'generated_leads.csv')
    print(f"Generated {num_leads} leads from 2019 to 2023 and saved to generated_leads.csv")


if __name__ == "__main__":
    main()