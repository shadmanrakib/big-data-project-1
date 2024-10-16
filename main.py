import click
from neo4j import GraphDatabase

from queries import get_disease_info, get_new_treatments
from setup_dbs import setup_dbs

@click.command()
@click.option('--uri', prompt='Neo4j URI', help='The URI to connect to Neo4j (ex: bolt://localhost:7687)')
@click.option('--user', prompt='Neo4j Username', help='Neo4j username (ex: neo4j)')
@click.option('--password', prompt='Neo4j Password', hide_input=True, help='Neo4j password')
@click.option('--database', prompt='Neo4j Database name', help='Neo4j database name (ex: neo4j)')
def cli(uri, user, password, database):
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        with driver.session(database=database) as session:
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
                    setup_dbs(session, nodes_filepath, edges_filepath)
                elif choice == 2 or choice == 3:
                    disease_id = click.prompt("Enter disease ID (ex: Disease::DOID:0050156)", type=str)
                    if choice == 2:
                        results, count = get_disease_info(session, disease_id)
                    else:
                        results, count = get_new_treatments(session, disease_id)
                    
                    if results:
                        click.echo("\nResults:")
                        for result in results:
                            click.echo(result)
                        click.echo(f"\nCount: {count}")
                    else:
                        click.echo("No results found.")
                elif choice == 4:
                    break
                else:
                    click.echo("Invalid choice. Please try again.")
        
if __name__ == '__main__':
    cli()

            