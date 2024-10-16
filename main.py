import pandas
from neo4j import GraphDatabase, Driver, Session

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
DATABASE = "neo4j"

def read_data(file_path: str) -> pandas.DataFrame:
    data=pandas.read_csv(file_path, sep='\t')
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
                                
def create_index(session: Session):
    # Create the index query
    query = f"CREATE CONSTRAINT unique_id FOR (n:Node) REQUIRE n.id IS UNIQUE"
    session.run(query)

def batch_add_nodes(session: Session, nodes_df: pandas.DataFrame):
    query = f"""
            UNWIND $nodes AS node 
            CREATE (n:Node {{id: node.id, name: node.name, kind: node.kind}})
            """
    session.run(
        query,
        nodes=nodes_df.to_dict(orient='records'),
    )
    
def batch_add_edges(session: Session, edges_df: pandas.DataFrame):
    for metaedge in edges_df['metaedge'].unique():
        filtered_df = edges_df[edges_df["metaedge"] == metaedge]
        statement = f"""
        UNWIND $edges as edge
        MATCH (a:Node {{id: edge.source_id}}), (b:Node {{id: edge.target_id}})
        CREATE (a)-[r:`{metaedge}`]->(b)
        """
        session.run(statement, edges=filtered_df)
    
def get_all_nodes(tx):
    result = tx.run("MATCH (n) RETURN n")
    return [record["n"] for record in result]

def setup_neo4j_db(uri: str, auth: str, database: str, nodes_df: pandas.DataFrame, edges_df: pandas.DataFrame):
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session(database=database) as session:     
            # delete all nodes, edges, index in db
            delete_all_edges(session)
            delete_all_nodes(session)
            delete_all_indices(session)
            
            # create index, nodes, and edges
            create_index(session)
            batch_add_nodes(session, nodes_df)
            batch_add_edges(session, edges_df)    

if __name__ == '__main__':    
    nodes_df = read_data('hetionet/nodes.tsv')
    edges_df = read_data('hetionet/edges.tsv')
    
    setup_neo4j_db(URI, AUTH, DATABASE, nodes_df, edges_df)

            