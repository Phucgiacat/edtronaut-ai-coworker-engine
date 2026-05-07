import uuid
from main import app_graph, SimulationState
from langchain_core.messages import HumanMessage

def run_simulation():
    print("==================================================")
    print("  Edtronaut AI Co-Worker Simulation: Gucci CEO")
    print("==================================================")
    print("Type 'quit' to exit.\n")
    
    # Initialize state
    current_state: SimulationState = {
        "messages": [],
        "rapport_score": 50,
        "director_hint": "",
        "turn_count": 0
    }
    
    while True:
        user_input = input("\nYou (OD Director): ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        # Append message
        current_state["messages"].append(HumanMessage(content=user_input))
        
        # Invoke Graph
        try:
            current_state = app_graph.invoke(current_state)
        except Exception as e:
            print(f"Error: {e}")
            break
            
        # Display Director Info (Debug mode)
        if current_state.get("director_hint"):
            print(f"\n[DEBUG: Director Node activated hint -> '{current_state['director_hint']}']")
            
        # Extract and print AI Response
        ai_response = current_state["messages"][-1].content
        print(f"\nGucci CEO (Draft): {ai_response}")

if __name__ == "__main__":
    run_simulation()
