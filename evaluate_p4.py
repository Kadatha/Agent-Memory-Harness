"""
Evaluation framework for agent harness research — Phase 4: Memory Optimization.
DO NOT MODIFY THIS FILE — the research agent only modifies harness.py.

Phase 4 benchmarks test memory capabilities:
- Retention accuracy across distractions
- Long-term persistence across simulated restarts
- Ambiguous/fuzzy recall
- Hybrid episodic + factual memory
- Decay and forgetting
- Adversarial/conflicting facts
- Domain-specific memory applications
"""

import json
import os
import shutil
import time
import importlib
import sys

# ---------------------------------------------------------------------------
# Benchmark Tasks — Phase 4: Memory Optimization
# ---------------------------------------------------------------------------

BENCHMARKS = [
    # ===== REGRESSION TESTS (from Phase 3) =====
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

    # ===== BASIC RETENTION =====
    {
        "id": "retain_01",
        "category": "basic_retention",
        "task": "Store these facts in memory: access_code='DELTA-9921', server_ip='10.0.44.7', admin_user='jcarter'. Then calculate 847 * 23. Then calculate the square root of 1764. After those calculations, recall the access_code and tell me what it is.",
        "expected": "DELTA-9921",
        "check": "contains",
    },
    {
        "id": "retain_02",
        "category": "basic_retention",
        "task": "Store 'meeting_room' = 'Conference B, 3rd Floor' in memory. Write a Python script that computes the prime factors of 360. After running the script, recall meeting_room and tell me where the meeting is.",
        "expected": "Conference B",
        "check": "contains",
    },
    {
        "id": "retain_03",
        "category": "basic_retention",
        "task": "Store these 3 items: color='cerulean', quantity=47, destination='warehouse_9'. Then write a file called 'distraction.txt' with a 5-line poem about robots. Then list the files in the current directory. Finally, recall all 3 stored items and report them.",
        "expected": "cerulean",
        "check": "contains",
        "also_expected": ["47", "warehouse_9"],
    },

    # ===== LONG-TERM PERSISTENCE =====
    {
        "id": "persist_01",
        "category": "long_persistence",
        "task": "Store 'client_name' = 'Marcus Webb' and 'contract_value' = '$2.4M' in memory. Then perform these 10 sequential tasks: (1) calculate 15*17, (2) write 'hello' to test1.txt, (3) calculate 99/7, (4) write 'world' to test2.txt, (5) calculate 2**16, (6) list files, (7) read test1.txt, (8) calculate sqrt(625), (9) write 'done' to test3.txt, (10) calculate 1000-377. After all 10 tasks, recall client_name and contract_value.",
        "expected": "Marcus Webb",
        "check": "contains",
        "also_expected": ["2.4M"],
    },
    {
        "id": "persist_02",
        "category": "long_persistence",
        "task": "Store these 5 key-value pairs: alpha='first', beta='second', gamma='third', delta='fourth', epsilon='fifth'. Then do 8 unrelated calculations (any math operations of your choice). After all calculations, recall ALL 5 values and list them in order (alpha through epsilon).",
        "expected": "first",
        "check": "contains",
        "also_expected": ["second", "third", "fourth", "fifth"],
    },
    {
        "id": "persist_03",
        "category": "long_persistence",
        "task": "Store 'project_deadline' = '2026-04-15' in memory. Then write a Python script that creates 5 files (data_1.txt through data_5.txt) each containing a random number. Read all 5 files back. Calculate the sum of the numbers. Write the sum to total.txt. After all of that, recall project_deadline and tell me when the project is due.",
        "expected": "2026-04-15",
        "check": "contains",
    },

    # ===== AMBIGUOUS RECALL =====
    {
        "id": "ambig_recall_01",
        "category": "ambiguous_recall",
        "task": "Store these customer notes: 'customer_john' = 'Prefers 7-gauge P&O, 60 inches wide, high ghost risk', 'customer_sarah' = 'Needs 10-gauge HR, 48 inches, reliable payer', 'customer_mike' = 'Wants specialty alloy, low volume, price-sensitive'. Now, without using exact keys, answer: Which customer is the picky one who wants specific gauge and width?",
        "expected": "john",
        "check": "contains",
    },
    {
        "id": "ambig_recall_02",
        "category": "ambiguous_recall",
        "task": "Store these facts: 'morning_meeting' = '9 AM with engineering team about API redesign', 'lunch_meeting' = '12 PM with client at downtown restaurant', 'afternoon_call' = '3 PM phone call with vendor about pricing'. Then answer: What am I doing around noon?",
        "expected": "client",
        "check": "contains",
    },
    {
        "id": "ambig_recall_03",
        "category": "ambiguous_recall",
        "task": "Store: 'tool_wrench' = 'in the garage, top shelf, red toolbox', 'tool_drill' = 'basement workshop, hanging on pegboard', 'tool_saw' = 'borrowed by neighbor Dave, due back Friday'. Where did I put the thing that makes holes?",
        "expected": "basement",
        "check": "contains",
    },

    # ===== HYBRID MEMORY TESTS =====
    {
        "id": "hybrid_01",
        "category": "hybrid_memory",
        "task": "Store 'budget_limit' = '50000' in memory. Then write a file 'expenses.json' with this data: [{\"item\": \"servers\", \"cost\": 22000}, {\"item\": \"licenses\", \"cost\": 15000}, {\"item\": \"training\", \"cost\": 8000}]. Read the file, recall the budget_limit from memory, and tell me if total expenses are within budget and by how much.",
        "expected": "5000",
        "check": "contains",
    },
    {
        "id": "hybrid_02",
        "category": "hybrid_memory",
        "task": "Write a CSV file 'sales.csv' with columns: month,revenue,costs. Add 6 months of data (Jan-Jun, make up realistic numbers where revenue > costs). Store 'target_margin' = '20' (percent) in memory. Read the CSV, recall the target margin, and tell me which months met or exceeded the target margin.",
        "expected": None,
        "check": "completed",
    },
    {
        "id": "hybrid_03",
        "category": "hybrid_memory",
        "task": "Store 'formula' = 'price * quantity * (1 - discount/100)' in memory. Write a file 'order.json' with {\"price\": 45.50, \"quantity\": 200, \"discount\": 12}. Read the file, recall the formula from memory, compute the result using the calculator, and tell me the total.",
        "expected": "8008",
        "check": "numeric",
    },

    # ===== DECAY AND COMPRESSION =====
    {
        "id": "decay_01",
        "category": "decay",
        "task": "Store these facts with varying importance: 'critical_password' = 'X9kL$mN2' (critical), 'lunch_order_tuesday' = 'turkey sandwich' (trivial), 'server_ip_prod' = '192.168.1.100' (critical), 'weather_yesterday' = 'partly cloudy' (trivial), 'api_key_payment' = 'sk_live_abc123' (critical). Simulate 7 days passing (store a timestamp, then store a new timestamp 7 days later). After the simulated time passage, recall all facts. Critical facts should be retained; trivial facts may be forgotten. Report which facts you still have.",
        "expected": "X9kL$mN2",
        "check": "contains",
        "also_expected": ["192.168.1.100", "sk_live_abc123"],
    },
    {
        "id": "decay_02",
        "category": "decay",
        "task": "Store 10 facts numbered fact_1 through fact_10 with values 'value_1' through 'value_10'. Mark odd-numbered facts as 'high confidence' and even-numbered as 'low confidence' (store a confidence key for each). After storing all facts, retrieve only the high-confidence facts (odd numbers). List their values.",
        "expected": "value_1",
        "check": "contains",
        "also_expected": ["value_3", "value_5", "value_7", "value_9"],
    },

    # ===== ADVERSARIAL MEMORY =====
    {
        "id": "adversarial_01",
        "category": "adversarial",
        "task": "Store 'server_port' = '8080'. Then store 'server_port' = '3000' (overwriting). Then store 'server_port' = '443'. Recall server_port. The answer should be the MOST RECENT value. What port is the server on?",
        "expected": "443",
        "check": "contains",
    },
    {
        "id": "adversarial_02",
        "category": "adversarial",
        "task": "Store 'ceo_name' = 'Alice Johnson'. Store 'ceo_name_backup' = 'Alice Johnson'. Now store 'ceo_name' = 'Bob Smith' (simulating a correction). Recall both 'ceo_name' and 'ceo_name_backup'. Note the conflict — the backup is outdated. Report the current CEO name and flag that the backup is stale.",
        "expected": "Bob Smith",
        "check": "contains",
    },
    {
        "id": "adversarial_03",
        "category": "adversarial",
        "task": "Store 'temperature' = '72°F'. Store 'temperature_celsius' = '22°C'. These are consistent. Now store 'temperature' = '90°F' but do NOT update temperature_celsius. Recall both values, detect the inconsistency, and report that the Celsius value needs updating. What should the Celsius value be?",
        "expected": "32",
        "check": "numeric",
    },

    # ===== DOMAIN-SPECIFIC (Steel/Sales) =====
    {
        "id": "domain_01",
        "category": "domain_specific",
        "task": "Store these steel lead details: 'lead_apex_mfg' = 'Contact: Jim Torres, needs 7ga HR P&O, 60in wide, 500 tons/month, price-sensitive, ghost risk medium', 'lead_summit_fab' = 'Contact: Dana Lee, needs 10ga CR, 48in wide, 200 tons/month, quality-focused, reliable payer', 'lead_river_steel' = 'Contact: Carlos Vega, needs 14ga galv, 36in wide, 100 tons/month, new customer, unknown risk'. Which lead has the highest monthly tonnage? Who should I call first for a high-volume opportunity?",
        "expected": "apex",
        "check": "contains",
    },
    {
        "id": "domain_02",
        "category": "domain_specific",
        "task": "Store these price points: 'price_hr_7ga' = '$42.50/cwt', 'price_cr_10ga' = '$51.20/cwt', 'price_galv_14ga' = '$58.75/cwt'. Store 'margin_target' = '15%'. A customer wants 300 tons of HR 7ga. Calculate the revenue at the stored price (1 ton = 20 cwt), then calculate what price per cwt would give exactly 15% margin above a cost basis of $36.00/cwt. Report both numbers.",
        "expected": "255000",
        "check": "contains",
    },
]

# ---------------------------------------------------------------------------
# Scoring — Phase 4 Composite
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
                if abs(float(n) - expected_num) < max(0.5, expected_num * 0.02):
                    return True
            return False
        except (ValueError, TypeError):
            return False

    elif check_type == "contains":
        primary_match = expected.lower() in answer.lower()
        # Check additional expected values if present
        also = benchmark.get("also_expected", [])
        also_match = all(e.lower() in answer.lower() for e in also)
        return primary_match and also_match

    return False


def score_run(results):
    """Compute Phase 4 composite score from all benchmark results."""
    total = len(results)
    if total == 0:
        return {"composite": 0.0}

    # Category groupings for weighted scoring
    retention_cats = {"basic_retention", "long_persistence", "ambiguous_recall"}
    retrieval_cats = {"basic_retention", "long_persistence", "hybrid_memory"}
    decay_cats = {"decay"}
    robustness_cats = {"adversarial"}
    regression_cats = {"regression"}

    # Retention accuracy: correct recall across memory-focused tasks
    retention_tasks = [r for r in results if r["benchmark"]["category"] in retention_cats]
    retention_score = sum(1 for r in retention_tasks if r["correct"]) / max(len(retention_tasks), 1)

    # Retrieval efficiency: fewer steps to retrieve = better
    retrieval_tasks = [r for r in results if r["benchmark"]["category"] in retrieval_cats]
    if retrieval_tasks:
        avg_steps = sum(r["result"]["steps"] for r in retrieval_tasks) / len(retrieval_tasks)
        # Normalize: 1 step = 1.0, 10+ steps = 0.0
        retrieval_score = max(0.0, 1.0 - (avg_steps - 1) / 9)
    else:
        retrieval_score = 0.0

    # Decay effectiveness: correct on decay benchmarks
    decay_tasks = [r for r in results if r["benchmark"]["category"] in decay_cats]
    decay_score = sum(1 for r in decay_tasks if r["correct"]) / max(len(decay_tasks), 1)

    # Robustness: correct on adversarial benchmarks
    robust_tasks = [r for r in results if r["benchmark"]["category"] in robustness_cats]
    robust_score = sum(1 for r in robust_tasks if r["correct"]) / max(len(robust_tasks), 1)

    # Regression check (not in composite, but reported)
    reg_tasks = [r for r in results if r["benchmark"]["category"] in regression_cats]
    reg_score = sum(1 for r in reg_tasks if r["correct"]) / max(len(reg_tasks), 1)

    # Domain + hybrid (folded into retention for scoring)
    domain_hybrid = [r for r in results if r["benchmark"]["category"] in {"domain_specific", "hybrid_memory"}]
    domain_score = sum(1 for r in domain_hybrid if r["correct"]) / max(len(domain_hybrid), 1)

    # Overall success rate
    successes = sum(1 for r in results if r["correct"])
    success_rate = successes / total

    total_errors = sum(r["result"]["errors"] for r in results)
    total_recoveries = sum(r["result"]["error_recoveries"] for r in results)
    total_steps = sum(r["result"]["steps"] for r in results)

    # Phase 4 composite: memory-weighted
    composite = (
        0.40 * retention_score +
        0.30 * retrieval_score +
        0.20 * decay_score +
        0.10 * robust_score
    )

    return {
        "composite": round(composite, 4),
        "retention_score": round(retention_score, 4),
        "retrieval_score": round(retrieval_score, 4),
        "decay_score": round(decay_score, 4),
        "robustness_score": round(robust_score, 4),
        "regression_score": round(reg_score, 4),
        "domain_hybrid_score": round(domain_score, 4),
        "success_rate": round(success_rate, 4),
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
    print("Agent Harness Evaluation — Phase 4: Memory Optimization")
    print("=" * 60)
    print(f"  Benchmarks: {len(BENCHMARKS)}")
    print()

    results, scores = run_evaluation()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Composite Score:    {scores['composite']:.4f}")
    print(f"  Retention:          {scores['retention_score']:.4f} (40%)")
    print(f"  Retrieval Eff:      {scores['retrieval_score']:.4f} (30%)")
    print(f"  Decay:              {scores['decay_score']:.4f} (20%)")
    print(f"  Robustness:         {scores['robustness_score']:.4f} (10%)")
    print(f"  ---")
    print(f"  Regression:         {scores['regression_score']:.4f} (must be 1.0)")
    print(f"  Domain/Hybrid:      {scores['domain_hybrid_score']:.4f}")
    print(f"  Overall Success:    {scores['success_rate']:.1%} ({scores['successes']}/{scores['total']})")
    print(f"  Total Steps:        {scores['total_steps']}")
    print(f"  Total Errors:       {scores['total_errors']}")
    print(f"  Recoveries:         {scores['total_recoveries']}")
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
