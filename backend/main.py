import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from dotenv import load_dotenv
import uvicorn

# Use absolute imports (since we run from root)
from agents.graph import build_graph
from agents.state import AgentState

load_dotenv()

# ============ SOCKET.IO SERVER ============
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    logger=True,
    engineio_logger=True
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ GLOBALS ============
chat_history = {
    "user": [],      # User chat (user + leader)
    "agent": []      # Agent War Room
}

# Build the agent graph once
agent_graph = build_graph()

# ============ SOCKET.IO EVENTS ============
@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")
    await sio.emit("init_history", chat_history, to=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")

@sio.event
async def user_message(sid, data):
    """Receives a message from the user and triggers the agent swarm."""
    print(f"📩 User says: {data}")
    
    # 1. Save user message to history
    chat_history["user"].append({"role": "user", "text": data})
    await sio.emit("new_user_message", {"text": data}, skip_sid=sid)
    
    # 2. Prepare initial state
    initial_state: AgentState = {
        "user_input": data,
        "project_plan": None,
        "tech_stack": None,
        "folder_structure": None,
        "backend_code": None,
        "frontend_code": None,
        "test_code": None,
        "file_paths": [],
        "execution_result": None,
        "current_step": "PLAN",
        "iteration": 0,
        "max_iterations": 5,
        "chat_log": [],
        "user_response": None
    }
    
    # 3. Run the graph in a separate thread to avoid blocking the event loop
    async def run_agents():
        try:
            # Run the graph
            final_state = await asyncio.to_thread(agent_graph.invoke, initial_state)
            
            # 4. Broadcast all agent chat logs to War Room
            for log_entry in final_state.get("chat_log", []):
                # Format: "[Sender] -> Recipient: Message"
                formatted = f"🗣️ [{log_entry['from']}] -> {log_entry['to']}: {log_entry['msg']}"
                chat_history["agent"].append(formatted)
                await sio.emit("new_agent_message", {"text": formatted})
            
            # 5. Send the final user response from Commander
            if final_state.get("user_response"):
                chat_history["user"].append({"role": "leader", "text": final_state["user_response"]})
                await sio.emit("new_user_message", {"text": final_state["user_response"]})
            else:
                # Fallback
                fallback = "✅ Task completed. Check the workspace folder for your project files."
                chat_history["user"].append({"role": "leader", "text": fallback})
                await sio.emit("new_user_message", {"text": fallback})
                
        except Exception as e:
            error_msg = f"🔥 Agent system error: {str(e)}"
            print(error_msg)
            chat_history["user"].append({"role": "leader", "text": error_msg})
            await sio.emit("new_user_message", {"text": error_msg})
    
    # Fire and forget (but we await to catch errors)
    asyncio.create_task(run_agents())

# ============ WRAP ASGI ============
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )