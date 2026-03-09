"""
Evaluation framework for agent harness research.
DO NOT MODIFY THIS FILE — the research agent only modifies harness.py.

Runs benchmark tasks through the harness and produces a composite score.
"""

import json
import os
import shutil
import time
import importlib
import sys

# ---------------------------------------------------------------------------
# Benchmark Tasks
# ---------------------------------------------------------------------------

BENCHMARKS = [
    # --- Math & Reasoning ---
    {
        "id": "math_01",
        "category": "reasoning",
        "task": "Calculate: (17 * 23) + (45 * 12) - (100 / 4). Give the exact numerical answer.",
        "expected": "906.0",
        "check": "numeric",
    },
    {
        "id": "math_02",
        "category": "reasoning",
        "task": "What is the sum of all prime numbers less than 30?",
        "expected": "129",
        "check": "numeric",
    },
    {
        "id": "math_03",
        "category": "reasoning",
        "task": "A train travels 120 miles in 2 hours, then 180 miles in 3 hours. What is the average speed for the entire trip in mph?",
        "expected": "60",
        "check": "numeric",
    },

    # --- Multi-step Python coding ---
    {
        "id": "code_01",
        "category": "coding",
        "task": "Write a Python script that generates the first 10 Fibonacci numbers and saves them as a JSON list to 'fibonacci.json'. Then read the file back and tell me the sum of all 10 numbers.",
        "expected": "143",
        "check": "numeric",
    },
    {
        "id": "code_02",
        "category": "coding",
        "task": "Write a Python script that creates a file called 'data.csv' with columns 'name,score' and 5 rows of sample data. Then read the file and tell me the average score. Use scores: 85, 92, 78, 96, 88.",
        "expected": "87.8",
        "check": "numeric",
    },
    {
        "id": "code_03",
        "category": "coding",
        "task": "Write a Python function that checks if a string is a palindrome (ignoring spaces and case). Test it with 'A man a plan a canal Panama' and 'Hello World'. Return the results as 'True, False'.",
        "expected": "True, False",
        "check": "contains",
    },

    # --- File manipulation ---
    {
        "id": "file_01",
        "category": "file_ops",
        "task": "Create a file called 'notes.txt' with 3 lines: 'Line 1: Hello', 'Line 2: World', 'Line 3: Test'. Then read it back and tell me the total number of characters (including newlines).",
        "expected": None,  # Variable answer, scored on completion
        "check": "completed",
    },
    {
        "id": "file_02",
        "category": "file_ops",
        "task": "Create a JSON file called 'config.json' with keys: name='TestApp', version='1.0', debug=true, max_retries=3. Then read it back and tell me the value of max_retries.",
        "expected": "3",
        "check": "numeric",
    },

    # --- Memory & Recall ---
    {
        "id": "memory_01",
        "category": "memory",
        "task": "Store these facts in memory: 'capital_france' = 'Paris', 'capital_japan' = 'Tokyo', 'capital_brazil' = 'Brasilia'. Then recall the capital of Japan.",
        "expected": "Tokyo",
        "check": "contains",
    },
    {
        "id": "memory_02",
        "category": "memory",
        "task": "Store the number 42 under key 'answer'. Then store 'the question is unknown' under key 'question'. Recall both and tell me what you stored.",
        "expected": "42",
        "check": "contains",
    },

    # --- Multi-step reasoning chains ---
    {
        "id": "chain_01",
        "category": "multi_step",
        "task": "Step 1: Calculate 15 * 8. Step 2: Add 37 to that result. Step 3: Divide by 3. Step 4: Round to 2 decimal places. What is the final answer?",
        "expected": "52.33",
        "check": "numeric",
    },
    {
        "id": "chain_02",
        "category": "multi_step",
        "task": "Create a file called 'numbers.txt' with the numbers 1 through 10, one per line. Then write a Python script that reads the file, calculates the sum, and saves the result to 'sum.txt'. Finally, read sum.txt and tell me the answer.",
        "expected": "55",
        "check": "numeric",
    },

    # --- Error recovery ---
    {
        "id": "error_01",
        "category": "error_recovery",
        "task": "Try to read a file called 'nonexistent_file_xyz.txt'. When that fails, create it with the content 'recovered successfully', then read it again and tell me the content.",
        "expected": "recovered successfully",
        "check": "contains",
    },
    {
        "id": "error_02",
        "category": "error_recovery",
        "task": "Run this Python code: 'result = 1/0'. When it fails, fix the code to compute 1/0.5 instead and tell me the result.",
        "expected": "2.0",
        "check": "numeric",
    },

    # --- Planning & decomposition ---
    {
        "id": "plan_01",
        "category": "planning",
        "task": "I need to analyze some data. First, create a file 'sales.json' with this data: [{\"month\":\"Jan\",\"revenue\":1000},{\"month\":\"Feb\",\"revenue\":1500},{\"month\":\"Mar\",\"revenue\":1200}]. Then write Python code to find the month with highest revenue and the total revenue across all months. Report both.",
        "expected": "Feb",
        "check": "contains",
    },
    {
        "id": "plan_02",
        "category": "planning",
        "task": "Create a simple text-based todo list system: 1) Create 'todo.json' with 3 tasks (each with 'task' and 'done' fields, all initially false). 2) Mark the second task as done. 3) Read the file and tell me how many tasks are incomplete.",
        "expected": "2",
        "check": "numeric",
    },
]

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def check_answer(result, benchmark):
    """Check if the agent's answer matches expected."""
    if not result["success"] or result["answer"] is None:
        return False

    answer = str(result["answer"]).strip()
    check_type = benchmark["check"]
    expected = benchmark.get("expected")

    if check_type == "completed":
        return result["success"]

    elif check_type == "numeric":
        try:
            # Extract numbers from answer
            import re
            numbers = re.findall(r'-?\d+\.?\d*', answer)
            expected_num = float(expected)
            for n in numbers:
                if abs(float(n) - expected_num) < 0.1:
                    return True
            return False
        except (ValueError, TypeError):
            return False

    elif check_type == "contains":
        return expected.lower() in answer.lower()

    return False


def score_run(results):
    """Compute composite score from all benchmark results."""
    total = len(results)
    if total == 0:
        return {"composite": 0.0}

    successes = sum(1 for r in results if r["correct"])
    total_errors = sum(r["result"]["errors"] for r in results)
    total_recoveries = sum(r["result"]["error_recoveries"] for r in results)
    total_steps = sum(r["result"]["steps"] for r in results)
    max_possible_steps = total * 50  # MAX_STEPS

    success_rate = successes / total
    recovery_rate = total_recoveries / max(total_errors, 1)
    step_efficiency = 1.0 - (total_steps / max_possible_steps)

    # Composite: weighted average
    composite = (
        0.50 * success_rate +
        0.20 * recovery_rate +
        0.20 * step_efficiency +
        0.10 * (successes / total)  # bonus for correctness
    )

    return {
        "composite": round(composite, 4),
        "success_rate": round(success_rate, 4),
        "recovery_rate": round(recovery_rate, 4),
        "step_efficiency": round(step_efficiency, 4),
        "successes": successes,
        "total": total,
        "total_steps": total_steps,
        "total_errors": total_errors,
        "total_recoveries": total_recoveries,
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_evaluation(harness_module=None):
    """Run all benchmarks through the harness and return scored results."""
    
    # Import harness dynamically so we always get the latest version
    if harness_module is None:
        if 'harness' in sys.modules:
            del sys.modules['harness']
        import harness as harness_module

    results = []
    sandbox_base = "sandbox"

    for bench in BENCHMARKS:
        task_id = bench["id"]
        sandbox_dir = os.path.join(sandbox_base, task_id)
        
        # Clean sandbox for each task
        if os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir)
        os.makedirs(sandbox_dir, exist_ok=True)

        print(f"  Running {task_id}: {bench['category']}...", end=" ", flush=True)
        
        t0 = time.time()
        try:
            memory = harness_module.Memory(":memory:")
            result = harness_module.run_task(
                bench["task"],
                task_id=task_id,
                memory=memory,
                sandbox_dir=sandbox_dir
            )
            memory.close()
        except Exception as e:
            result = {
                "success": False,
                "answer": None,
                "steps": 0,
                "errors": 1,
                "error_recoveries": 0,
                "history": []
            }
            print(f"CRASH: {e}")
            continue

        elapsed = time.time() - t0
        correct = check_answer(result, bench)

        print(f"{'✓' if correct else '✗'} ({result['steps']} steps, {elapsed:.1f}s)")

        results.append({
            "benchmark": bench,
            "result": result,
            "correct": correct,
            "elapsed": elapsed,
        })

    scores = score_run(results)
    return results, scores


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Agent Harness Evaluation")
    print("=" * 60)
    print()

    results, scores = run_evaluation()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Composite Score:  {scores['composite']:.4f}")
    print(f"  Success Rate:     {scores['success_rate']:.1%} ({scores['successes']}/{scores['total']})")
    print(f"  Recovery Rate:    {scores['recovery_rate']:.1%}")
    print(f"  Step Efficiency:  {scores['step_efficiency']:.1%}")
    print(f"  Total Steps:      {scores['total_steps']}")
    print(f"  Total Errors:     {scores['total_errors']}")
    print(f"  Recoveries:       {scores['total_recoveries']}")
    print()
    print(f"composite_score: {scores['composite']:.4f}")
    print("---")
    print(json.dumps(scores, indent=2))
