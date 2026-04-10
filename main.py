import os
import uuid
from dotenv import load_dotenv

# Load environment variables (e.g. GOOGLE_API_KEY)
load_dotenv()

# Pre-check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("\n[ERROR] GOOGLE_API_KEY is not set in the environment.")
    print("Please copy .env.example to .env and add your key, or export it in your terminal.\n")
    exit(1)

# Import the pre-compiled graph
from langchain_core.messages import HumanMessage
from src.agent import agent_app

def main():
    print("==================================================")
    print("    AutoStream Conversational AI Agent (Demo)     ")
    print("==================================================")
    print("Type 'quit' or 'exit' to end the session.\n")

    # Generate a unique thread ID for tracking this session's memory across runs
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
            if not user_input.strip():
                continue
            
            # Prepare the user message
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # Invoke the graph. The config maps this conversation to exactly one thread.
            final_state = agent_app.invoke(inputs, config=config)
            
            # Parse the last response
            agent_msgs = final_state.get("messages", [])
            if agent_msgs:
                print(f"Agent: {agent_msgs[-1].content}\n")
                
        except Exception as e:
            print(f"\n[Exception]: {e}\n")

if __name__ == "__main__":
    main()
