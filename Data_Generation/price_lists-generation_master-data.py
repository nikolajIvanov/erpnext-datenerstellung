import csv


def generate_price_lists():
    price_lists = [
        {
            "Currency": "EUR",
            "Price List Name": "Standard Selling",
            "Buying": 0,
            "Enabled": 1,
            "Price Not UOM Dependent": 0,
            "Selling": 1
        },
        {
            "Currency": "EUR",
            "Price List Name": "Wholesale Price",
            "Buying": 0,
            "Enabled": 1,
            "Price Not UOM Dependent": 0,
            "Selling": 1
        },
        {
            "Currency": "EUR",
            "Price List Name": "Standard Buying",
            "Buying": 1,
            "Enabled": 1,
            "Price Not UOM Dependent": 0,
            "Selling": 0
        }
    ]
    return price_lists


def save_to_csv(price_lists, filename):
    fieldnames = [
        "Currency", "Price List Name", "Buying", "Enabled",
        "Price Not UOM Dependent", "Selling"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for price_list in price_lists:
            writer.writerow(price_list)


def main():
    price_lists = generate_price_lists()
    save_to_csv(price_lists, '../Generated_CSV/price_lists.csv')
    print(f"Generated {len(price_lists)} price lists and saved to price_lists.csv")


if __name__ == "__main__":
    main()