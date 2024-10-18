import click
from neo4j import GraphDatabase
from pymongo import MongoClient

from queries import get_new_treatments, get_disease_info_mongodb
from setup_dbs import setup_dbs

@click.command()
@click.option('--neo4j_uri', prompt='Neo4j URI', help='The URI to connect to Neo4j (ex: bolt://localhost:7687)')
@click.option('--neo4j_user', prompt='Neo4j Username', help='Neo4j username (ex: neo4j)')
@click.option('--neo4j_password', prompt='Neo4j Password', hide_input=True, help='Neo4j password')
@click.option('--neo4j_database', prompt='Neo4j Database name', help='Neo4j database name (ex: neo4j)')
@click.option('--mongodb_uri', prompt='MongoDB URI', help='MongoDB URI (ex: mongodb://localhost:27017)')
@click.option('--mongodb_database', prompt='MongoDB Database name', help='MongoDB database name (ex: graphdb)')
def cli(neo4j_uri, neo4j_user, neo4j_password, neo4j_database, mongodb_uri, mongodb_database):
    with GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
        with driver.session(database=neo4j_database) as session:
            client = MongoClient(mongodb_uri)
            db = client[mongodb_database]
                        
            while True:
                click.echo("\nChoose an option:")
                click.echo("1. Build database")
                click.echo("2. Get disease info")
                click.echo("3. Get new treatments")
                click.echo("4. Exit")
                
                choice = click.prompt("Enter your choice", type=int)
                
                if choice == 1:
                    nodes_filepath = click.prompt("Enter the filepath for nodes", 
                                                default="hetionet/nodes.tsv", 
                                                show_default=True)
                    edges_filepath = click.prompt("Enter the filepath for edges", 
                                                default="hetionet/edges.tsv", 
                                                show_default=True)
                    setup_dbs(db, session, nodes_filepath, edges_filepath)
                elif choice == 2 or choice == 3:
                    disease_id = click.prompt("Enter disease ID (ex: Disease::DOID:0050156)", type=str)
                    if choice == 2:
                        results = get_disease_info_mongodb(db, disease_id)
                        click.echo("\nResults:")
                        if results:
                            click.echo(results)
                        else:
                            click.echo("No results found.")
                    else:
                        results = get_new_treatments(session, disease_id)
                        click.echo("\nResults:")
                        if results:
                            for result in results:
                                click.echo(result)
                            count = len(results)
                            click.echo(f"Count {count}")
                        else:
                            click.echo("No results found.")
                elif choice == 4:
                    break
                else:
                    click.echo("Invalid choice. Please try again.")

            client.close()
if __name__ == '__main__':
    cli()

            
