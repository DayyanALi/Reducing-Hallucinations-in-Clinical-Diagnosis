import csv
import sys
import os
import pickle
from pathlib import Path
from networkx import MultiDiGraph
from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from  generator.clients import llama3, openai_gpt4nano, openai_gpt35
from dotenv import load_dotenv

load_dotenv()

csv.field_size_limit(sys.maxsize)
GRAPH_PATH = Path("generator/External_KB/lit_graph_kg.pkl")

def build_graph_knowledge_base(csv_path: str):
    G = MultiDiGraph()

    with open(csv_path, newline="", encoding="utf8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj       = row["Entity1_name"].strip()
            subj_type  = row["Entity1_type"].strip()
            obj        = row["Entity2_name"].strip()
            obj_type   = row["Entity2_type"].strip()
            rel        = row["relationship_type"].strip()
            
            # if not (subj_type.lower() == "disease" or obj_type.lower() == "Disease"):
            #     continue

            pmids = [p.strip() for p in row["PubMed_ID"].split(",") if p.strip() and p.strip().lower()!="nan"]
            evidence = [s.strip().strip("'") for s in row["Sentence_tokenized"].split("','") if s.strip()]

            # Add nodes (with type attribute)
            G.add_node(subj, type=subj_type)
            G.add_node(obj,  type=obj_type)

            # Add the edge (using the raw relationship_type)
            G.add_edge(
                subj,
                obj,
                relation=rel,
                pmids=pmids,
                evidence=evidence
            )
    with open(GRAPH_PATH, "wb") as out:
        pickle.dump(G, out)
    print(f"✅ Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")


def get_graphrag_qa_chain(llm=None) -> GraphQAChain:
    if not os.path.exists(GRAPH_PATH):
        raise FileNotFoundError(f"Knowledge graph not found at {GRAPH_PATH}. "
                                "Run build_graph_knowledge_base() first.")

    with open(GRAPH_PATH, "rb") as f:
        nx_graph = pickle.load(f)
    kg = NetworkxEntityGraph(nx_graph)
    if llm is None:
        llm = openai_gpt4nano()  # or llama3(), etc.

    chain = GraphQAChain.from_llm(llm=llm, graph=kg)
    return chain

# build_graph_knowledge_base(csv_path="generator/External_KB/raw_PharmKG-180k.csv")

qa_chain = get_graphrag_qa_chain()

question = "Whah is Acute lumbar strain?"
answer = qa_chain.invoke(question)
print("Answer:", answer)    
