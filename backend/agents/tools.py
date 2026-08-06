import os
import subprocess
import sys

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace")

def ensure_workspace():
    """Create workspace folder if it doesn't exist."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

def save_file(filename: str, content: str) -> str:
    """Save a file to the workspace. Returns the full path."""
    ensure_workspace()
    filepath = os.path.join(WORKSPACE_DIR, filename)
    # Ensure subdirectories exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

def read_file(filename: str) -> str:
    """Read a file from workspace."""
    filepath = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(filepath):
        return f"ERROR: File {filename} not found"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def run_python_script(filename: str) -> str:
    """Run a Python script and return the output."""
    filepath = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(filepath):
        return f"ERROR: File {filename} not found"
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return f"✅ SUCCESS\n{result.stdout}"
        else:
            return f"❌ ERROR\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "⏰ TIMEOUT: Script ran too long"
    except Exception as e:
        return f"🔥 EXCEPTION: {str(e)}"