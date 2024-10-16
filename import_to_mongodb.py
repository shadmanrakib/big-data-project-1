import pandas as pd
from pymongo import MongoClient
import pymongo

# Paths to the files
nodes_file = 'C:/Users/nurul/Downloads/hetionet/nodes.tsv'
edges_file = 'C:/Users/nurul/Downloads/hetionet/edges.tsv'

# Load TSV files into pandas DataFrames
nodes_df = pd.read_csv(nodes_file, sep='\t')
edges_df = pd.read_csv(edges_file, sep='\t')

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['graphdb']

# Drop collections if they already exist
db.nodes.drop()
db.edges.drop()

# Insert nodes into the 'nodes' collection
nodes_collection = db['nodes']
nodes_data = nodes_df.to_dict(orient='records')
nodes_collection.insert_many(nodes_data)

# Insert edges into the 'edges' collection
edges_collection = db['edges']
edges_data = edges_df.to_dict(orient='records')
edges_collection.insert_many(edges_data)

print("Data has been successfully imported into MongoDB.")
