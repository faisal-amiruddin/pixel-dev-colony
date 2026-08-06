from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    # Input from user
    user_input: str
    
    # Planning stage
    project_plan: Optional[str]
    tech_stack: Optional[str]
    folder_structure: Optional[str]
    
    # Code generation
    backend_code: Optional[str]
    frontend_code: Optional[str]
    test_code: Optional[str]
    
    # Execution
    file_paths: Optional[List[str]]
    execution_result: Optional[str]
    
    # Control flow
    current_step: str  # "PLAN", "ARCHITECT", "BACKEND", "FRONTEND", "QA", "DEPLOY"
    iteration: int
    max_iterations: int
    
    # Logs for UI broadcast
    chat_log: List[Dict[str, str]]  # [{"from": "Commander", "to": "All", "msg": "..."}]
    user_response: Optional[str]  # Final message to show in User Chat