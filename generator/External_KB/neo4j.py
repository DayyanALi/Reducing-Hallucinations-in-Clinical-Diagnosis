
import csv, sys, os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import csv, sys
from  generator.clients import llama3, openai_gpt4nano, openai_gpt35
from langchain.chains import GraphQAChain
from langchain.graphs.neo4j_graph import Neo4jGraph

csv.field_size_limit(sys.maxsize)
load_dotenv()
URI  = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PW   = os.getenv("NEO4J_PW", "password")

driver = GraphDatabase.driver(URI, auth=(USER, PW))

def build_graph_to_neo4j(csv_path: str):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        with open(csv_path, newline="", encoding="utf8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                subj, subj_type = row["Entity1_name"].strip(), row["Entity1_type"].strip()
                obj,  obj_type  = row["Entity2_name"].strip(), row["Entity2_type"].strip()
                rel = row["relationship_type"].strip()
                
                if not (subj_type.lower() == "disease" or obj_type.lower() == "Disease"):
                    continue

                pmids = [p.strip() for p in row["PubMed_ID"].split(",") if p.strip() and p.strip().lower()!="nan"]
                evidence = [s.strip().strip("'") for s in row["Sentence_tokenized"].split("','") if s.strip()]

                session.run(
                    """
                    MERGE (a:Entity {name: $subj, type: $subj_type})
                    MERGE (b:Entity {name: $obj,  type: $obj_type})
                    MERGE (a)-[r:RELATION {relation: $rel}]->(b)
                      ON CREATE SET r.pmids = $pmids, r.evidence = $evidence
                      ON MATCH  SET 
                        r.pmids     = r.pmids     + $pmids,
                        r.evidence  = r.evidence  + $evidence
                    """,
                    subj=subj, subj_type=subj_type,
                    obj=obj,   obj_type=obj_type,
                    rel=rel, pmids=pmids, evidence=evidence
                )
    print("✅ Ingest complete!")
    

def get_neo4j_qa_chain(llm=None) -> GraphQAChain:
    if llm is None:
        llm = openai_gpt4nano()   # or llama3(), ChatOpenAI, etc.

    graph = Neo4jGraph(
        url=URI,
        username=USER,
        password=PW,
    )
    return GraphQAChain.from_llm(llm=llm, graph=graph)

# build_graph_to_neo4j("generator/External_KB/raw_PharmKG-180k.csv")
# driver.close()

qa_chain = get_neo4j_qa_chain()

# ask questions
print( qa_chain.run("Which medications treat hypertension?") )
print( qa_chain.run("What genes interact_with aspirin?") )

