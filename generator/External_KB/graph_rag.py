from langchain.chains import GraphQAChain
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from  generator.clients import openai_gpt4nano
from langchain_core.documents import Document
from dotenv import load_dotenv
import pickle
import os

load_dotenv()

GRAPH_PATH = "generator/External_KB/graph_kg.pkl"  # where the knowledge graph is saved

def build_graph_knowledge_base(text_path: str):
    with open(text_path, 'r') as file:
        text = file.read()
        # print(content)
    if text is None:
        raise ValueError("No text found")

    # llm = llama3()
    llm = openai_gpt4nano()
    documents = [Document(page_content=text)]
    # print("text:",text)
    # Create graph and transformer
    llm_transformer_filtered = LLMGraphTransformer(
        llm=llm,
        allowed_nodes = [
            "Disease", "Condition", "Symptom", "Sign", "Medication",
            "Treatment", "Intervention", "Test", "AnatomicalSite",
            "PhysiologicalParameter", "Complication", "RiskFactor", "Pathogen"
        ],
        allowed_relationships = [
            "causes", "presents_with", "has_sign", "treated_by", "diagnosed_by",
            "risk_factor_for", "complication_of", "located_in", "contraindicated_with",
            "associated_with", "indicates"
        ],
        strict_mode=False,
    )
    graph_documents_filtered = llm_transformer_filtered.convert_to_graph_documents(documents=documents)

    graph = NetworkxEntityGraph()

    # Add nodes to the graph 
    for node in graph_documents_filtered[0].nodes:
        graph.add_node(node.id) 
    
    # Add edges to the graph
    for edge in graph_documents_filtered[0].relationships:
        graph._graph.add_edge(
            edge.source.id,
            edge.target.id,
            relation=edge.type,
        )
    
    # Save graph to file for later reuse
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(graph, f)

    print(f"Graph created and saved with {graph._graph.nodes} nodes and {graph._graph.edges} edges.")
    print(f"Graph created and saved with {len(graph._graph.nodes)} nodes and {len(graph._graph.edges)} edges.")


def graphrag_qa_chain(llm=None) -> GraphQAChain:
    # Check if the graph file exists
    if not os.path.exists(GRAPH_PATH):      
        raise FileNotFoundError("Knowledge graph file not found. Please run build_graph_knowledge_base() first.")
    with open(GRAPH_PATH, "rb") as f:
        graph: NetworkxEntityGraph = pickle.load(f)
    if llm is None:
        # llm = llama3()  
        llm = openai_gpt4nano()

    chain = GraphQAChain.from_llm(llm=llm, graph=graph)

    return chain
    
    
build_graph_knowledge_base("generator/External_KB/essentials-of-clinical-medicina-kumar-and-clarks.txt")

# chain = graphrag_qa_chain()

# # Step 2: Ask a question
# question = "What is Septic Shock?"
# answer = chain.invoke(question)

# print(f"Answer: {answer}")
