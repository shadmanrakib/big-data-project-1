# big-data-project-1

## Installations
Setup Neo4J database (download and configure), create python virtual environment, and install dependencies.

```bash
install python dependencies
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

## How to run cli
```bash
python3 main.py
```
You can provide config input prompts ahead of time too.
```bash
python3 main.py --neo4j_uri=bolt://localhost:7687 --neo4j_user=neo4j --neo4j_password=password --neo4j_database=neo4j --mongodb_uri=mongodb://localhost:27017 --mongodb_database=graphdb
```


## Requirements
- A python CLI for database creation and queries
- Use at least two types of NoSQL stores (document, graph, key value, column family)
- Document/specifications (in print)
  - design diagram
  - all queries
  - potential improvements (e.g. how to speed up queries)
- All source code set by email
- Two person team

## Questions
1. Given a disease id, what is its name,
what are drug names that can treat or
palliate this disease, what are gene
names that cause this disease, and
where this disease occurs? Obtain and
output this information in a single query.

2. We assume that a compound can treat a disease if the
compound up-regulates/down-regulates a gene, but the location 
down-regulates/up-regulates the gene in an opposite direction 
where the disease occurs. Find all compounds that can treat 
a new disease (i.e. the missing edges between compound and disease excluding existing drugs). Obtain and output all drugs in
a single query.

## Queries

### Query 1 (MongoDB)
```python
pipeline = [
        # get disease with matching id
        {"$match": {"id": disease_id, "kind": "Disease"}},
        # find relevant edges
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
	    # find nodes from relevant edges above
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
	   # turn array of results into documents so we can project again
                {"$unwind": "$related_node"},
                 # add necessary info about the node and the relation
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
        # turn array of result into documents so that we can group
        {"$unwind": "$relations"},
        # group the relations based on relation type
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
```

### Query 1 (Neo4j)
```cypher
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
```

### Query 2
```cypher
// get all compounds that can have potential to do opposite of some anatomy on a gene
MATCH (c:Node {kind: "Compound"})-[:CuG|CdG]->(g:Node {kind: "Gene"})<-[:AdG|AuG]-(a:Node {kind: "Anatomy"})
// narrow to down to just the opposite
WHERE (c)-[:CuG]->(g)<-[:AdG]-(a)
  OR (c)-[:CdG]->(g)<-[:AuG]-(a)
MATCH (d {kind: "Disease", id: $diseaseId})-[:DlA]->(a)
// make sure the compound is a new one
WHERE NOT EXISTS ((c)-[:CtD]->(d))
RETURN DISTINCT c.name as drug_name, c.id as drug_id
```

