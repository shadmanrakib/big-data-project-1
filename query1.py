from pymongo import MongoClient
from bson import ObjectId

def get_disease_relations(mongo_uri, database_name, disease_id):
    client = MongoClient(mongo_uri)
    #with MongoClient(mongo_uri) as client:
    db = client[database_name]
    #disease_id = ObjectId('670ef4694c8d47ed14846cc0')

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
                        {"$match": {"$expr": {"$eq": ["$id", "$$related_id"]}}},
                        {"$project": {"id": 1, "kind": 1, "name": 1}}
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
            "name": "$_id.name",
            "kind": "$_id.kind",
            "related_nodes": 1
        }}
    ]

    #print(list(db.nodes.find({ "id": disease_id, "kind": "Disease" })))

    result = list(db.nodes.aggregate(pipeline))

    client.close()

    return result[0] if result else None

if __name__ == "__main__":
    mongo_uri = "mongodb://localhost:27017"
    database_name = "myTestDB"
    disease_id = "Disease::DOID:0050156"

    result = get_disease_relations(mongo_uri, database_name, disease_id)
    if result:
        print(f"Disease ID: {result['id']}")
        print(f"Disease Kind: {result['kind']}")
        print("Related Nodes:")
        for relation in result['related_nodes']:
            print(f"  Relation Type: {relation['relation_type']}")
            print(f"    - ID: {relation['related_node']['id']}, Kind: {relation['related_node']['kind']}")
    else:
        print("No results found.")