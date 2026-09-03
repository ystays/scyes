from langchain.tools import tool
import subprocess
import sys


@tool
def python_repl(code: str) -> str:
    """Execute Python code and return stdout/stderr. 10-second timeout enforced."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout or result.stderr or "(no output)"
    except subprocess.TimeoutExpired:
        return "Execution timed out (10s limit)."
    except Exception as e:
        return f"Error: {e}"
