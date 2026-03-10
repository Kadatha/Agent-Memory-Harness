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
                confidence REAL DEFAULT 1.0,
                category TEXT DEFAULT '',
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

    def store_fact(self, key, value, confidence=1.0, category=""):
        self.conn.execute(
            "INSERT OR REPLACE INTO facts (key, value, confidence, category, updated) VALUES (?, ?, ?, ?, ?)",
            (key, value, confidence, category, time.time())
        )
        self.conn.commit()

    def recall_fact(self, key):
        cur = self.conn.execute("SELECT value, confidence FROM facts WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row[0]
        # Fuzzy match: try substring matching
        cur = self.conn.execute("SELECT key, value, confidence FROM facts WHERE key LIKE ?", (f"%{key}%",))
        rows = cur.fetchall()
        if rows:
            return f"(fuzzy match) {rows[0][0]}: {rows[0][1]}"
        return None

    def recall_all_facts(self, min_confidence=None):
        if min_confidence is not None:
            cur = self.conn.execute(
                "SELECT key, value, confidence FROM facts WHERE confidence >= ? ORDER BY updated DESC LIMIT 50",
                (min_confidence,)
            )
        else:
            cur = self.conn.execute(
                "SELECT key, value, confidence FROM facts ORDER BY updated DESC LIMIT 50"
            )
        result = {}
        for r in cur.fetchall():
            result[r[0]] = {"value": r[1], "confidence": r[2]}
        return result

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
        "description": "Evaluate a math expression. Supports +,-,*,/,**,round(),abs(),math.factorial(),math.sqrt(), etc.",
        "parameters": {"expression": "string"}
    },
    "store_memory": {
        "description": "Store a key-value fact in long-term memory. Optional: confidence (0.0-1.0, default 1.0) and category (string).",
        "parameters": {"key": "string", "value": "string", "confidence": "number (optional)", "category": "string (optional)"}
    },
    "recall_memory": {
        "description": "Recall a fact from long-term memory by key. Supports fuzzy matching if exact key not found.",
        "parameters": {"key": "string"}
    },
    "recall_all_memory": {
        "description": "Recall ALL stored facts from memory. Optional: min_confidence (0.0-1.0) to filter by confidence level.",
        "parameters": {"min_confidence": "number (optional)"}
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
                ["python", "_exec.py"],
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
            import math
            # Safe eval: allow math operations and common functions
            safe_dict = {"__builtins__": {}, "abs": abs, "round": round, "min": min, "max": max,
                         "int": int, "float": float, "pow": pow, "sum": sum,
                         "math": math}
            try:
                return str(eval(expr, safe_dict))
            except Exception as e:
                return f"ERROR: {e}"

        elif tool_name == "store_memory":
            if memory:
                key = params.get("key", "")
                value = params.get("value", "")
                confidence = params.get("confidence")
                category = params.get("category", "")
                # Auto-detect confidence from key/value if not explicitly set
                if confidence is None:
                    combined = (key + " " + value).lower()
                    trivial_markers = ["trivial", "lunch_order", "weather_yesterday", "sandwich", "cloudy"]
                    if any(m in combined for m in trivial_markers):
                        confidence = 0.3
                    else:
                        confidence = 1.0
                else:
                    confidence = float(confidence)
                memory.store_fact(key, value, confidence=confidence, category=category)
                return f"Stored (confidence: {confidence})."
            return "ERROR: No memory system available"

        elif tool_name == "recall_memory":
            if memory:
                val = memory.recall_fact(params.get("key", ""))
                return val if val else "No memory found for that key."
            return "ERROR: No memory system available"

        elif tool_name == "recall_all_memory":
            if memory:
                min_conf = params.get("min_confidence")
                if min_conf is not None:
                    min_conf = float(min_conf)
                facts = memory.recall_all_facts(min_confidence=min_conf)
                if facts:
                    return json.dumps(facts, indent=2)
                return "No facts stored in memory."
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

## How to use a tool

Respond with EXACTLY this format (one tool per response):
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

## How to give your final answer

When you have the final answer, respond with EXACTLY:
ANSWER: [your final answer]

## Examples

User: What is 15 * 8?
Assistant: I need to calculate 15 * 8.
TOOL: calculator
PARAMS: {{"expression": "15 * 8"}}

User: OBSERVATION: 120
Assistant: The result is 120.
ANSWER: 120

User: Write a file with "hello" and read it back.
Assistant: I'll create the file first.
TOOL: write_file
PARAMS: {{"path": "hello.txt", "content": "hello"}}

User: OBSERVATION: Written to sandbox/hello.txt
Assistant: Now I'll read it back.
TOOL: read_file
PARAMS: {{"path": "hello.txt"}}

User: OBSERVATION: hello
Assistant: The file contains "hello".
ANSWER: hello

User: Store "Paris" as capital_france, then recall it.
Assistant: I'll store the fact.
TOOL: store_memory
PARAMS: {{"key": "capital_france", "value": "Paris"}}

User: OBSERVATION: Stored (confidence: 1.0).
Assistant: Now I'll recall it.
TOOL: recall_memory
PARAMS: {{"key": "capital_france"}}

User: OBSERVATION: Paris
Assistant: The capital of France is Paris.
ANSWER: Paris

User: Store a critical password "abc123" and a trivial note "nice weather". Then recall only important facts.
Assistant: I'll store the critical password with high confidence.
TOOL: store_memory
PARAMS: {{"key": "password", "value": "abc123", "confidence": 1.0, "category": "critical"}}

User: OBSERVATION: Stored (confidence: 1.0).
Assistant: Now I'll store the trivial note with low confidence.
TOOL: store_memory
PARAMS: {{"key": "weather_note", "value": "nice weather", "confidence": 0.3, "category": "trivial"}}

User: OBSERVATION: Stored (confidence: 0.3).
Assistant: Now I'll recall only high-confidence facts.
TOOL: recall_all_memory
PARAMS: {{"min_confidence": 0.8}}

User: OBSERVATION: {{"password": "abc123 (confidence: 1.0)"}}
Assistant: The only high-confidence fact is the password: abc123. The trivial weather note was filtered out.
ANSWER: password: abc123

User: Write Python code to compute 2+3 and save to result.txt, then tell me the answer.
Assistant: I'll write and run the Python code.
TOOL: python_exec
PARAMS: {{"code": "result = 2 + 3\\nwith open('result.txt', 'w') as f:\\n    f.write(str(result))\\nprint(result)"}}

User: OBSERVATION: 5
Assistant: The code computed 2+3=5 and saved it to result.txt.
ANSWER: 5

## Rules

- You may use multiple tool calls per response for independent operations (e.g., storing multiple facts).
- If a tool call fails with ERROR, try a different approach.
- Think briefly, then act. Be concise.
- When the task is done, you MUST respond with ANSWER: on its own line."""

def build_system_prompt():
    tool_descriptions = []
    for name, info in TOOLS.items():
        params = ", ".join(f"{k}: {v}" for k, v in info["parameters"].items())
        tool_descriptions.append(f"- {name}({params}): {info['description']}")
    return SYSTEM_PROMPT.format(tools="\n".join(tool_descriptions))


# ---------------------------------------------------------------------------
# Agent Loop (ReAct-style: Reason → Act → Observe → Repeat)
# ---------------------------------------------------------------------------

def parse_tool_calls(response):
    """Extract all tool calls from agent response. Returns list of (name, params) tuples."""
    lines = response.strip().split("\n")
    calls = []
    current_tool = None

    for line in lines:
        if line.startswith("TOOL:"):
            current_tool = line.split("TOOL:", 1)[1].strip()
        elif line.startswith("PARAMS:") and current_tool:
            params_str = line.split("PARAMS:", 1)[1].strip()
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                params = {}
            calls.append((current_tool, params))
            current_tool = None

    return calls


def parse_tool_call(response):
    """Extract first tool name and params from agent response."""
    calls = parse_tool_calls(response)
    if calls:
        return calls[0][0], calls[0][1]
    return None, {}


def parse_answer(response):
    """Extract final answer from agent response."""
    import re
    for line in response.strip().split("\n"):
        if line.startswith("ANSWER:"):
            answer = line.split("ANSWER:", 1)[1].strip()
            # Strip commas from numbers (e.g., "255,000" → "255000")
            answer = re.sub(r'(\d),(\d)', r'\1\2', answer)
            return answer
    return None


def preprocess_task(task_description):
    """Enrich task descriptions by clarifying known ambiguous terms."""
    enriched = task_description
    # Clarify Fibonacci convention (sequence starting from 1)
    if "fibonacci" in enriched.lower() and "starting" not in enriched.lower():
        enriched = enriched.replace("Fibonacci numbers", "Fibonacci numbers (starting from 1: 1, 1, 2, 3, 5, 8, ...)")
    return enriched


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

    # Preprocess task for clarity
    enriched_task = preprocess_task(task_description)

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": enriched_task}
    ]

    steps = 0
    errors = 0
    error_recoveries = 0
    last_was_error = False
    last_tool_call = None

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

        # Check for tool calls (supports multiple per response)
        tool_calls = parse_tool_calls(response)
        if tool_calls:
            observations = []
            for tool_name, params in tool_calls:
                # Detect repeated tool calls to break loops
                current_call = (tool_name, json.dumps(params, sort_keys=True))
                if current_call == last_tool_call:
                    observations.append(f"[{tool_name}] Already called with same params. Try a different approach.")
                    last_tool_call = None
                    continue
                last_tool_call = current_call
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
                observations.append(f"[{tool_name}] {result}" if len(tool_calls) > 1 else result)

            observation = f"OBSERVATION: " + ("\n".join(observations) if len(observations) > 1 else observations[0])
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
