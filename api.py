from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import uuid
import os
from dotenv import load_dotenv

# Load API Keys
load_dotenv()

# Import our LangGraph agent and DB
from src.agent import agent_app
from src.database import get_all_leads

app = FastAPI(title="AutoStream Conversational AI API", version="2.0")

class ChatRequest(BaseModel):
    message: str
    thread_id: str = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Generate thread ID if not provided
        thread_id = request.thread_id if request.thread_id else str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        # Invoke LangGraph agent
        final_state = agent_app.invoke(inputs, config=config)
        agent_response = final_state["messages"][-1].content
        
        return ChatResponse(response=agent_response, thread_id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads/")
async def leads_endpoint():
    try:
        leads = get_all_leads()
        return {"total": len(leads), "leads": leads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
