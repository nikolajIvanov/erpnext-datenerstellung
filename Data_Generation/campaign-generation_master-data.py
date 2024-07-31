import csv
import random
from faker import Faker

# Initialize Faker for German locale
fake = Faker('de_DE')

def generate_campaigns(num_campaigns):
    campaigns = []
    for i in range(1, num_campaigns + 1):
        campaign = {
            "ID": f"CAMP-{i:04d}",
            "Campaign Name": f"Kampagne {i:04d} - {fake.bs()}",
            "Description": fake.paragraph(),
            "Naming Series": "CAMP-.YYYY.-",
        }
        campaigns.append(campaign)
    return campaigns

def save_to_csv(campaigns, filename):
    fieldnames = [
        "ID", "Campaign Name", "Description", "Naming Series",
        "ID (Campaign Schedules)", "Email Template (Campaign Schedules)",
        "Send After (days) (Campaign Schedules)"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for campaign in campaigns:
            writer.writerow(campaign)

def main():
    num_campaigns = 20  # Adjust this number as needed
    campaigns = generate_campaigns(num_campaigns)
    save_to_csv(campaigns, '../Generated_CSV/campaigns.csv')
    print(f"Generated {len(campaigns)} campaigns and saved to campaigns.csv")

if __name__ == "__main__":
    main()