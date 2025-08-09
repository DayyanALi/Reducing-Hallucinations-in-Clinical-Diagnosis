from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from generator.clients import embedding_model_llama, openai_gpt4nano
from utils.utils import load_documents, split_documents
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from dotenv import load_dotenv

load_dotenv()

def build_vectorDB(file_path:str):
    documents = load_documents(file_path=file_path)
    docs = split_documents(documents=documents, chunk_size=300)
    
    embeddings = embedding_model_llama()
    vectordb = Chroma(
        persist_directory="./chroma_db",
        collection_name="medical_context",
        embedding_function=embeddings
    )
    vectordb.add_documents(docs)
    vectordb.persist()

def load_vector_retriever(
    persist_directory: str = "./chroma_db",
    collection_name: str = "medical_context",
    search_kwargs: dict = None
):
    embeddings = embedding_model_llama()
    llm = openai_gpt4nano()
    vectordb = Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    base_retriever = vectordb.as_retriever(
        search_kwargs=search_kwargs or {"k": 3}
    )
    compressor = LLMChainExtractor.from_llm(llm=llm)
    compression_retriever = ContextualCompressionRetriever(
        base_retriever=base_retriever,
        base_compressor=compressor
    )
    return compression_retriever

# build_vectorDB("generator/External_KB/output.txt")

retriever = load_vector_retriever()
results = retriever.invoke("What is Congestive heart failure")
for result in results:  
    print("results",result.page_content)