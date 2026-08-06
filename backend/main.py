import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import socketio
from dotenv import load_dotenv
import uvicorn

# Load environment
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

# ============ MOUNT STATIC (Frontend) ============
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
# For development, we usually serve via Vite proxy, but keep this for static fallback if needed.
# However, since we use Vite proxy, we don't strictly need this, but it's safe to keep.
# We'll just serve index.html from root if needed, but we rely on Vite's dev server.
# Actually, for Phase 1, we don't need to mount static, because we use Vite proxy.

# ============ ROUTE (Optional health check) ============
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ============ SOCKET.IO EVENTS ============
chat_history = {
    "user": [],      # User chat history (user & leader)
    "agent": []      # Agent War Room history (internal agent convos)
}

@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")
    await sio.emit("init_history", chat_history, to=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")

@sio.event
async def user_message(sid, data):
    """Receives a message from the user (left chat column)"""
    print(f"📩 User says: {data}")
    
    # Save to user history
    chat_history["user"].append({"role": "user", "text": data})
    
    # Broadcast to all clients to update the user chat
    await sio.emit("new_user_message", {"text": data}, skip_sid=sid)
    
    # ========== SIMULATION: Leader Auto-Reply (to be replaced by LangGraph in Phase 2) ==========
    import asyncio
    await asyncio.sleep(1)  # Simulate processing time
    
    fake_leader_reply = f"📋 Commander: Received your request '{data}'. I am delegating tasks to my team. Stand by..."
    chat_history["user"].append({"role": "leader", "text": fake_leader_reply})
    await sio.emit("new_user_message", {"text": fake_leader_reply})
    
    # Also broadcast to Agent War Room (internal team communication)
    fake_agent_chat = f"🗣️ [Commander] -> All: User requested '{data}'. Team, prepare for action!"
    chat_history["agent"].append(fake_agent_chat)
    await sio.emit("new_agent_message", {"text": fake_agent_chat})

# ============ WRAP ASGI ============
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    # FIX: Using import string to enable reload properly
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )