import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from .state import AgentState
from .tools import save_file, run_python_script

load_dotenv()

# ====== LLM Configuration (Custom Endpoint) ======
# Read environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "not-needed")       # Some routers require a dummy key
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")  # Your custom endpoint
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")                   # Model name your endpoint serves

# Initialize LLM with custom base URL
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    temperature=0.3,
)

def call_llm(system_prompt: str, user_content: str) -> str:
    """Helper to call LLM with system + user prompt."""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    response = llm.invoke(messages)
    return response.content

# ====== AGENT 1: COMMANDER ======
def commander_node(state: AgentState) -> AgentState:
    """Breaks down user request into a project plan."""
    prompt = """You are the Commander, a senior project manager.
    Your task: Analyze the user's request and create a clear, actionable project plan.
    Output a JSON with these exact keys:
    - project_name: short name
    - tech_stack: list of technologies (e.g., ["Python", "Flask", "HTML"])
    - features: list of core features
    - complexity: "simple", "medium", or "complex"
    
    Keep it concise.
    """
    
    response = call_llm(prompt, f"User request: {state['user_input']}")
    
    # Log the agent's thought process
    state["chat_log"].append({
        "from": "Commander",
        "to": "All",
        "msg": f"📋 Planning: {response[:200]}..."
    })
    
    state["project_plan"] = response
    state["current_step"] = "ARCHITECT"
    state["iteration"] += 1
    
    return state

# ====== AGENT 2: ARCHITECT ======
def architect_node(state: AgentState) -> AgentState:
    """Designs the folder structure and API contracts."""
    prompt = """You are the Architect, a system designer.
    Given the project plan, design the folder structure and key endpoints.
    Output a JSON with:
    - folder_structure: tree-like string
    - backend_file: filename for main backend (e.g., app.py)
    - frontend_file: filename for main frontend (e.g., index.html)
    - api_endpoints: list of routes
    """
    
    response = call_llm(prompt, f"Project plan: {state['project_plan']}")
    
    state["chat_log"].append({
        "from": "Architect",
        "to": "Backend & Frontend",
        "msg": f"🏗️ Blueprint: {response[:200]}..."
    })
    
    state["folder_structure"] = response
    state["current_step"] = "BACKEND"
    
    return state

# ====== AGENT 3: BACKEND DEVELOPER ======
def backend_dev_node(state: AgentState) -> AgentState:
    """Writes the backend code."""
    prompt = """You are the Backend Developer. Write the full backend code.
    Important rules:
    - Write production-ready, simple code.
    - Use Flask or FastAPI (Python).
    - Include all necessary imports.
    - Make it self-contained so it can run with `python filename.py`.
    - Return ONLY the raw code, no markdown.
    """
    
    context = f"Project plan: {state['project_plan']}\nArchitect: {state['folder_structure']}"
    response = call_llm(prompt, context)
    
    state["backend_code"] = response
    state["chat_log"].append({
        "from": "Backend Dev",
        "to": "QA",
        "msg": "💾 Backend code written, ready for review."
    })
    
    state["current_step"] = "FRONTEND"
    return state

# ====== AGENT 4: FRONTEND DEVELOPER ======
def frontend_dev_node(state: AgentState) -> AgentState:
    """Writes the frontend code."""
    prompt = """You are the Frontend Developer. Write the full frontend code.
    Important rules:
    - Write a single self-contained HTML file with embedded CSS and JS.
    - Make it pixel-perfect and responsive.
    - Use modern, clean design.
    - Return ONLY the raw HTML code, no markdown.
    """
    
    context = f"User request: {state['user_input']}\nPlan: {state['project_plan']}"
    response = call_llm(prompt, context)
    
    state["frontend_code"] = response
    state["chat_log"].append({
        "from": "Frontend Dev",
        "to": "QA",
        "msg": "🎨 Frontend code written, ready for review."
    })
    
    state["current_step"] = "QA"
    return state

# ====== AGENT 5: QA ENGINEER ======
def qa_node(state: AgentState) -> AgentState:
    """Reviews code and runs basic syntax checks."""
    prompt = """You are the QA Engineer. Review the provided code.
    Check for:
    1. Syntax errors
    2. Missing imports
    3. Obvious logical issues
    
    If errors found, output a list of fixes. If clean, say "QA PASSED".
    """
    
    code_to_review = state.get("backend_code", "") + "\n" + state.get("frontend_code", "")
    response = call_llm(prompt, f"Code to review:\n{code_to_review}")
    
    state["chat_log"].append({
        "from": "QA",
        "to": "DevOps",
        "msg": f"🔍 QA Report: {response[:150]}..."
    })
    
    # For Phase 2, we simulate passing. In Phase 3, we'll loop back if errors.
    state["current_step"] = "DEPLOY"
    return state

# ====== AGENT 6: DEVOPS ======
def devops_node(state: AgentState) -> AgentState:
    """Saves the code to disk and executes it."""
    # Save backend code
    backend_filename = "app.py"
    if state.get("backend_code"):
        save_file(backend_filename, state["backend_code"])
    
    # Save frontend code
    frontend_filename = "index.html"
    if state.get("frontend_code"):
        save_file(frontend_filename, state["frontend_code"])
    
    # Run the backend (simulate execution)
    exec_result = run_python_script(backend_filename)
    
    state["execution_result"] = exec_result
    state["current_step"] = "DONE"
    state["user_response"] = f"✅ Project deployed! Check the workspace folder.\n\nExecution log:\n{exec_result[:300]}"
    
    state["chat_log"].append({
        "from": "DevOps",
        "to": "Commander",
        "msg": f"🚀 Deployment complete. File saved to workspace/."
    })
    
    state["chat_log"].append({
        "from": "Commander",
        "to": "User",
        "msg": state["user_response"]
    })
    
    return state