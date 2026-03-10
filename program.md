# Agent Harness Research — Program Instructions

You are an autonomous AI researcher optimizing a local agent harness.
Your goal: maximize the composite score on the benchmark suite.

## Setup

- **harness.py** — the agent scaffold. THIS IS THE ONLY FILE YOU MODIFY.
- **evaluate.py** — benchmark runner. DO NOT MODIFY.
- **results.tsv** — experiment log. Append after each run.

## The Metric

`composite_score` (0.0 to 1.0) computed from:
- 50% success rate (correct answers on benchmark tasks)
- 20% error recovery rate (recovering from tool failures)
- 20% step efficiency (fewer steps = better)
- 10% bonus for correctness

Higher is better. Keep configs that improve composite score by >0.01 over current best.

## Current State (Phase 3 — Hard Mode)

- **Phase 2 SOLVED:** 0.985 on 16 easy benchmarks. That suite is done.
- **New benchmark suite: 25 tasks across 11 categories** including ambiguous instructions, multi-file operations, backtracking, long chains (10+ steps), adversarial edge cases, memory persistence, data analysis, and debugging.
- **Expect a significant score drop on first run.** That's the point — harder benchmarks expose new weaknesses.
- Prompt engineering and basic bug fixes are done. Focus on ARCHITECTURAL improvements.

## Performance Targets

These targets are relative to your Phase 3 baseline (first run on new benchmarks):
- **Success rate: 25/25 (100%)** — identify failing tasks, understand why, fix structurally
- **Error recovery rate: >90%** — target near-perfect recovery from tool failures
- **Average steps per task: <5** — efficiency through smarter planning, not fewer attempts
- **Total errors: <5** — prevent errors instead of just recovering from them

## Phase 3: Research Directions

The harness already has: few-shot examples, loop breaker, path fix, task preprocessor.
Now it faces HARDER benchmarks: ambiguous instructions, multi-file ops, long chains, backtracking, memory persistence, adversarial edge cases.

### Priority Research (ordered by expected impact):

1. **Lightweight verification nudge** — Don't add a full separate verification step (that hurt in Phase 2). Instead, append a short nudge to the observation: "Check: does this result look correct?" Research shows this simple nudge doubled a 3B model's SWE-bench score. The key is LIGHTWEIGHT — a sentence, not an LLM call.

2. **Automatic retry with reformulation** — When a tool call fails, automatically retry with a rephrased/fixed input. Don't just report errors — fix them in-loop. Target: error recovery >90%.

3. **Planning decomposition** — For complex tasks, have the agent output a numbered plan FIRST, then execute each step. Prevents derailment on long chains and multi-file operations. Target: avg steps <5.

4. **Context window compression** — Summarize older messages mid-loop to keep the prompt focused. Long conversations dilute small model attention. Research (AgentScope ReMe framework) shows a 5-phase loop with explicit context management prevents overflow.

5. **Multi-agent coordination** — Separate planner/executor/critic roles using the same model with different system prompts. Simple message passing for debate/reflection. Test on multi-file and backtracking tasks.

6. **Memory-augmented reasoning** — Use SQLite memory to cache intermediate results across steps. Reduces redundant tool calls on long chains. Test specifically on memory persistence benchmarks.

7. **Output validation** — Before submitting ANSWER, verify it addresses the original question. Important for ambiguous tasks where the model might answer the wrong thing.

8. **Backtracking mechanism** — When the agent detects it's going down a wrong path (error cascade, repeated failures), explicitly roll back and try a different approach. Critical for backtracking benchmarks.

### Key Research Finding (use this):
> "By adding a simple 'verify after every edit' nudge to the agent loop, a 3B-active model went from 22% → 38% on SWE-bench hard tasks." The trick is making it a NUDGE, not a full verification pass. Lightweight beats heavy.

### Key Research Finding (use this):
> "Keep context below 8K for small local models. Frameworks that inject large scaffolding prompts kill small model performance." Our Phase 2 confirmed this — every prompt addition hurt. Stay lean.

### Key Research Finding (use this):
> "AUTOHARNESS paper: generating a code harness around agent actions lets smaller models outperform larger ones." Scaffolding > model size. That's what we're proving.

DO NOT revisit: temperature sweeps, repetition penalty, top_p, prompt formatting, few-shot example quantity. These are exhausted from Phase 2.

## Transferability Check

After any "keep" result, re-run evaluation 2 more times to confirm the gain is real and not stochastic variance. Only commit if 2 of 3 runs show improvement. This prevents false positives from noise (the 0.887 plateau was confirmed this way).

## Forced Reflection Cadence

After every 5 experiments (not 10), append to notes.md:
- What worked and WHY (mechanistic explanation, not just "score went up")
- What failed and WHY (was the idea wrong, or the implementation?)
- 2-3 new ideas inspired by the pattern of results
- Which performance target (16/16, >90% recovery, <7 steps, <3 errors) is closest to being hit

If you've run 5 experiments with no improvement, STOP parameter tuning and make a structural change. Read harness.py end-to-end looking for architectural oversights — missing mechanisms, redundant steps, implicit assumptions that could be wrong.

## Workflow

1. Read harness.py and evaluate.py to understand the current system
2. Think about what ONE focused change could improve the composite score
3. Modify harness.py with that change
4. Run: `python evaluate.py`
5. Record the composite_score
6. If improved (>0.01 gain): `git add -A && git commit -m "Experiment: [description] score=[result]"`
7. If worse or marginal: `git checkout harness.py` to revert
8. After every 10 experiments, review results.tsv and write a brief analysis to `notes.md` — what's working, what's not, what to try next
9. Repeat

## What You Can Change in harness.py

ANYTHING in harness.py is fair game:

### Planning & Execution
- ReAct loop structure (current baseline is simple loop)
- Add planning step before execution
- Add reflection/critique after tool results
- Tree-of-thought or graph-based planning
- Sub-goal decomposition

### Prompting
- System prompt template
- Tool descriptions and formatting
- Few-shot examples
- Chain-of-thought instructions
- Output format (TOOL/PARAMS/ANSWER parsing)

### Memory System
- Episode storage strategy
- Fact compression/summarization
- Context window management
- Memory retrieval strategy
- Working memory vs long-term memory

### Tool Integration
- Error handling and retry logic
- Tool result formatting
- Sandboxing improvements
- New tool implementations (within sandbox)

### Inference Parameters
- Temperature, top_p, repetition_penalty
- Max tokens per call
- Number of retries on failure

### Architecture
- Self-verification steps
- Critic/validator passes
- Multi-turn reflection
- Backtracking on failures

## Constraints

- Must use Ollama with local model (qwen3.5:9b default)
- Must complete all 25 benchmarks per evaluation run
- Each evaluation should complete in under 45 minutes
- All file operations must stay in sandbox/ directory
- Do not modify evaluate.py or the benchmarks

## Strategy Tips

- Prompt engineering is DONE. Don't go back to it.
- Look for architectural oversights — missing verification steps, no retry logic, no planning phase. These are the "forgotten regularization" equivalents that Karpathy's agent found.
- Each structural change should target a specific metric (success rate, recovery rate, step efficiency, error count).
- Test one change at a time. Don't combine multiple changes (hard to attribute gains).
- If a structural change hurts score but the IDEA is sound, consider the implementation was wrong, not the idea. Try a different implementation before discarding the concept.
- Read notes.md before each experiment to avoid repeating failed approaches.
- **Favor low-latency designs.** Overhead per step matters — complex scaffolding that adds 2 seconds per step kills efficiency on 25 tasks.
- **After a keep, verify on a quick subset of 5 diverse benchmarks** to confirm transferability before the full 3-run validation. This mirrors Karpathy's approach of verifying small-model findings transfer to larger models.

## Results Logging

After each experiment, append a line to results.tsv:
```
commit\tcomposite_score\tstatus\tdescription
```

Example:
```
abc1234\t0.4500\tkeep\tadd few-shot examples for tool calling
def5678\t0.4200\tdiscard\tincrease temperature to 0.9 (worse)
```
