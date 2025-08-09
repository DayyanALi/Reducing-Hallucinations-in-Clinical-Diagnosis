import csv, os
from neo4j import GraphDatabase
from  generator.clients import embedding_model_llama
from langchain.vectorstores import Chroma
from generator.clients import embedding_model_llama, openai_gpt4nano
import pandas as pd
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph 

load_dotenv()

uri  = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
pwd  = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, pwd))

def build_disease_name_index(
    csv_path: str,
    persist_directory: str = "./chroma_db",
    collection_name: str = "disease_names",
):
    df = pd.read_csv(csv_path)  
    diseases = df["disease"].str.strip().unique().tolist()

    metadatas = [{"disease": d} for d in diseases]
    embeddings = embedding_model_llama()

    vectordb = Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    vectordb.add_texts(
        texts=diseases,
        metadatas=metadatas
    )
    vectordb.persist()
    print(f"✅ Indexed {len(diseases)} diseases into '{collection_name}'")

def parse_symptoms(text: str) -> list[str]:
    if "," in text and text.count(",") > 1:
        # comma-delimited list
        parts = [p.strip() for p in text.split(",")]
    else:
        # narrative paragraph → split into sentences
        parts = [s.strip() for s in text.split(".") if s.strip()]
    return [p for p in parts if p]

def build_disease_symptom_KG(csv_path: str):
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"No such file: {csv_path}")

    with driver.session() as session, open(csv_path, newline="", encoding="utf8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            disease = row["disease"].strip()
            symptoms_text = row["text"].strip()
            symptoms = parse_symptoms(symptoms_text)
            for symptom in symptoms:
                session.run(
                    """
                    MERGE (d:Disease {name: $disease})
                    MERGE (s:Symptom {name: $symptom})
                    MERGE (d)-[:HAS_SYMPTOM]->(s)
                    """,
                    disease=disease,
                    symptom=symptom
                )
                
def make_knowledge_graph(csv_path:str):
    build_disease_name_index(csv_path=csv_path)
    build_disease_symptom_KG(csv_path=csv_path)

def get_symptoms_by_disease(
    disease: str,
    persist_directory: str = "./chroma_db",
    collection_name: str = "disease_names",
    k: int = 1
) -> list[str]:
    embeddings = embedding_model_llama()
    vectordb = Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(disease)
    if not docs:
        return []

    canonical = docs[0].metadata["disease"]
    print(f"🔍 Matched '{disease}' → '{canonical}'")

    query = """
    MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)
    RETURN s.name AS symptom
    """
    with driver.session() as session:
        result = session.run(query, name=canonical)
        symptoms = "".join([rec["symptom"] for rec in result])
        return symptoms


# make_knowledge_graph(csv_path="generator/External_KB/symptoms_with_diseases.csv")

# 2) Query
# syms = get_symptoms_by_disease("Anemia")
# # syms = get_symptoms_for_disease("Chronic Arthritis")
# print("Symptoms:", syms)

# driver.close()