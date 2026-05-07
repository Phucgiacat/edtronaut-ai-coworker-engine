import time
from main import app_graph, SimulationState
from langchain_core.messages import HumanMessage

def print_turn(state: SimulationState):
    if state.get("director_hint"):
        print(f"\n[DIRECTOR INVISIBLE INTERVENTION] -> Hint injected to CEO: '{state['director_hint']}'")
    
    ai_response = state["messages"][-1].content
    print(f"\n[AI CEO]: {ai_response}\n")
    print("-" * 60)

def main():
    print("=" * 60)
    print("  SIMULATION DEMO: EDTRONAUT AI CO-WORKER (GUCCI CEO)")
    print("=" * 60)
    
    state: SimulationState = {
        "messages": [],
        "rapport_score": 50,
        "director_hint": "",
        "turn_count": 0
    }
    
    # --- Turn 1: Bad interaction ---
    msg1 = "Hi CEO. I'm going to roll out a strict standard competency framework to all brands immediately."
    print(f"\n[USER Turn 1]: {msg1}")
    state["messages"].append(HumanMessage(content=msg1))
    state = app_graph.invoke(state)
    print_turn(state)
    
    time.sleep(1)
    
    # --- Turn 2: Still not getting it ---
    msg2 = "It's more efficient if everyone uses the exact same metrics regardless of the brand."
    print(f"\n[USER Turn 2]: {msg2}")
    state["messages"].append(HumanMessage(content=msg2))
    state = app_graph.invoke(state)
    print_turn(state)
    
    time.sleep(1)
    
    # --- Turn 3: User is stuck, Director steps in ---
    msg3 = "I don't understand why you're pushing back."
    print(f"\n[USER Turn 3]: {msg3}")
    state["messages"].append(HumanMessage(content=msg3))
    state = app_graph.invoke(state)
    print_turn(state)
    
    time.sleep(1)

    # --- Turn 4: User finally understands (Good interaction) ---
    msg4 = "Ah, I see. What if we customize the framework to respect the autonomy and unique DNA of each brand?"
    print(f"\n[USER Turn 4]: {msg4}")
    state["messages"].append(HumanMessage(content=msg4))
    state = app_graph.invoke(state)
    print_turn(state)

if __name__ == "__main__":
    main()
