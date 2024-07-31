import csv
from faker import Faker

# Initialize Faker for German locale
fake = Faker('de_DE')


def generate_sales_structure():
    territories = ["Germany", "Austria", "Switzerland"]
    sales_directors = []
    sales_managers = []
    sales_reps = []
    territory_data = []

    # Create a top-level sales director
    sales_director = {
        "Sales Person Name": fake.name(),
        "Is Group": 1,
        "Commission Rate": round(fake.random.uniform(7, 9), 2),
        "Department": "Sales",
        "Employee": "",
        "Enabled": 1,
        "Parent Sales Person": ""
    }
    sales_directors.append(sales_director)

    for territory in territories:
        # Generate one Regional Sales Manager for each territory
        regional_manager = {
            "Sales Person Name": fake.name(),
            "Is Group": 1,
            "Commission Rate": round(fake.random.uniform(5, 7), 2),
            "Department": "Sales",
            "Employee": "",
            "Enabled": 1,
            "Parent Sales Person": sales_director["Sales Person Name"]
        }
        sales_managers.append(regional_manager)

        # Generate Territory data
        territory_info = {
            "Territory Name": territory,
            "Is Group": 0,
            "Parent Territory": "All Territories",
            "Territory Manager": regional_manager["Sales Person Name"]
        }
        territory_data.append(territory_info)

        # Generate 3 Sales Representatives for each territory
        for _ in range(3):
            sales_rep = {
                "Sales Person Name": fake.name(),
                "Is Group": 0,
                "Commission Rate": round(fake.random.uniform(1, 3), 2),
                "Department": "Sales",
                "Employee": "",
                "Enabled": 1,
                "Parent Sales Person": regional_manager["Sales Person Name"]
            }
            sales_reps.append(sales_rep)

    return sales_directors, sales_managers, sales_reps, territory_data


def save_to_csv(data, filename, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            # Fill in empty values for fields not generated
            for field in fieldnames:
                if field not in item:
                    item[field] = ""
            writer.writerow(item)


def main():
    sales_person_fields = [
        "Sales Person Name", "Is Group", "Commission Rate", "Department",
        "Employee", "Enabled", "old_parent", "Parent Sales Person",
        "ID (Targets)", "Fiscal Year (Targets)", "Item Group (Targets)",
        "Target  Amount (Targets)", "Target Distribution (Targets)", "Target Qty (Targets)"
    ]

    territory_fields = [
        "Territory Name", "Is Group", "old_parent", "Parent Territory",
        "Territory Manager", "ID (Targets)", "Fiscal Year (Targets)",
        "Item Group (Targets)", "Target  Amount (Targets)",
        "Target Distribution (Targets)", "Target Qty (Targets)"
    ]

    sales_directors, sales_managers, sales_reps, territories = generate_sales_structure()

    save_to_csv(sales_directors, '../Generated_CSV/sales_directors.csv', sales_person_fields)
    save_to_csv(sales_managers, '../Generated_CSV/sales_managers.csv', sales_person_fields)
    save_to_csv(sales_reps, '../Generated_CSV/sales_reps.csv', sales_person_fields)
    save_to_csv(territories, '../Generated_CSV/territories.csv', territory_fields)

    print(f"Generated {len(sales_directors)} sales directors and saved to sales_directors.csv")
    print(f"Generated {len(sales_managers)} sales managers and saved to sales_managers.csv")
    print(f"Generated {len(sales_reps)} sales representatives and saved to sales_reps.csv")
    print(f"Generated {len(territories)} territories and saved to territories.csv")


if __name__ == "__main__":
    main()