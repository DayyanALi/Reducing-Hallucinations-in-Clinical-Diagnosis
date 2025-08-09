from langchain.chains import GraphQAChain
from langchain_experimental.graph_transformers import LLMGraphTransformer
# from langchain_experimental.graph_transformers.llm import DynamicGraph
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from generator.clients import openai_gpt4nano, llama3
from langchain_core.documents import Document
from dotenv import load_dotenv
import pickle
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os

load_dotenv()

GRAPH_PATH = "generator/External_KB/graph_kg.pkl"  # where the knowledge graph is saved

def build_graph_knowledge_base(text_path: str):
    if not os.path.isfile(text_path):
        raise FileNotFoundError(f"No such file: {text_path}")
    with open(text_path, "r", encoding="utf8") as f:
        raw = f.read()
    print("✅ Raw text loaded")
    # documents = [Document(page_content=raw, metadata={"source": text_path})]

    # 2) Wrap in a single Document
    documents = [Document(page_content=raw)]
    # llm = llama3()
    # llm = ChatGroq(model="Gemma2-9b-It")
    # llm = ChatGroq(
    #     model="Gemma2-9b-It",
    #     temperature=0,
    #     functions=[ DynamicGraph.get_openai_schema() ],        # register the function
    #     function_call="auto"                                   # allow auto calls
    # )
    llm = openai_gpt4nano()

    print("text loaded")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000)
    print("splitting text")
    documents = text_splitter.split_documents(documents=documents)
    print("text splitted", len(documents))
    # return

    llm_transformer_filtered = LLMGraphTransformer(llm=llm)
    print("making graph documents")
    graph_documents_filtered = llm_transformer_filtered.convert_to_graph_documents(documents=documents)
    print("done making graph documents")

    graph = NetworkxEntityGraph()

    print("Starting adding nodes and edges")
    # Add nodes to the graph 
    for node in graph_documents_filtered[0].nodes:
        print("Adding node")
        graph.add_node(node.id) 
    
    # Add edges to the graph
    for edge in graph_documents_filtered[0].relationships:
        print("Adding edge")    
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

    chain = GraphQAChain.from_llm(llm=llm, graph=graph, verbose=True)
    # return llm
    return chain
    
    
# build_graph_knowledge_base("generator/External_KB/test_file.txt")
# build_graph_knowledge_base("generator/External_KB/output.txt")


chain = graphrag_qa_chain()

# Step 2: Ask a question
question = "What is Gastroesophageal reflux disease?"
answer = chain.invoke(question)

print(f"Answer: {answer}")
