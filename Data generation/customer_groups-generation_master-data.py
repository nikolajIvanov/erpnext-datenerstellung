import csv


def generate_customer_groups():
    groups = [
        {
            "Customer Group Name": "Wholesale",
            "Parent Customer Group": "All Customer Groups",
            "Is Group": 0,
            "Default Price List": "Standard Selling"
        },
        {
            "Customer Group Name": "Retail",
            "Parent Customer Group": "All Customer Groups",
            "Is Group": 0,
            "Default Price List": "Standard Selling"
        },
        {
            "Customer Group Name": "B2B",
            "Parent Customer Group": "All Customer Groups",
            "Is Group": 0,
            "Default Price List": "Wholesale Price"
        },
        {
            "Customer Group Name": "B2C",
            "Parent Customer Group": "All Customer Groups",
            "Is Group": 0,
            "Default Price List": "Standard Selling"
        }
    ]
    return groups


def save_to_csv(groups, filename):
    fieldnames = [
        "Customer Group Name", "Default Payment Terms Template", "Default Price List",
        "Is Group", "old_parent", "Parent Customer Group"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for group in groups:
            writer.writerow(group)


def main():
    customer_groups = generate_customer_groups()
    save_to_csv(customer_groups, 'customer_groups.csv')
    print(f"Generated {len(customer_groups)} customer groups and saved to velo_gmbh_customer_groups.csv")


if __name__ == "__main__":
    main()