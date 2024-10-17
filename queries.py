from neo4j import Session
from pymongo import MongoClient
from bson import ObjectId

def get_disease_info(session: Session, disease_id: str):
    query = """
    MATCH (d:Node {kind: "Disease", id: $diseaseId})
    // Match compounds that treat or palliate the disease
    OPTIONAL MATCH (d)<-[r:CtD|CpD]-(c:Node {kind: "Compound"})
    // Match genes associated with the disease
    OPTIONAL MATCH (d)-[:DaG]->(g:Node {kind: "Gene"})
    // Match anatomical locations related to the disease
    OPTIONAL MATCH (d)-[:DlA]->(a:Node {kind: "Anatomy"})
    RETURN d.name AS disease_name,
        collect(distinct c.name) AS compound_names,
        collect(distinct g.name) AS gene_names,
        collect(distinct a.name) AS anatomy_locations
    """
    result = session.run(query, diseaseId=disease_id)
    records = [record.data() for record in result]
    return records, len(records)

def get_new_treatments(session: Session, disease_id: str):
    query = """
    // get all compounds that can have potential to do opposite of some anatomy on a gene
    MATCH (c:Node {kind: "Compound"})-[:CuG|CdG]->(g:Node {kind: "Gene"})<-[:AdG|AuG]-(a:Node {kind: "Anatomy"})
    // narrow to down to just the opposite
    WHERE (c)-[:CuG]->(g)<-[:AdG]-(a)
        OR (c)-[:CdG]->(g)<-[:AuG]-(a)
    MATCH (d {kind: "Disease", id: $diseaseId})-[:DlA]->(a)
    // make sure the compound is a new one
    WHERE NOT EXISTS ((c)-[:CtD]->(d))
    RETURN DISTINCT c.name as drug_name, c.id as drug_id
    """
    result = session.run(query, diseaseId=disease_id)
    records = [record.data() for record in result]
    return records, len(records)

def get_disease_relations(mongo_uri, database_name, disease_id):
    """Fetch related nodes for a given disease from MongoDB."""
    with MongoClient(mongo_uri) as client:
        db = client[database_name]

        pipeline = [
            {"$match": {"id": disease_id, "kind": "Disease"}},
            {"$lookup": { 
                "from": "edges",
                "let": {"node_id": "$id"},
                "pipeline": [
                    {"$match": 
                        {"$expr": 
                            {"$or": [
                                {"$eq": ["$source", "$$node_id"]},
                                {"$eq": ["$target", "$$node_id"]}
                            ]}
                        }
                    },
                    {"$lookup": {
                        "from": "nodes",
                        "let": {"related_id": {"$cond": [{"$eq": ["$source", "$$node_id"]}, "$target", "$source"]}},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$id", "$$related_id"]}}}
                        ],
                        "as": "related_node"
                    }},
                    {"$unwind": "$related_node"},
                    {"$project": {
                        "relation_type": "$metaedge",
                        "related_node": { 
                            "id": "$related_node.id",
                            "kind": "$related_node.kind"
                        }
                    }}
                ],
                "as": "relations"
            }},
            {"$unwind": "$relations"},
            {"$group": {
                "_id": {
                    "id": "$id",
                    "kind": "$kind"
                },
                "related_nodes": {
                    "$push": {
                        "relation_type": "$relations.relation_type",
                        "related_node": "$relations.related_node"
                    }
                }
            }},
            {"$project": {
                "_id": 0,
                "id": "$_id.id",
                "kind": "$_id.kind",
                "related_nodes": 1
            }}
        ]

        try:
            result = list(db.nodes.aggregate(pipeline))
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
            return None

        return result[0] if result else None