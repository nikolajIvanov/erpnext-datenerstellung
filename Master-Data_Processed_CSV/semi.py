import pandas as pd

# Load the CSV file with semicolon separation
file_path = 'bom.csv'
df = pd.read_csv(file_path, sep=';')

# Save the CSV file with comma separation
new_file_path = 'bom.csv'
df.to_csv(new_file_path, sep=',', index=False)

new_file_path