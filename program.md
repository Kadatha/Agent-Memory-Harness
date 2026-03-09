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

## High-Priority Research Directions

Try these categories roughly in order (biggest expected gains first):

1. **Prompt engineering** — Few-shot examples for tool-call formatting, chain-of-thought instructions. Small models benefit enormously from clear examples.
2. **Self-reflection loops** — After tool results, add a "verify this result" step. Catch errors before they cascade.
3. **Retry logic & error handling** — Automatic retry on tool failure with reformulated input. Free points on error recovery benchmarks.
4. **Planning decomposition** — Before executing, have the agent break the task into numbered sub-goals. Reduces derailment on multi-step tasks.
5. **Multi-agent coordination** — Separate planner/executor/critic roles (can be same model, different system prompts). Debate/reflection cycles.
6. **Memory optimization** — Summarize long conversation histories to stay within context window. Compress episodic memory into working memory.
7. **Inference parameters** — Temperature, top_p, repetition penalty sweeps. Low-hanging fruit.

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
- Must complete all 16 benchmarks per evaluation run
- Each evaluation should complete in under 30 minutes
- All file operations must stay in sandbox/ directory
- Do not modify evaluate.py or the benchmarks

## Strategy Tips

- Start with the lowest-hanging fruit (prompt engineering often gives big gains)
- Tool-use reliability is usually the biggest bottleneck for small models
- Few-shot examples in the system prompt can dramatically improve tool-call formatting
- Error recovery is free points — adding retry logic is almost always worth it
- Step efficiency matters — if the agent solves tasks in fewer steps, score goes up
- Test one change at a time. Don't combine multiple changes (hard to attribute gains)

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
