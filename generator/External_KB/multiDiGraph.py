# import csv
# import sys
# import os
# import pickle
# from pathlib import Path
# from networkx import MultiDiGraph
# from langchain.chains import GraphQAChain
# from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
# from  generator.clients import llama3, openai_gpt4nano, openai_gpt35
# from dotenv import load_dotenv

# load_dotenv()

# csv.field_size_limit(sys.maxsize)
# GRAPH_PATH = Path("generator/External_KB/lit_graph_kg.pkl")

# def build_graph_knowledge_base(csv_path: str):
#     G = MultiDiGraph()

#     with open(csv_path, newline="", encoding="utf8") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             subj       = row["Entity1_name"].strip()
#             subj_type  = row["Entity1_type"].strip()
#             obj        = row["Entity2_name"].strip()
#             obj_type   = row["Entity2_type"].strip()
#             rel        = row["relationship_type"].strip()
            
#             # if not (subj_type.lower() == "disease" or obj_type.lower() == "Disease"):
#             #     continue

#             pmids = [p.strip() for p in row["PubMed_ID"].split(",") if p.strip() and p.strip().lower()!="nan"]
#             evidence = [s.strip().strip("'") for s in row["Sentence_tokenized"].split("','") if s.strip()]
#             rel = rel + evidence
#             # Add nodes (with type attribute)
#             G.add_node(subj, type=subj_type)
#             G.add_node(obj,  type=obj_type)

#             # Add the edge (using the raw relationship_type)
#             G.add_edge(
#                 subj,
#                 obj,
#                 relation=rel,
#                 pmids=pmids,
#                 evidence=evidence
#             )
#     with open(GRAPH_PATH, "wb") as out:
#         pickle.dump(G, out)
#     print(f"✅ Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")


# def get_graphrag_qa_chain(llm=None) -> GraphQAChain:
#     if not os.path.exists(GRAPH_PATH):
#         raise FileNotFoundError(f"Knowledge graph not found at {GRAPH_PATH}. "
#                                 "Run build_graph_knowledge_base() first.")

#     with open(GRAPH_PATH, "rb") as f:
#         nx_graph = pickle.load(f)
#     kg = NetworkxEntityGraph(nx_graph)
#     if llm is None:
#         llm = openai_gpt4nano()  # or llama3(), etc.

#     chain = GraphQAChain.from_llm(llm=llm, graph=kg)
#     return chain

# build_graph_knowledge_base(csv_path="generator/External_KB/raw_PharmKG-180k.csv")

# # qa_chain = get_graphrag_qa_chain()

# # question = "Whah is Ovarian Cancer?"
# # answer = qa_chain.invoke(question)
# # print("Answer:", answer)    



import csv, sys, pickle, os
from pathlib import Path
from networkx import MultiDiGraph
from dotenv import load_dotenv

from langchain.chains import GraphQAChain
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from generator.clients import openai_gpt4nano

load_dotenv()
csv.field_size_limit(sys.maxsize)

GRAPH_PATH = Path("generator/External_KB/lit_graph_kg.pkl")

def build_graph_knowledge_base(csv_path: str):
    G = MultiDiGraph()
    with open(csv_path, newline="", encoding="utf8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj, subj_type = row["Entity1_name"].strip(), row["Entity1_type"].strip()
            obj,  obj_type  = row["Entity2_name"].strip(), row["Entity2_type"].strip()
            rel             = row["relationship_type"].strip()

            pmids = [p.strip() for p in row["PubMed_ID"].split(",") 
                     if p.strip() and p.strip().lower()!="nan"]
            evidence = [s.strip().strip("'") for s in row["Sentence_tokenized"]
                        .split("','") if s.strip() and s.strip().lower()!="nan"]

            G.add_node(subj, type=subj_type)
            G.add_node(obj,  type=obj_type)

            if G.has_edge(subj, obj):
                data = G[subj][obj][0]
                data["pmids"]    = list(dict.fromkeys(data["pmids"] + pmids))
                data["evidence"] = list(dict.fromkeys(data["evidence"] + evidence))
            else:
                G.add_edge(subj, obj,
                           relation=rel,
                           pmids=pmids,
                           evidence=evidence)

    with open(GRAPH_PATH, "wb") as out:
        pickle.dump(G, out)
    print(f"✅ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

def get_graphrag_qa_chain(llm=None) -> GraphQAChain:
    if not GRAPH_PATH.exists():
        raise FileNotFoundError("Run build_graph_knowledge_base() first.")
    with open(GRAPH_PATH, "rb") as f:
        nx_graph = pickle.load(f)
    kg = NetworkxEntityGraph(nx_graph)
    llm = llm or openai_gpt4nano()

    # Custom QA prompt that uses {context}
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are a medical QA assistant.  Use only the following facts (with evidence sentences)
        to answer the user’s question.  Cite evidence where appropriate. If no facts are provided to you then just return that no Context was provided.
        """),
                ("human", """
        Context (one fact per line, with evidence in parentheses):

        {context}

        Question: {question}
        """),
    ])

    return GraphQAChain.from_llm(
        llm=llm,
        graph=kg,
        qa_prompt=qa_prompt
    )
    
def node_exists(node_name:str):    
    # 1) Load your pickled graph
    with open(GRAPH_PATH, "rb") as f:
        nx_graph = pickle.load(f)

    # 2) Wrap it in the LangChain retriever
    kg = NetworkxEntityGraph(nx_graph)

    # 3a) Check with `has_node()`
    if kg._graph.has_node(node_name):
        print("✅ Node exists!")
    else:
        print("❌ Node not found.")

    # 3b) Or with the `in` operator


def format_fact_line(fact: dict) -> str:
    subj, rel, obj = fact["source"], fact["relation"], fact["target"]
    ev = fact.get("evidence", [])
    if ev:
        return f"{subj} – {rel} – {obj} (Evidence: {'; '.join(ev)})"
    else:
        return f"{subj} – {rel} – {obj}"

def get_relevant_context(question: str) -> str:
    # 1) Load and wrap your graph
    if not GRAPH_PATH.exists():
        raise FileNotFoundError("Run build_graph_knowledge_base() first.")
    with open(GRAPH_PATH, "rb") as f:
        nx_graph = pickle.load(f)
    kg = NetworkxEntityGraph(nx_graph)

    # 2) Naïvely match any node name appearing in the question (case‐insensitive)
    q_lower = question.lower()
    matched_entities = [
        node for node in kg._graph.nodes
        if node.lower() in q_lower
    ]

    # 3) Fetch all facts for those entities
    facts = []
    for ent in matched_entities:
        facts.extend(kg.get_entity_knowledge(ent))

    # 4) Deduplicate triples by (source, relation, target)
    seen = set()
    unique_facts = []
    for f in facts:
        key = (f["source"], f["relation"], f["target"])
        if key not in seen:
            seen.add(key)
            unique_facts.append(f)

    # 5) Format as one line per fact
    if not unique_facts:
        return "No relevant context found for that question."
    lines = [format_fact_line(f) for f in unique_facts]
    return "\n".join(lines)

# ─── Usage ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    q = "Which drugs are known to treat hypertension?"
    print("=== Question ===\n", q)
    print("\n=== Context ===\n", get_relevant_context(q))


# if __name__ == "__main__":
#     # 1) Uncomment to (re)build your graph:
#     # build_graph_knowledge_base("generator/External_KB/raw_PharmKG-180k.csv")

#     # 2) Load the chain and ask
#     # chain = get_graphrag_qa_chain()
#     q = "arrhythmias cardiac"
#     # print("Q:", q)
#     # print("A:", chain.invoke(q))
    
#     chain = get_graphrag_qa_chain()
#     chain.verbose = True
#     result = chain.invoke(q)
#     print("result",result)
    
#     # node_name = "hamartoma syndrome multiple"
#     # node_exists(node_name=node_name)
#     # node_to_check = "Metformin"
#     # exists = node_to_check in kg._graph.nodes
#     # print(f"{node_to_check} exists? {exists}")


