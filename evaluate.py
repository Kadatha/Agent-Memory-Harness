"""
Evaluation framework for agent harness research — Phase 3: Hard Mode.
DO NOT MODIFY THIS FILE — the research agent only modifies harness.py.

Phase 3 benchmarks test capabilities that broke Phase 2:
- Ambiguous instructions requiring interpretation
- Multi-file operations with dependencies
- Tasks requiring backtracking/self-correction
- Long reasoning chains (10+ steps)
- Adversarial edge cases
- Cross-task memory persistence
"""

import json
import os
import shutil
import time
import importlib
import sys

# ---------------------------------------------------------------------------
# Benchmark Tasks — Phase 3 Hard Mode
# ---------------------------------------------------------------------------

BENCHMARKS = [
    # ===== RETAINED FROM PHASE 2 (regression tests) =====
    {
        "id": "reg_01",
        "category": "regression",
        "task": "Calculate: (17 * 23) + (45 * 12) - (100 / 4). Give the exact numerical answer.",
        "expected": "906.0",
        "check": "numeric",
    },
    {
        "id": "reg_02",
        "category": "regression",
        "task": "Write a Python script that generates the first 10 Fibonacci numbers (starting 0, 1, 1, 2, 3, 5, 8, 13, 21, 34) and saves them as a JSON list to 'fibonacci.json'. Then read the file back and tell me the sum of all 10 numbers.",
        "expected": "88",
        "check": "numeric",
    },
    {
        "id": "reg_03",
        "category": "regression",
        "task": "Try to read a file called 'nonexistent_file_xyz.txt'. When that fails, create it with the content 'recovered successfully', then read it again and tell me the content.",
        "expected": "recovered successfully",
        "check": "contains",
    },

    # ===== AMBIGUOUS INSTRUCTIONS =====
    {
        "id": "ambig_01",
        "category": "ambiguous",
        "task": "Sort these numbers and give me the middle one: 42, 17, 83, 56, 31.",
        "expected": "42",
        "check": "numeric",
    },
    {
        "id": "ambig_02",
        "category": "ambiguous",
        "task": "I have a list of temperatures in Celsius: 20, 25, 30, 15, 35. Convert each to Fahrenheit, find the average of the Fahrenheit values, then convert that average back to Celsius. What do you get?",
        "expected": "25",
        "check": "numeric",
    },
    {
        "id": "ambig_03",
        "category": "ambiguous",
        "task": "Write some data to a file, process it, and tell me something interesting about it. Use these numbers: 2, 4, 8, 16, 32, 64, 128.",
        "expected": None,
        "check": "completed",
    },

    # ===== MULTI-FILE OPERATIONS =====
    {
        "id": "multi_file_01",
        "category": "multi_file",
        "task": "Create three files: 'part1.txt' with 'Hello', 'part2.txt' with ' ', 'part3.txt' with 'World'. Then write a Python script that reads all three files, concatenates their contents, and saves the result to 'combined.txt'. Read combined.txt and tell me what it says.",
        "expected": "Hello World",
        "check": "contains",
    },
    {
        "id": "multi_file_02",
        "category": "multi_file",
        "task": "Create a JSON file 'users.json' with 3 users (name, age, department). Create another JSON file 'departments.json' mapping department names to budgets. Write Python code that joins the data and finds which department has the oldest employee. Tell me the department name and the employee's age.",
        "expected": None,
        "check": "completed",
    },
    {
        "id": "multi_file_03",
        "category": "multi_file",
        "task": "Create a Python module file called 'mathutils.py' with functions add(a,b) and multiply(a,b). Then create a separate script 'main.py' that imports mathutils and computes add(multiply(3,4), multiply(5,6)). Run main.py and tell me the result.",
        "expected": "42",
        "check": "numeric",
    },

    # ===== BACKTRACKING & SELF-CORRECTION =====
    {
        "id": "backtrack_01",
        "category": "backtracking",
        "task": "Write a Python script that finds all two-digit prime numbers whose digits sum to 10. If your first approach has a bug or gives wrong results, fix it and try again. List all such primes.",
        "expected": "19",
        "check": "contains",
    },
    {
        "id": "backtrack_02",
        "category": "backtracking",
        "task": "Create a CSV file with headers 'item,price,quantity'. Add 5 rows of store inventory data. Then write code to find the total inventory value (price * quantity for each item, summed). If you get an error reading the CSV, debug and fix it. Tell me the total value.",
        "expected": None,
        "check": "completed",
    },

    # ===== LONG REASONING CHAINS =====
    {
        "id": "long_01",
        "category": "long_chain",
        "task": "Solve this step by step: Start with 100. Subtract 17. Multiply by 3. Add 49. Divide by 2. Subtract 31. Multiply by 4. Add 7. Divide by 3. Round to the nearest integer. What is the result?",
        "expected": "153",
        "check": "numeric",
    },
    {
        "id": "long_02",
        "category": "long_chain",
        "task": "Create a file 'log.txt'. Write 'Step 1: initialized' to it. Then, in a loop of 5 iterations: read the file, count the lines, write 'Step N: count was X' (where N is the current step and X is the line count). After all iterations, read the file and tell me how many lines it has.",
        "expected": "6",
        "check": "numeric",
    },
    {
        "id": "long_03",
        "category": "long_chain",
        "task": "Write a Python script that implements bubble sort from scratch (no built-in sort). Sort the list [64, 34, 25, 12, 22, 11, 90] and save each pass of the sort to 'sort_log.txt' (one line per pass). Then tell me the sorted list and how many passes it took.",
        "expected": "11, 12, 22, 25, 34, 64, 90",
        "check": "contains",
    },

    # ===== ADVERSARIAL EDGE CASES =====
    {
        "id": "edge_01",
        "category": "edge_case",
        "task": "Calculate the factorial of 0. Then calculate the factorial of 1. Then calculate the factorial of 10. Give all three answers separated by commas.",
        "expected": "3628800",
        "check": "contains",
    },
    {
        "id": "edge_02",
        "category": "edge_case",
        "task": "Create an empty file called 'empty.txt'. Read it. Write 'not empty anymore' to it. Read it again. Tell me what you got from BOTH reads.",
        "expected": "not empty anymore",
        "check": "contains",
    },
    {
        "id": "edge_03",
        "category": "edge_case",
        "task": "Write Python code that handles these cases: divide 10 by 3 (float division), divide 10 by 0 (should catch the error and return 'infinity'), and divide 0 by 10. Report all three results.",
        "expected": "infinity",
        "check": "contains",
    },

    # ===== MEMORY PERSISTENCE =====
    {
        "id": "mem_01",
        "category": "memory_hard",
        "task": "Store these 5 facts in memory: pi=3.14159, euler=2.71828, golden=1.61803, sqrt2=1.41421, ln2=0.69315. Then recall euler and golden, multiply them together using the calculator, and tell me the result.",
        "expected": "4.39",
        "check": "numeric",
    },
    {
        "id": "mem_02",
        "category": "memory_hard",
        "task": "Store 'secret_code' = 'ALPHA-7742-BRAVO' in memory. Then do 3 unrelated calculations (any math). After the calculations, recall the secret code and tell me what it is.",
        "expected": "ALPHA-7742-BRAVO",
        "check": "contains",
    },

    # ===== DATA ANALYSIS =====
    {
        "id": "analysis_01",
        "category": "analysis",
        "task": "Create a JSON file with monthly sales data for a year (Jan-Dec, make up realistic numbers between 10000 and 50000). Write Python code to find: the best month, the worst month, the average, and the standard deviation. Report all four.",
        "expected": None,
        "check": "completed",
    },
    {
        "id": "analysis_02",
        "category": "analysis",
        "task": "Write Python code that generates 100 random numbers between 1 and 1000 (use seed 42 for reproducibility), saves them to 'numbers.json', then computes: mean, median, mode (most frequent tens digit), and how many are prime. Report all four statistics.",
        "expected": None,
        "check": "completed",
    },

    # ===== DEBUGGING =====
    {
        "id": "debug_01",
        "category": "debugging",
        "task": "Run this buggy Python code: 'data = {\"a\": 1, \"b\": 2}; print(data[\"c\"])'. It will crash. Fix it to print the value of key 'c' with a default of 0 if the key doesn't exist. Tell me the output.",
        "expected": "0",
        "check": "numeric",
    },
    {
        "id": "debug_02",
        "category": "debugging",
        "task": "Run this code: 'nums = [1,2,3,4,5]; result = nums[5]'. It will crash with an IndexError. Fix the code to safely get the last element instead. Tell me the result.",
        "expected": "5",
        "check": "numeric",
    },

    # ===== SEMANTIC RETRIEVAL =====
    {
        "id": "semantic_01",
        "category": "semantic_retrieval",
        "task": "Store this information in memory: 'John Smith works as a software engineer at TechCorp and enjoys hiking on weekends'. Later, without using the exact words, find information about someone who codes professionally and likes outdoor activities.",
        "expected": "John Smith",
        "check": "contains",
    },
    {
        "id": "semantic_02", 
        "category": "semantic_retrieval",
        "task": "Store these facts: 'The capital of France is Paris', 'Tokyo is Japan's largest city', 'London is in England'. Then find information about a European metropolitan area without using the words 'capital', 'France', or 'Paris'.",
        "expected": "London",
        "check": "contains",
    },
    {
        "id": "semantic_03",
        "category": "semantic_retrieval", 
        "task": "Remember: 'Project Alpha deadline is March 15, 2024', 'Beta release scheduled for April 30', 'Gamma testing begins in May'. Later, find information about what happens in the spring of 2024 without mentioning specific project names.",
        "expected": "April 30",
        "check": "contains",
    },
    {
        "id": "semantic_04",
        "category": "semantic_retrieval",
        "task": "Store: 'The red car costs $25,000', 'Blue vehicle priced at $30,000', 'Green automobile is $22,000'. Then find the least expensive transportation option without using color words or 'cost'.",
        "expected": "22,000",
        "check": "contains",
    },
    {
        "id": "semantic_05",
        "category": "semantic_retrieval",
        "task": "Remember these relationships: 'Alice reports to Bob', 'Bob reports to Carol', 'Dave reports to Alice'. Create a hierarchy diagram, then find who is at the top of the management structure without directly stating their name in your query.",
        "expected": "Carol",
        "check": "contains",
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
            import re
            numbers = re.findall(r'-?\d+\.?\d*', answer)
            expected_num = float(expected)
            for n in numbers:
                if abs(float(n) - expected_num) < 0.5:
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
    
    if harness_module is None:
        if 'harness' in sys.modules:
            del sys.modules['harness']
        import harness as harness_module

    results = []
    sandbox_base = "sandbox"

    for bench in BENCHMARKS:
        task_id = bench["id"]
        sandbox_dir = os.path.join(sandbox_base, task_id)
        
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
    print("Agent Harness Evaluation — Phase 3: Hard Mode")
    print("=" * 60)
    print(f"  Benchmarks: {len(BENCHMARKS)}")
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
    
    # Per-category breakdown
    categories = {}
    for r in results:
        cat = r["benchmark"]["category"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["correct"]:
            categories[cat]["correct"] += 1
    
    print("  Per-Category:")
    for cat, stats in sorted(categories.items()):
        print(f"    {cat}: {stats['correct']}/{stats['total']}")
    
    print()
    print(f"composite_score: {scores['composite']:.4f}")
    print("---")
    print(json.dumps(scores, indent=2))
