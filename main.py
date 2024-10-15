import pandas
from neo4j import GraphDatabase, Driver

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def read_data(file_path: str) -> pandas.DataFrame:
    data=pandas.read_csv(file_path, sep='\t')
    return data

def delete_all_nodes(driver: Driver):
    driver.execute_query(
        "MATCH (n) DELETE n",
        database_="neo4j"
    )
def delete_all_edges(driver: Driver):
    driver.execute_query(
        "MATCH ()-[r]->() DELETE r",
        database_="neo4j"
    )
    
def delete_all_indices(driver: Driver, database: str, kinds):
    with driver.session(database=database) as session:
        # Fetch all constraints
        constraint_query = "SHOW CONSTRAINTS"
        constraints = session.run(constraint_query, database_=database).data()

        dropped_count = 0

        for constraint in constraints:
            # Check if it's a uniqueness constraint
            if constraint['type'] == 'UNIQUENESS':
                # Extract the constraint name
                constraint_name = constraint['name']
                
                # Construct and execute the drop query
                drop_query = f"DROP CONSTRAINT {constraint_name}"
                driver.execute_query(drop_query, database_="neo4j")
                
                dropped_count += 1
                print(f"Dropped constraint: {constraint_name}")

        print(f"Total uniqueness constraints dropped: {dropped_count}")
    
def create_id_indexes(driver: Driver, database: str, unique_kinds: pandas.Series):
    with driver.session(database=database) as session:
        for kind in unique_kinds:
            # Create the index query for the specific kind
            query = f"CREATE CONSTRAINT unique_id_{kind} FOR (n:{kind}) REQUIRE n.id IS UNIQUE"
            session.run(query)
    
def chunk_dataframe(df: pandas.DataFrame, chunk_size: int = 1000):
    """Generator to chunk dataframe into smaller dataframes based on chunk_size"""
    for start in range(0, len(df), chunk_size):
        yield df.iloc[start:start + chunk_size]

def batch_add_nodes_by_kind(driver: Driver, database_: str, kind, nodes):
    query = f"""
            UNWIND $nodes AS node 
            CREATE (n:`{kind}` {{id: node.id, name: node.name}})
            """
    driver.execute_query(
        query,
        nodes=nodes,
        database_=database_,
    )
    
def batch_add_nodes(driver: Driver, database: str, nodes_df: pandas.DataFrame):
    # batch add nodes by kind
    for kind in nodes_df['kind'].unique():
        filtered_nodes = nodes_df[nodes_df['kind'] == kind]
        batch_add_nodes_by_kind(driver, database, kind, filtered_nodes.to_dict(orient='records'))
    
def batch_add_edges(driver: Driver, database: str, edges_df: pandas.DataFrame):
    with driver.session(database=database) as session:
        trans_action = session.begin_transaction()

        for idx, row in edges_df.iterrows():
            source_label = row['source'].split("::")[0]
            target_label = row['target'].split("::")[0]
            statement = f"""
            MATCH (a:`{source_label}` {{id: $source_id}}), (b:`{target_label}` {{id: $target_id}})
            CREATE (a)-[r:`{row['metaedge']}`]->(b)
            """
            trans_action.run(statement, {"source_id": row['source'], "target_id": row['target']})

            if idx % 1000 == 0 and idx > 0:
                trans_action.commit()
                trans_action = session.begin_transaction()
                print(f"Processed {idx} edges")

        trans_action.commit()  # Commit any remaining queries after the loop
    
def get_all_nodes(tx):
    result = tx.run("MATCH (n) RETURN n")
    return [record["n"] for record in result]

if __name__ == '__main__':
    database = "neo4j"
    
    nodes_df = read_data('hetionet/nodes.tsv')
    edges_df = read_data('hetionet/edges.tsv')
        
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        unique_kinds = nodes_df['kind'].unique()
        unique_metaedges = edges_df['metaedge'].unique()
        
        # delete all nodes, edges, indices in db
        delete_all_edges(driver)
        delete_all_nodes(driver)
        delete_all_indices(driver, database, unique_kinds)
                
        create_id_indexes(driver, database, unique_kinds)
        
        batch_add_nodes(driver, database, nodes_df)
        batch_add_edges(driver, database, edges_df)    
            