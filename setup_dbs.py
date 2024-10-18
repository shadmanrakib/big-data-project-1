import pandas as pd
from neo4j import GraphDatabase, Session
from pymongo import MongoClient

#prob don't need, since all data coming from MongoDB insted of tsv files
def read_data(file_path: str) -> pd.DataFrame:
    data=pd.read_csv(file_path, sep='\t')
    return data

def delete_all_nodes(session: Session):
    session.run(        
        "MATCH (n) DELETE n"
    )
def delete_all_edges(session: Session):
    session.run(
        "MATCH ()-[r]->() DELETE r"
    )
    
def delete_all_indices(session: Session):
    # Fetch all constraints
    constraint_query = "SHOW CONSTRAINTS"
    constraints = session.run(constraint_query).data()

    for constraint in constraints:
        # Check if it's a uniqueness constraint
        if constraint['type'] == 'UNIQUENESS':
            # Extract the constraint name
            constraint_name = constraint['name']
            
            # Construct and execute the drop query
            drop_query = f"DROP CONSTRAINT {constraint_name}"
            session.run(drop_query)
            
    # drop kind index
    drop_kind_query = "DROP INDEX node_kind_index IF EXISTS"
    session.run(drop_kind_query)
                                
def create_index(session: Session):
    # Create the index query
    queries = [
        "CREATE CONSTRAINT unique_id FOR (n:Node) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX node_kind_index FOR (n:Node) ON (n.kind)"
    ]
    for query in queries:
        session.run(query)

def batch_add_nodes(session: Session, nodes_df: pd.DataFrame):
    query = f"""
            UNWIND $nodes AS node 
            CREATE (n:Node {{id: node.id, name: node.name, kind: node.kind}})
            """
    session.run(
        query,
        nodes=nodes_df.to_dict(orient='records'),
    )
    
def batch_add_edges(session: Session, edges_df: pd.DataFrame):
    for metaedge in edges_df['metaedge'].unique():
        filtered_df = edges_df[edges_df["metaedge"] == metaedge]
        statement = f"""
        UNWIND $edges as edge
        MATCH (a:Node {{id: edge.source}}), (b:Node {{id: edge.target}})
        CREATE (a)-[r:`{metaedge}`]->(b)
        """
        session.run(statement, edges=filtered_df.to_dict(orient='records'))
        
def setup_neo4j_db(session: Session, nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    # delete all nodes, edges, index in db
    print("STARTING to delete edges, nodes, indices")
    delete_all_edges(session)
    delete_all_nodes(session)
    delete_all_indices(session)
    print("FINISHED deleting edges, nodes, indices")
    
    # create index, nodes, and edges
    print("STARTING to create index, nodes, and edges")
    create_index(session)
    batch_add_nodes(session, nodes_df)
    batch_add_edges(session, edges_df)    
    print("FINISHED creating index, nodes, and edges")
    

def setup_mongo_db(db, nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    print("STARTING to fetch data from MongoDB")
    
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
    
    print("FINISHED fetching data from MongoDB")
    
def setup_dbs(mongodb, neo4j_session: Session, nodes_filepath: str, edges_filepath: str):
    nodes_df = read_data(nodes_filepath)
    edges_df = read_data(edges_filepath)
    
    setup_mongo_db(mongodb, nodes_df, edges_df)
    setup_neo4j_db(neo4j_session, nodes_df, edges_df)