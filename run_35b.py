"""Resilient baseline run with qwen3.5:35b-a3b model.
Catches per-task crashes and continues. Writes results after EACH task."""
import sys
import io
import os
import time
import json
import shutil

os.environ["PYTHONIOENCODING"] = "utf-8:replace"

log_file = open("run_35b_log.txt", "w", encoding="utf-8", errors="replace")
sys.stdout = log_file
sys.stderr = log_file

import harness
harness.MODEL = "qwen3.5:35b-a3b"

import evaluate_p4

results = []
sandbox_base = "sandbox"

for bench in evaluate_p4.BENCHMARKS:
    task_id = bench["id"]
    sandbox_dir = os.path.join(sandbox_base, task_id)

    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)
    os.makedirs(sandbox_dir, exist_ok=True)

    print(f"  Running {task_id}: {bench['category']}...", end=" ", flush=True)

    t0 = time.time()
    try:
        memory = harness.Memory(":memory:")
        result = harness.run_task(
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
        print(f"CRASH: {e}", flush=True)
        # Wait a moment for Ollama to recover if it restarted
        time.sleep(5)

    elapsed = time.time() - t0
    correct = evaluate_p4.check_answer(result, bench)

    status = "PASS" if correct else "FAIL"
    print(f"{'[OK]' if correct else '[X]'} ({result['steps']} steps, {elapsed:.1f}s)", flush=True)

    results.append({
        "benchmark": bench,
        "result": result,
        "correct": correct,
        "elapsed": elapsed,
    })

    # Write incremental results after each task (crash-safe)
    with open("run_35b_progress.txt", "w", encoding="utf-8", errors="replace") as pf:
        for r in results:
            s = "PASS" if r["correct"] else "FAIL"
            pf.write(f"  {r['benchmark']['id']:25s} {r['benchmark']['category']:20s} {s}  {r['result']['steps']:3d} steps  {r['elapsed']:.1f}s\n")

# Score the run
scores = evaluate_p4.score_run(results)

# Write final results
with open("run_35b_results.txt", "w", encoding="utf-8", errors="replace") as f:
    f.write("=" * 60 + "\n")
    f.write("35B-A3B BASELINE RESULTS\n")
    f.write("=" * 60 + "\n")
    f.write(f"  Composite Score:    {scores['composite']:.4f}\n")
    f.write(f"  Retention:          {scores['retention_score']:.4f}\n")
    f.write(f"  Retrieval Eff:      {scores['retrieval_score']:.4f}\n")
    f.write(f"  Decay:              {scores['decay_score']:.4f}\n")
    f.write(f"  Robustness:         {scores['robustness_score']:.4f}\n")
    f.write(f"  Regression:         {scores['regression_score']:.4f}\n")
    f.write(f"  Domain/Hybrid:      {scores['domain_hybrid_score']:.4f}\n")
    f.write(f"  Success Rate:       {scores['success_rate']:.1%} ({scores['successes']}/{scores['total']})\n")
    f.write(f"  Total Steps:        {scores['total_steps']}\n")
    f.write(f"  Total Errors:       {scores['total_errors']}\n")
    f.write(f"  Recoveries:         {scores['total_recoveries']}\n")
    f.write("\n  Per-Category:\n")
    
    categories = {}
    for r in results:
        cat = r["benchmark"]["category"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0, "steps": 0}
        categories[cat]["total"] += 1
        categories[cat]["steps"] += r["result"]["steps"]
        if r["correct"]:
            categories[cat]["correct"] += 1
    
    for cat, stats in sorted(categories.items()):
        f.write(f"    {cat}: {stats['correct']}/{stats['total']} ({stats['steps']} steps)\n")
    
    f.write("\n  Per-Task:\n")
    for r in results:
        b = r["benchmark"]
        status = "PASS" if r["correct"] else "FAIL"
        f.write(f"    {b['id']}: {status} ({r['result']['steps']} steps, {r['elapsed']:.1f}s)\n")

print("\nDONE. Results written to run_35b_results.txt", flush=True)
log_file.close()
