import pandas as pd

# Use the correct file paths
tsv_file = 'C:/Users/nurul/Downloads/hetionet/edges.tsv' 
json_file = 'C:/Users/nurul/Downloads/edges.json'

# Convert TSV to JSON
df = pd.read_csv(tsv_file, sep='\t')
df.to_json(json_file, orient='records', lines=True)

print(f"TSV file has been successfully converted to JSON and saved as {json_file}")
