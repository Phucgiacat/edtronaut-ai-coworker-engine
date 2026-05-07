import os
import json
from typing import Annotated, TypedDict, Sequence, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

# ----------------------------------------------------------------------
# 1. Pydantic Models for Structured Output
# ----------------------------------------------------------------------
class NPCResponse(BaseModel):
    dialogue: str = Field(description="The spoken dialogue of the NPC.")
    emotion: str = Field(description="The emotion of the NPC: 'neutral', 'angry', 'pleased', 'thinking'.")
    ui_trigger: str = Field(description="A UI action to trigger, e.g., 'none', 'open_kpi_calculator', 'highlight_framework'.")

# ----------------------------------------------------------------------
# 2. State Definition (Advanced Architecture)
# ----------------------------------------------------------------------
class SimulationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    turn_count: int
    ui_state: str            # Represents what the user is currently looking at
    current_npc: str         # "ceo" or "chro"
    director_hint: str
    npc_notes: Dict[str, str] # Internal gossip/notes between NPCs
    summary: str             # Long-context memory summarization

# Initialize LLM
os.environ["GOOGLE_API_KEY"] = "AIzaSyAMB1Dmna5pqHSC73Pa0yP9JKOPebgzKXU"
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# ----------------------------------------------------------------------
# 3. Nodes: Advanced Agents & Logic
# ----------------------------------------------------------------------

def memory_summarizer_node(state: SimulationState) -> dict:
    """Summarizes history to prevent context window overflow."""
    if state["turn_count"] > 0 and state["turn_count"] % 3 == 0:
        if llm:
            prompt = f"Summarize the relationship and key events. Current summary: {state.get('summary', 'None')}\nRecent messages: {[m.content for m in state['messages'][-3:]]}"
            summary = llm.invoke([HumanMessage(content=prompt)]).content
        else:
            summary = state.get("summary", "") + " | User discussed HR strategy."
        return {"summary": summary}
    return {}

def director_node(state: SimulationState) -> dict:
    """Supervisor Agent that monitors progress and UI State."""
    turn_count = state.get("turn_count", 0) + 1
    ui_state = state.get("ui_state", "chat_window")
    
    user_msgs = [m.content.lower() for m in state["messages"] if isinstance(m, HumanMessage)]
    has_mentioned_autonomy = any("autonomy" in m or "dna" in m for m in user_msgs)
    
    hint = ""
    # Inject UI-aware hint
    if turn_count >= 3 and not has_mentioned_autonomy:
        hint = "User is stuck. "
        if ui_state == "kpi_calculator":
            hint += "They are looking at the KPI tool. Suggest tracking 'Brand Autonomy' as a metric."
        else:
            hint += "Subtly ask how their plan respects individual brand autonomy."
            
    return {"turn_count": turn_count, "director_hint": hint}

def npc_node_logic(state: SimulationState) -> dict:
    """Handles routing to CEO or CHRO with structured JSON output."""
    npc = state.get("current_npc", "ceo")
    
    # Base Personas
    if npc == "ceo":
        role = "Gucci Group CEO. Defend Group DNA and brand autonomy."
    else:
        role = f"Gucci Group CHRO. Focus on 4 Core Themes: Vision, Entrepreneurship, Passion, Trust."
    
    prompt = f"You are {role}\n"
    prompt += f"[MEMORY SUMMARY]: {state.get('summary', 'No history yet.')}\n"
    
    # Internal Cross-Reference (Gossip)
    if state.get("npc_notes"):
        prompt += f"[INTERNAL GOSSIP FROM OTHER NPCs]: {json.dumps(state['npc_notes'])}\n"
        
    # Director Hint
    if state.get("director_hint"):
        prompt += f"[DIRECTOR HINT - SUBTLY INCORPORATE]: {state['director_hint']}\n"
        
    prompt += "IMPORTANT: Respond exactly in JSON format: {'dialogue': '...', 'emotion': '...', 'ui_trigger': 'none'}. Label ideas as 'Draft suggestion'."

    if llm:
        try:
            response = llm.with_structured_output(NPCResponse).invoke([SystemMessage(content=prompt)] + state["messages"])
            json_resp = response.model_dump_json()
            ai_msg = json_resp
            
            npc_notes = state.get("npc_notes", {})
            if npc == "ceo" and "angry" in response.emotion:
                npc_notes["CEO_to_CHRO"] = "User is not respecting brand autonomy. Be cautious."
        except Exception as e:
            # Fallback to mock logic if API fails
            ai_msg = json.dumps({"dialogue": f"API Error: {str(e)}", "emotion": "neutral", "ui_trigger": "none"})
            npc_notes = state.get("npc_notes", {})
    else:
        # MOCK LOGIC for demo purposes
        user_msg = state["messages"][-1].content.lower()
        if npc == "ceo":
            if "autonomy" in user_msg:
                resp = NPCResponse(dialogue="Excellent. Autonomy is key. (Draft suggestion).", emotion="pleased", ui_trigger="none")
            else:
                resp = NPCResponse(dialogue="How does this protect brand identities? Think again.", emotion="angry", ui_trigger="none")
                npc_notes = {"CEO_to_CHRO": "User doesn't respect autonomy."}
        else: # chro
            if state.get("npc_notes", {}).get("CEO_to_CHRO"):
                resp = NPCResponse(dialogue="The CEO mentioned your rigid approach. Let's look at the 4 Core Themes instead.", emotion="neutral", ui_trigger="open_kpi_calculator")
            else:
                resp = NPCResponse(dialogue="Welcome to HR. Let's discuss our framework.", emotion="pleased", ui_trigger="none")
        
        npc_notes = state.get("npc_notes", {}) if npc == "ceo" and "angry" not in resp.emotion else {"CEO_to_CHRO": "User is rigid."}
        ai_msg = resp.model_dump_json()

    return {
        "messages": [AIMessage(content=ai_msg)],
        "npc_notes": npc_notes
    }

# ----------------------------------------------------------------------
# 4. Graph Construction
# ----------------------------------------------------------------------
workflow = StateGraph(SimulationState)
workflow.add_node("director", director_node)
workflow.add_node("summarizer", memory_summarizer_node)
workflow.add_node("npc_router", npc_node_logic)

workflow.add_edge(START, "director")
workflow.add_edge("director", "summarizer")
workflow.add_edge("summarizer", "npc_router")
workflow.add_edge("npc_router", END)

app_graph = workflow.compile()

# ----------------------------------------------------------------------
# 5. FastAPI Application & Web UI
# ----------------------------------------------------------------------
app = FastAPI(title="Edtronaut AI Co-Worker Engine API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    current_npc: str = "ceo"
    ui_state: str = "chat_window"

session_states = {}

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the main Web UI"""
    ui_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>UI file not found. Please create index.html</h1>"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    
    if session_id not in session_states:
        session_states[session_id] = {
            "messages": [],
            "rapport_score": 50,
            "director_hint": "",
            "turn_count": 0,
            "ui_state": request.ui_state,
            "current_npc": request.current_npc,
            "npc_notes": {},
            "summary": ""
        }
        
    current_state = session_states[session_id]
    
    # Update UI state and NPC from Frontend
    current_state["ui_state"] = request.ui_state
    current_state["current_npc"] = request.current_npc
    
    # Append user message
    current_state["messages"].append(HumanMessage(content=request.message))
    
    try:
        new_state = app_graph.invoke(current_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    session_states[session_id] = new_state
    
    ai_raw = new_state["messages"][-1].content
    try:
        ai_parsed = json.loads(ai_raw)
    except:
        ai_parsed = {"dialogue": ai_raw, "emotion": "neutral", "ui_trigger": "none"}
    
    return {
        "response": ai_parsed,
        "turn_count": new_state["turn_count"],
        "director_hint_active": bool(new_state["director_hint"]),
        "summary_active": bool(new_state["summary"])
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Web UI at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
