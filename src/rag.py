import json
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def setup_rag(knowledge_base_path="data/knowledge_base.json"):
    """Loads the knowledge base and sets up a simple in-memory FAISS RAG system."""
    with open(knowledge_base_path, "r") as f:
        data = json.load(f)
    
    docs = []
    
    # Process Pricing & Features
    for plan in data.get("pricing_and_features", []):
        plan_name = plan.get("plan")
        price = plan.get("price")
        features = ", ".join(plan.get("features", []))
        
        content = f"Plan: {plan_name}\nPrice: {price}\nFeatures: {features}"
        docs.append(Document(page_content=content, metadata={"source": "pricing"}))
        
    # Process Company Policies
    for policy in data.get("company_policies", []):
        docs.append(Document(page_content=f"Policy: {policy}", metadata={"source": "policy"}))
        
    # Use local HuggingFace embeddings (no API key needed)
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(docs, embeddings)
    
    # Return retriever configured to fetch the top 2 most relevant passages
    return vector_store.as_retriever(search_kwargs={"k": 2})
