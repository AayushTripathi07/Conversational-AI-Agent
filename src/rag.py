import json
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def setup_rag(knowledge_base_path="data/knowledge_base.json"):
    """Loads the knowledge base and sets up a simple in-memory FAISS RAG system."""
    with open(knowledge_base_path, "r") as f:
        data = json.load(f)
    
    docs = []
    
    # Process all keys in the JSON dynamically
    for section_name, items in data.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    # Handle nested dictionaries (like pricing)
                    content_parts = []
                    for k, v in item.items():
                        if isinstance(v, list):
                            v = ", ".join(v)
                        content_parts.append(f"{k.capitalize()}: {v}")
                    content = "\n".join(content_parts)
                else:
                    # Handle flat strings (like policies or about us)
                    content = f"{section_name.replace('_', ' ').capitalize()}: {item}"
                
                docs.append(Document(page_content=content, metadata={"source": section_name}))
        
    # Use local HuggingFace embeddings (no API key needed)
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(docs, embeddings)
    
    # Return retriever configured to fetch the top 5 most relevant passages
    return vector_store.as_retriever(search_kwargs={"k": 5})
