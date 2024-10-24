import csv
import random
from datetime import datetime, timedelta


def generate_campaigns(num_campaigns):
    campaigns = []
    campaign_types = ["Email", "Social Media", "Trade Show", "Print", "Referral"]
    product_lines = ["Regular Bikes", "E-Bikes", "Accessories", "Services"]
    target_audiences = ["B2B", "B2C", "Both"]

    for i in range(num_campaigns):
        campaign_type = random.choice(campaign_types)
        product_line = random.choice(product_lines)
        target_audience = random.choice(target_audiences)

        campaign = {
            "ID": f"CAMP-{i + 1:04d}",
            "Campaign Name": f"{campaign_type} - {product_line} - {target_audience}",
            "Description": f"Campaign targeting {target_audience} customers for {product_line} using {campaign_type} marketing.",
            # Removed "Naming Series" field
        }
        """
        # Generate 1-3 schedules for each campaign
        num_schedules = random.randint(1, 3)
        for j in range(num_schedules):
            campaign[f"ID (Campaign Schedules)"] = f"CAMP-SCH-{i + 1:04d}-{j + 1}"
            # Removed "Email Template (Campaign Schedules)" field
            campaign[f"Send After (days) (Campaign Schedules)"] = random.randint(1, 30)
        """
        campaigns.append(campaign)

    return campaigns


def save_to_csv(campaigns, filename):
    fieldnames = [
        "ID", "Campaign Name", "Description",
        # "ID (Campaign Schedules)", "Send After (days) (Campaign Schedules)"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for campaign in campaigns:
            writer.writerow(campaign)


def main():
    num_campaigns = 20  # Adjust this number as needed
    campaigns = generate_campaigns(num_campaigns)
    save_to_csv(campaigns, '../generated/campaigns.csv')
    print(f"Generated {len(campaigns)} campaigns and saved to campaigns.csv")


if __name__ == "__main__":
    main()