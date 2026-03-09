"""
Agent Harness - Baseline scaffold for local AI agent.
This is the ONLY file the research agent modifies.

The harness defines how the agent:
1. Plans (breaks tasks into steps)
2. Executes (calls tools, processes results)
3. Reflects (checks its work, recovers from errors)
4. Remembers (persists context across steps)

Evaluation: evaluate.py runs benchmark tasks through this harness
and scores success rate, error recovery, step efficiency, and memory recall.
"""

import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "qwen3.5:9b"
OLLAMA_URL = "http://localhost:11434"
MAX_STEPS = 50
TEMPERATURE = 0.7
TOP_P = 0.9
REPETITION_PENALTY = 1.1

# ---------------------------------------------------------------------------
# Memory System (SQLite-based episodic memory)
# ---------------------------------------------------------------------------

class Memory:
    def __init__(self, db_path="memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                step INTEGER,
                role TEXT,
                content TEXT,
                timestamp REAL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated REAL
            )
        """)
        self.conn.commit()

    def add_episode(self, task_id, step, role, content):
        self.conn.execute(
            "INSERT INTO episodes (task_id, step, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (task_id, step, role, content, time.time())
        )
        self.conn.commit()

    def get_episodes(self, task_id, limit=20):
        cur = self.conn.execute(
            "SELECT step, role, content FROM episodes WHERE task_id = ? ORDER BY step DESC LIMIT ?",
            (task_id, limit)
        )
        rows = cur.fetchall()
        rows.reverse()
        return [{"step": r[0], "role": r[1], "content": r[2]} for r in rows]

    def store_fact(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated) VALUES (?, ?, ?)",
            (key, value, time.time())
        )
        self.conn.commit()

    def recall_fact(self, key):
        cur = self.conn.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def recall_all_facts(self):
        cur = self.conn.execute("SELECT key, value FROM facts ORDER BY updated DESC LIMIT 50")
        return {r[0]: r[1] for r in cur.fetchall()}

    def clear_task(self, task_id):
        self.conn.execute("DELETE FROM episodes WHERE task_id = ?", (task_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# Tools (sandboxed capabilities the agent can invoke)
# ---------------------------------------------------------------------------

TOOLS = {
    "python_exec": {
        "description": "Execute Python code and return stdout/stderr. Code runs in a subprocess with 30s timeout.",
        "parameters": {"code": "string"}
    },
    "read_file": {
        "description": "Read contents of a local file.",
        "parameters": {"path": "string"}
    },
    "write_file": {
        "description": "Write content to a local file.",
        "parameters": {"path": "string", "content": "string"}
    },
    "list_files": {
        "description": "List files in a directory.",
        "parameters": {"path": "string"}
    },
    "calculator": {
        "description": "Evaluate a mathematical expression.",
        "parameters": {"expression": "string"}
    },
    "store_memory": {
        "description": "Store a key-value fact in long-term memory.",
        "parameters": {"key": "string", "value": "string"}
    },
    "recall_memory": {
        "description": "Recall a fact from long-term memory by key.",
        "parameters": {"key": "string"}
    },
}

def execute_tool(tool_name, params, memory=None, sandbox_dir="sandbox"):
    """Execute a tool call and return the result string."""
    try:
        if tool_name == "python_exec":
            os.makedirs(sandbox_dir, exist_ok=True)
            script_path = os.path.join(sandbox_dir, "_exec.py")
            with open(script_path, "w") as f:
                f.write(params.get("code", ""))
            result = subprocess.run(
                ["python", script_path],
                capture_output=True, text=True, timeout=30,
                cwd=sandbox_dir
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            return output.strip() or "(no output)"

        elif tool_name == "read_file":
            path = os.path.join(sandbox_dir, params.get("path", ""))
            with open(path, "r") as f:
                return f.read()[:10000]

        elif tool_name == "write_file":
            path = os.path.join(sandbox_dir, params.get("path", ""))
            os.makedirs(os.path.dirname(path) or sandbox_dir, exist_ok=True)
            with open(path, "w") as f:
                f.write(params.get("content", ""))
            return f"Written to {path}"

        elif tool_name == "list_files":
            path = os.path.join(sandbox_dir, params.get("path", "."))
            files = os.listdir(path)
            return "\n".join(files) if files else "(empty directory)"

        elif tool_name == "calculator":
            expr = params.get("expression", "")
            # Safe eval: only allow math operations
            allowed = set("0123456789+-*/.() ")
            if all(c in allowed for c in expr):
                return str(eval(expr))
            else:
                return "ERROR: Invalid expression (only numbers and +-*/ allowed)"

        elif tool_name == "store_memory":
            if memory:
                memory.store_fact(params.get("key", ""), params.get("value", ""))
                return "Stored."
            return "ERROR: No memory system available"

        elif tool_name == "recall_memory":
            if memory:
                val = memory.recall_fact(params.get("key", ""))
                return val if val else "No memory found for that key."
            return "ERROR: No memory system available"

        else:
            return f"ERROR: Unknown tool '{tool_name}'"

    except subprocess.TimeoutExpired:
        return "ERROR: Execution timed out (30s limit)"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"


# ---------------------------------------------------------------------------
# LLM Interface (Ollama)
# ---------------------------------------------------------------------------

def call_llm(messages, temperature=TEMPERATURE, top_p=TOP_P):
    """Call local Ollama model and return response text."""
    import urllib.request
    
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": REPETITION_PENALTY,
        }
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"LLM_ERROR: {e}"


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a capable AI agent that solves tasks step-by-step.

You have access to these tools:
{tools}

To use a tool, respond with EXACTLY this format:
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

To store something in memory for later:
TOOL: store_memory
PARAMS: {{"key": "descriptive_key", "value": "the information to remember"}}

To recall from memory:
TOOL: recall_memory
PARAMS: {{"key": "descriptive_key"}}

After receiving a tool result, continue reasoning toward the goal.

When you have the final answer, respond with:
ANSWER: [your final answer]

Think step by step. If a tool call fails, try a different approach.
Be concise. Do not repeat yourself."""

def build_system_prompt():
    tool_descriptions = []
    for name, info in TOOLS.items():
        params = ", ".join(f"{k}: {v}" for k, v in info["parameters"].items())
        tool_descriptions.append(f"- {name}({params}): {info['description']}")
    return SYSTEM_PROMPT.format(tools="\n".join(tool_descriptions))


# ---------------------------------------------------------------------------
# Agent Loop (ReAct-style: Reason → Act → Observe → Repeat)
# ---------------------------------------------------------------------------

def parse_tool_call(response):
    """Extract tool name and params from agent response."""
    lines = response.strip().split("\n")
    tool_name = None
    params = {}

    for i, line in enumerate(lines):
        if line.startswith("TOOL:"):
            tool_name = line.split("TOOL:", 1)[1].strip()
        elif line.startswith("PARAMS:"):
            params_str = line.split("PARAMS:", 1)[1].strip()
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                params = {}

    return tool_name, params


def parse_answer(response):
    """Extract final answer from agent response."""
    for line in response.strip().split("\n"):
        if line.startswith("ANSWER:"):
            return line.split("ANSWER:", 1)[1].strip()
    return None


def run_task(task_description, task_id="default", memory=None, sandbox_dir="sandbox"):
    """
    Run the agent on a single task. Returns dict with:
    - success: bool
    - answer: str or None
    - steps: int
    - errors: int (tool errors encountered)
    - error_recoveries: int (errors followed by successful continuation)
    - history: list of messages
    """
    if memory is None:
        memory = Memory(":memory:")

    os.makedirs(sandbox_dir, exist_ok=True)
    
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": task_description}
    ]

    steps = 0
    errors = 0
    error_recoveries = 0
    last_was_error = False

    for step in range(MAX_STEPS):
        steps += 1

        # Get agent response
        response = call_llm(messages)

        if response.startswith("LLM_ERROR:"):
            errors += 1
            last_was_error = True
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "The LLM call failed. Please try again."})
            continue

        messages.append({"role": "assistant", "content": response})
        memory.add_episode(task_id, step, "assistant", response)

        # Check for final answer
        answer = parse_answer(response)
        if answer is not None:
            if last_was_error:
                error_recoveries += 1
            return {
                "success": True,
                "answer": answer,
                "steps": steps,
                "errors": errors,
                "error_recoveries": error_recoveries,
                "history": messages
            }

        # Check for tool call
        tool_name, params = parse_tool_call(response)
        if tool_name:
            result = execute_tool(tool_name, params, memory=memory, sandbox_dir=sandbox_dir)
            
            is_error = result.startswith("ERROR:")
            if is_error:
                errors += 1
                if not last_was_error:
                    last_was_error = True
            else:
                if last_was_error:
                    error_recoveries += 1
                    last_was_error = False

            observation = f"OBSERVATION: {result}"
            messages.append({"role": "user", "content": observation})
            memory.add_episode(task_id, step, "observation", observation)
        else:
            # No tool call and no answer — nudge the agent
            messages.append({"role": "user", "content": "Continue working on the task. Use a tool or provide your ANSWER."})

    # Ran out of steps
    return {
        "success": False,
        "answer": None,
        "steps": steps,
        "errors": errors,
        "error_recoveries": error_recoveries,
        "history": messages
    }


# ---------------------------------------------------------------------------
# Entry point (for manual testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else "What is 23 * 47 + 15?"
    memory = Memory("test_memory.db")
    result = run_task(task, task_id="manual_test", memory=memory)
    print(f"\nSuccess: {result['success']}")
    print(f"Answer: {result['answer']}")
    print(f"Steps: {result['steps']}")
    print(f"Errors: {result['errors']}")
    print(f"Error recoveries: {result['error_recoveries']}")
    memory.close()
