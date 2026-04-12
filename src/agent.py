import os
from typing import Annotated, TypedDict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from src.tools import mock_lead_capture
from src.rag import setup_rag

# Initialize the Dual-Brain LLM Engine
# NOTE: Make sure GOOGLE_API_KEY and GROQ_API_KEY are loaded in environment variables.
gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, max_retries=0)
groq_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_retries=1)
llm = gemini_llm.with_fallbacks([groq_llm])

# Initialize Retriever immediately during import or later.
retriever = setup_rag("data/knowledge_base.json")

class LeadDetails(BaseModel):
    """Pydantic model representing variables required to capture a lead."""
    name: Optional[str] = Field(default=None, description="The user's name")
    email: Optional[str] = Field(default=None, description="The user's email address")
    platform: Optional[str] = Field(default=None, description="The user's creator platform e.g., YouTube, Instagram")

class AgentState(TypedDict):
    """LangGraph State class."""
    messages: Annotated[list, add_messages]
    intent: str
    lead_details: LeadDetails

class IntentClassification(BaseModel):
    """Pydantic model for extracting the intent string via structured output."""
    intent: str = Field(description="Must be exactly one of: 'greeting', 'inquiry', 'lead'")

def detect_intent(state: AgentState):
    """Node: Analyzes the conversation history to classify the user's intent."""
    msgs = state["messages"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an intent classification assistant for AutoStream. "
         "Based on the conversation history, classify the user's latest message into one of three categories:\n"
         "1. 'greeting': A casual greeting or simple acknowledgment.\n"
         "2. 'inquiry': Questions about pricing, basic/pro plans, features, or policies.\n"
         "3. 'lead': High intent, showing readiness to sign up, use it for their channel, or agreeing to try a specific plan.\n\n"
         "Output ONLY the exact intent string."),
        ("placeholder", "{messages}")
    ])
    
    structured_gemini = gemini_llm.with_structured_output(IntentClassification)
    structured_groq = groq_llm.with_structured_output(IntentClassification)
    structured_llm = structured_gemini.with_fallbacks([structured_groq])
    chain = prompt | structured_llm
    
    # Process intent. If API fails to structure, default to greeting
    try:
        result = chain.invoke({"messages": msgs})
        intent = result.intent
    except Exception:
        intent = "greeting"
        
    return {"intent": intent}

def handle_greeting(state: AgentState):
    """Node: Handles simple or casual greetings."""
    response = llm.invoke([
        SystemMessage(content="You are a helpful assistant for AutoStream, an automated video editing SaaS. Respond casually and politely to the user's greeting and ask how you can help them today.")
    ] + state["messages"])
    return {"messages": [response]}

def handle_inquiry(state: AgentState):
    """Node: Answers questions using the RAG retriever (Knowledge Base)."""
    
    # 1. Contextualize the question for multi-turn capability
    if len(state["messages"]) > 1:
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given a chat history and the latest user question, "
             "formulate a standalone question which can be understood without the context. "
             "Ensure the output is a single, naturally spaced sentence. Do NOT answer it."),
            ("placeholder", "{messages}")
        ])
        contextualized_q = llm.invoke(contextualize_prompt.format_messages(messages=state["messages"])).content
    else:
        contextualized_q = state["messages"][-1].content

    # 2. Retrieve documents using the standalone contextualized question
    docs = retriever.invoke(contextualized_q)
    context = "\n".join([doc.page_content for doc in docs])
    
    # 3. Answer the user
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional assistant for AutoStream. Answer the user's question clearly and helpfuly based on the provided context.\n"
                   "Write in a friendly, conversational tone with standard spacing and paragraphs.\n\nContext:\n{context}"),
        ("placeholder", "{messages}")
    ])
    
    response = llm.invoke(prompt.format_messages(context=context, messages=state["messages"]))
    return {"messages": [response]}

def parse_lead_details(state: AgentState):
    """Node: Extracts lead details (Name, Email, Platform) if the user is a lead."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract any lead details (Name, Email, Creator Platform) provided by the user in the conversation. If a value is missing or unclear, leave it null.\n"
                   "Creator Platform generally means YouTube, TikTok, Instagram, etc."),
        ("placeholder", "{messages}")
    ])
    structured_gemini = gemini_llm.with_structured_output(LeadDetails)
    structured_groq = groq_llm.with_structured_output(LeadDetails)
    structured_llm = structured_gemini.with_fallbacks([structured_groq])
    
    try:
        extracted = structured_llm.invoke(prompt.format_messages(messages=state["messages"]))
    except Exception:
        extracted = LeadDetails() # default empty
        
    return {"lead_details": extracted}

def manage_lead(state: AgentState):
    """Node: Evaluates LeadDetails state and calls external Tool if complete, or asks for missing info."""
    details = state.get("lead_details", LeadDetails())
    
    missing = []
    if not details.name: missing.append("Name")
    if not details.email: missing.append("Email")
    if not details.platform: missing.append("Creator Platform (e.g. YouTube, Instagram)")
        
    if missing:
        missing_str = ", ".join(missing)
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a sales agent for AutoStream. The user has shown high intent to sign up. "
             f"You need to collect their: {missing_str}. Ask politely for the missing information. Only ask for what is missing."),
            ("placeholder", "{messages}")
        ])
        response = llm.invoke(prompt.format_messages(messages=state["messages"]))
        return {"messages": [response]}
    else:
        # All info collected! Call the Tool.
        result = mock_lead_capture(details.name, details.email, details.platform)
        msg_content = f"Thank you! {result} Our team will grant you access to AutoStream shortly!"
        return {"messages": [AIMessage(content=msg_content)]}

def route_intent(state: AgentState):
    """Conditional Edge function routing to the proper node based on Intent."""
    intent = state.get("intent", "greeting")
    if intent == "lead":
        return "parse_lead_details"
    elif intent == "inquiry":
        return "handle_inquiry"
    else:
        return "handle_greeting"

# Build StateGraph
builder = StateGraph(AgentState)

builder.add_node("detect_intent", detect_intent)
builder.add_node("handle_greeting", handle_greeting)
builder.add_node("handle_inquiry", handle_inquiry)
builder.add_node("parse_lead_details", parse_lead_details)
builder.add_node("manage_lead", manage_lead)

builder.add_edge(START, "detect_intent")
builder.add_conditional_edges(
    "detect_intent", 
    route_intent, 
    {"parse_lead_details": "parse_lead_details", "handle_inquiry": "handle_inquiry", "handle_greeting": "handle_greeting"}
)
builder.add_edge("parse_lead_details", "manage_lead")
builder.add_edge("handle_greeting", END)
builder.add_edge("handle_inquiry", END)
builder.add_edge("manage_lead", END)

# Memory component required by assignment to preserve state across turns
memory = MemorySaver()

# Compile the Graph
agent_app = builder.compile(checkpointer=memory)
