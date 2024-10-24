import csv
import os


def convert_csv_delimiter(input_file, output_file):
    """
    Convert a semicolon-delimited CSV file to a comma-delimited CSV file.

    Args:
        input_file (str): Path to the input CSV file (semicolon-delimited)
        output_file (str): Path to the output CSV file (comma-delimited)
    """
    try:
        # Read the semicolon-delimited CSV file
        with open(input_file, 'r', encoding='utf-8') as infile:
            # Use semicolon as delimiter for reading
            reader = csv.DictReader(infile, delimiter=';')

            # Get the fieldnames from the reader
            fieldnames = reader.fieldnames

            # Read all rows
            rows = list(reader)

        # Write to the new CSV file with comma delimiter
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            # Use comma as delimiter for writing
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write all rows
            writer.writerows(rows)

        print(f"Successfully converted {input_file} to {output_file}")

    except Exception as e:
        print(f"Error converting file {input_file}: {str(e)}")


def main():
    # Define the input and output files
    files_to_convert = [
        ('bom_bike.csv', 'bom_bike.csv'),
        ('bom_ebike.csv', 'bom_ebike.csv')
    ]

    # Get the current directory
    current_dir = os.getcwd()

    # Process each file
    for input_name, output_name in files_to_convert:
        input_path = os.path.join(current_dir, input_name)
        output_path = os.path.join(current_dir, output_name)

        if os.path.exists(input_path):
            convert_csv_delimiter(input_path, output_path)
        else:
            print(f"Input file not found: {input_path}")


if __name__ == "__main__":
    main()