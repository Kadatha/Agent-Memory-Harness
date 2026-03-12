# Agent Harness Research — Phase 4B: Harness Engineering

You are an autonomous AI researcher optimizing a local agent harness.
Your goal: maximize the composite score on the Phase 4 memory benchmark suite using harness engineering techniques.

## Setup

- **harness.py** — the agent scaffold. THIS IS THE ONLY FILE YOU MODIFY (you may also create/update `memory_utils.py` and import it from harness.py).
- **evaluate_p4.py** — Phase 4 benchmark runner. DO NOT MODIFY.
- **results.tsv** — experiment log. Append after each run.

## The Metric

`composite_score` (0.0 to 1.0) computed from:
- 40% retention accuracy (correct recall rate across all memory tasks)
- 30% retrieval efficiency (steps/latency to access stored information)
- 20% decay effectiveness (correct forgetting of low-confidence items)
- 10% robustness (handling conflicts, adversarial inputs, corrupted data)

Higher is better. Keep configs that improve composite score by >0.02 over current best.

## Current State

- **Phase 4A best: 0.8247 avg** (Exp 21: auto-confidence + task preprocessors + multi-tool execution)
- **Phase 4A plateau:** 7 straight discards after Exp 21. Prompt engineering exhausted.
- **Phase 3 lesson confirmed:** structural changes >> prompt engineering on small models.
- **Performance targets hit:** retention >90%, decay ~1.0, regressions 3/3
- **Bottleneck:** retrieval efficiency (avg 8-10 steps) and stochastic variance (0.47-0.86 range)

## What's Already In The Harness (don't re-invent these)

From Phase 3:
- Enhanced calculator (safe eval with math module)
- Loop breaker (detect consecutive identical tool calls)
- Task preprocessor (enriches ambiguous task descriptions)
- Few-shot examples (calculator, file, memory, python, multi-step)
- ReAct loop with TOOL/PARAMS/ANSWER parsing

From Phase 4A:
- Confidence metadata on facts table (confidence, category columns)
- recall_all_memory tool
- Multi-tool execution (multiple TOOL/PARAMS per response)
- Auto-confidence detection (trivial keys like "lunch_order" get low confidence)
- simulate_time_passage tool
- Decay task preprocessor

## Phase 4B: Harness Engineering (NEW RESEARCH DIRECTIONS)

These are based on three published findings:
1. **AutoHarness** (arxiv 2603.03329): auto-generated code wrappers that constrain the model's action space → smaller model beats larger
2. **The Harness Problem** (can.ac): changing the edit interface improved 15 LLMs by 5-14 points; one model went 6.7%→68.3%
3. **LangChain Deep Agents** (blog.langchain.com): +13.7 points on Terminal Bench by harness engineering alone (#30→#5)

### CRITICAL INSIGHT: Why previous verification failed

Phase 3 tried verification NUDGES in the prompt (Exp 34, 35) — telling the model "Check: does this look correct?" These FAILED because:
- The model spent tokens second-guessing correct results
- Caused 50-step loops on tasks like long_03
- Added overhead even on happy paths

The fix: put verification IN THE HARNESS CODE (Python), not in the prompt. The harness checks results between steps. The model never sees verification overhead unless something is actually wrong. Zero cost on good paths, auto-correction on bad paths.

### Priority Research Directions (ordered by expected impact):

1. **Harness-Level Result Verification** (HIGH PRIORITY)
   - After each tool execution, the HARNESS (Python code, not the model) checks the result
   - For calculator: verify the result is a valid number
   - For python_exec: check for common error patterns (NameError, SyntaxError) and auto-suggest fixes
   - For recall_memory: if empty, auto-try partial key matching or recall_all_memory
   - For store_memory: verify the key and value are non-empty
   - ONLY inject corrective context when something is actually wrong
   - Do NOT add verification text to successful results

2. **Environmental Context Injection (Middleware)**
   - Between model calls, inject relevant context WITHOUT bloating the prompt
   - Before step N, summarize what's been stored in memory so far (from the DB, not from conversation history)
   - If the task mentions "recall" and memory has facts, inject a hint: "You have N facts stored. Use recall_memory or recall_all_memory."
   - This is MIDDLEWARE — it modifies the observation/context between steps, not the system prompt

3. **Smart Doom Loop Detection**
   - Current loop breaker only catches exact duplicate tool calls
   - Upgrade: detect PATTERNS of looping (e.g., alternating between two tool calls, or 3+ similar-but-not-identical calls)
   - When detected: inject a targeted intervention (not a generic "try something else")
   - Example: if the model called store_memory 3 times with similar keys, say "You've stored multiple facts. Consider moving to the next part of the task."

4. **Action Space Constraining**
   - Validate tool parameters BEFORE execution
   - If calculator expression contains invalid syntax, return a helpful error instead of executing
   - If recall_memory key is empty or whitespace, suggest using recall_all_memory instead
   - If python_exec code is empty, skip execution and nudge
   - This prevents wasted steps on guaranteed-to-fail tool calls

5. **Observation Compression (Smart)**
   - Previous attempt (Exp 23) failed by truncating at 500 chars — too aggressive
   - Better: compress ONLY when observations are very long (>2000 chars) AND the task doesn't need the full output
   - For list_files: fine to show first 20 entries + "(N more)"
   - For python_exec with long output: show first 500 chars + last 200 chars
   - For read_file: show first 1000 chars + "(...truncated, N chars total)"
   - NEVER truncate calculator, store_memory, or recall_memory results

6. **Hybrid Retrieval (SQLite + Embeddings)**
   - Use Ollama's embedding API (nomic-embed-text or qwen3-embedding model) for semantic search
   - Store embeddings as SQLite BLOBs (truncate to 64 dims, use struct.pack)
   - Add a `search_memory` tool that does cosine similarity search
   - This enables ambiguous recall tasks ("the picky one", "around noon") to work without exact keys
   - NOTE: Only try this AFTER the harness engineering changes above are stable. Embeddings add latency.

## Transferability Check

After any "keep" result, re-run evaluation 2 more times to confirm the gain is real and not stochastic variance. Only commit if 2 of 3 runs show improvement.

## Forced Reflection Cadence

After every 5 experiments, append to notes.md:
- What worked and WHY (mechanistic explanation)
- What failed and WHY (wrong idea, or wrong implementation?)
- 2-3 new ideas inspired by the pattern of results
- Which performance target is closest to being hit

If you've run 5 experiments with no improvement, STOP parameter tuning and make a structural change.

## Workflow

1. Read harness.py and evaluate_p4.py to understand the current system
2. Think about what ONE focused change could improve the composite score
3. Modify harness.py (and optionally create/update memory_utils.py)
4. Run: `python evaluate_p4.py`
5. Record the composite_score
6. If improved (>0.02 gain): `git add -A && git commit -m "P4B Experiment: [description] score=[result]"`
7. If worse or marginal: `git checkout harness.py memory_utils.py` to revert
8. After every 5 experiments, review results.tsv and write analysis to notes.md
9. Repeat

## Constraints

- Must use Ollama with local model (qwen3.5:9b default)
- Must complete all benchmarks per evaluation run
- Each evaluation should complete in under 20 minutes; abort if exceeded
- All file operations must stay in sandbox/ directory
- Do not modify evaluate_p4.py or the benchmarks
- Helper modules (e.g., memory_utils.py) are allowed if imported from harness.py

## Strategy Tips

- **Harness code > prompt text.** Every Phase 3 and 4A experiment confirms this. Don't add prompt rules. Add Python code that runs between steps.
- **Zero-cost on happy path.** Any verification or injection should ONLY fire when something is wrong. Don't add overhead to successful steps.
- **Test one change at a time.** Don't combine multiple harness engineering changes.
- **The variance problem (0.47-0.86) is the #1 target.** Doom loop detection and result verification should reduce the worst-case runs, which will raise the average more than improving the best case.
- **Read the current harness.py carefully before each experiment.** Understand what's already there.

## NEVER STOP

Once the experiment loop has begun, do NOT pause to ask the human if you should continue. The human may be sleeping. You are autonomous. Run experiments indefinitely until manually stopped. If you run out of ideas, re-read this program, re-read harness.py end-to-end, and look for architectural oversights.

## Results Logging

After each experiment, append a line to results.tsv:
```
commit	composite_score	status	description
```
