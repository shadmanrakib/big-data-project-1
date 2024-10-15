# big-data-project-1

## installations
Setup Neo4J database (download and configure), create python virtual environment, and install dependencies.

```bash
install python dependencies
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

## requirements
- A python CLI for database creation and queries
- Use at least two types of NoSQL stores (document, graph, key value, column family)
- Document/specifications (in print)
  - design diagram
  - all queries
  - potential improvements (e.g. how to speed up queries)
- All source code set by email
- Two person team

## questions
1. Given a disease id, what is its name,
what are drug names that can treat or
palliate this disease, what are gene
names that cause this disease, and
where this disease occurs? Obtain and
output this information in a single query.

2. We assume that a compound can treat a disease if the
compound up-regulates/down-regulates a gene, but the location down-regulates/up-regulates the gene in an opposite direction where the disease occurs. Find all compounds that can treat a new disease (i.e. the missing edges between compound and disease excluding existing drugs). Obtain and output all drugs in
a single query.

## Queries
MATCH (d:Disease)
WHERE d.id = $diseaseId
// Match compounds that treat or palliate the disease
OPTIONAL MATCH (d)<-[r:CtD|CpD]-(c:Compound)
// Match genes associated with the disease
OPTIONAL MATCH (d)-[:DuG|DdG|DaG]->(g:Gene)
// Match anatomical locations related to the disease
OPTIONAL MATCH (d)-[:DlA]->(a:Anatomy)
RETURN d.name AS disease_name,
       collect(distinct c.name) AS compound_names,
       collect(distinct g.name) AS gene_names,
       collect(distinct a.name) AS anatomy_locations

MATCH (c:Compound)-[cr:CuG]->(g:Gene)<-[ar:AdG]-(a:Anatomy)
MATCH (c)-[cr:CdG]->(g)<-[ar:AuG]-(a)
MATCH (d:Disease)-[lr:DlA]->(a)
WHERE there doesnt exists a (c)-[:CtD]->(d)
RETURN c.name as drug, d.name as disease

MATCH (c:Compound)-[:CuG|CdG]->(g:Gene)<-[:AdG|AuG]-(a:Anatomy)
WHERE (c)-[:CuG]->(g)<-[:AdG]-(a)
   OR (c)-[:CdG]->(g)<-[:AuG]-(a)
MATCH (d:Disease)-[:DlA]->(a)
WHERE NOT EXISTS ((c)-[:CtD]->(d))
RETURN DISTINCT d.name AS disease, collect(DISTINCT c.name) AS drugs



