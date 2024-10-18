from neo4j import Session

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
    return records

def get_disease_info_neo4j(session: Session, disease_id: str):
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

def get_disease_info_mongodb(db, disease_id: str):
    pipeline = [
        {"$match": {"id": disease_id, "kind": "Disease"}},
        {"$lookup": {
            "from": "edges",
            "let": {"node_id": "$id"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$or": [
                            {"$eq": ["$source", "$$node_id"]},
                            {"$eq": ["$target", "$$node_id"]}
                        ]
                    }
                }},
                {"$lookup": {
                    "from": "nodes",
                    "let": {"related_id": {"$cond": [{"$eq": ["$source", "$$node_id"]}, "$target", "$source"]}},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$id", "$$related_id"]}
                        }}
                    ],
                    "as": "related_node"
                }},
                {"$unwind": "$related_node"},
                {"$project": {
                    "relation_type": "$metaedge",
                    "related_node": {
                        "id": "$related_node.id",
                        "kind": "$related_node.kind",
                        "name": "$related_node.name"
                    }
                }}
            ],
            "as": "relations"
        }},
        {"$unwind": "$relations"},
        {"$group": {
            "_id": {
                "id": "$id",
                "kind": "$kind",
                "name": "$name"
            },
            "compounds": {
                "$addToSet": {
                    "$cond": [
                        {"$in": ["$relations.relation_type", ["CtD", "CpD"]]},
                        "$relations.related_node.name",
                        "$$REMOVE"
                    ]
                }
            },
            "genes": {
                "$addToSet": {
                    "$cond": [
                        {"$eq": ["$relations.relation_type", "DaG"]},
                        "$relations.related_node.name",
                        "$$REMOVE"
                    ]
                }
            },
            "anatomy": {
                "$addToSet": {
                    "$cond": [
                        {"$eq": ["$relations.relation_type", "DlA"]},
                        "$relations.related_node.name",
                        "$$REMOVE"
                    ]
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "disease_name": "$_id.name",
            "compound_names": "$compounds",
            "gene_names": "$genes",
            "anatomy_locations": "$anatomy"
        }}
    ]
    
    result = list(db.nodes.aggregate(pipeline))

    return result[0] if result else None