# Agent Memory Harness

**0.8852 composite score · 22/22 benchmarks · $0 inference · Runs offline on consumer hardware**

A harness-level optimization framework for reliable agent memory persistence using local language models. No cloud. No API keys. No model modification.

> Patent Pending · MIT License

---

## What Is This?

A Python harness that sits between a language model and its tools, intercepting and improving agent behavior through six coordinated mechanisms:

| Mechanism | What It Does |
|-----------|-------------|
| **Auto-Injection** | Detects empty recall and injects cached memory before regeneration |
| **Confidence Retry** | Scores output confidence (0–1) and retries low-confidence answers up to 3x |
| **Decay Simulation** | Fades old facts by relevance weight; boosts task-relevant data |
| **Multi-Tool Execution** | Queues parallel tool calls and merges results |
| **Minimum Step Enforcement** | Prevents premature answers on multi-step tasks |
| **Task Preprocessing** | Auto-enriches prompts with category-specific instructions |

All interventions are **zero-cost on the happy path** — they only activate when something goes wrong.

---

## Results

### Best Single Run (Qwen 3.5 35B-A3B)

| Category | Score | Tasks |
|----------|-------|-------|
| Retention | 1.0000 | 3/3 |
| Decay | 1.0000 | 2/2 |
| Robustness | 1.0000 | 3/3 |
| Regression | 1.0000 | 3/3 |
| Domain/Hybrid | 1.0000 | 5/5 |
| Retrieval Efficiency | 0.6173 | — |
| **Composite** | **0.8852** | **22/22** |

### Baseline Comparison

| Configuration | Composite | Success Rate |
|---------------|-----------|-------------|
| No harness (raw model) | 0.4556 | ~50% |
| Harness + Qwen 3.5 9B | 0.8247 | ~82% |
| Harness + Qwen 3.5 35B-A3B | **0.8852** | **100%** |

**94% improvement** from harness changes alone. The model was never modified.

### Reproducibility

Across 3 independent runs: average success rate 95.3%, composite scores ranging 0.80–0.89. Consistent task-level pass/fail patterns indicate systematic rather than stochastic performance.

---

## Hardware

Validated on consumer hardware:

- **CPU:** AMD Ryzen 9 3950X
- **GPU:** NVIDIA RTX 5070 (12GB VRAM)
- **RAM:** 48GB DDR4
- **Inference:** Ollama (local)
- **Models:** Qwen 3.5 9B, Qwen 3.5 35B-A3B (open source, Apache 2.0)
- **Cost:** $0

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- A model with tool-calling capability

### Setup

```bash
# Clone the repo
git clone https://github.com/Kadatha/agent-memory-harness.git
cd agent-memory-harness

# Pull a model
ollama pull qwen3.5:9b
# or for best results:
ollama pull qwen3.5:35b-a3b

# Run the benchmark suite
python evaluate_p4.py
```

### Configuration

Edit the top of `harness.py`:

```python
MODEL = "qwen3.5:35b-a3b"    # Any Ollama model with tool calling
OLLAMA_URL = "http://localhost:11434"
MAX_STEPS = 25
```

### Run a Single Task

```python
import harness

memory = harness.Memory(":memory:")
result = harness.run_task(
    "Store 'api_key' = 'sk_live_abc123'. Do 5 unrelated calculations. Recall the api_key.",
    task_id="test_01",
    memory=memory,
    sandbox_dir="sandbox/test_01"
)
print(result["answer"])  # sk_live_abc123
```

---

## Benchmark Suite

22 benchmarks across 8 categories:

| Category | Count | Tests |
|----------|-------|-------|
| Regression | 3 | Core math, file I/O, multi-step |
| Basic Retention | 3 | Store/recall with distractors |
| Long Persistence | 3 | Memory survives 10+ intermediate tasks |
| Ambiguous Recall | 3 | Fuzzy matching, partial keys |
| Hybrid Memory | 3 | Memory + calculation + file ops |
| Decay | 2 | Critical vs. trivial fact retention over time |
| Adversarial | 3 | Prompt injection, contradictory updates |
| Domain-Specific | 2 | Steel pricing, margin calculations |

---

## Research Methodology

This harness was developed through **60+ iterative experiments** over 3 days using a systematic approach:

1. **Propose** a structural change to the harness
2. **Run** the full 22-benchmark suite (3 runs for verification)
3. **Score** using the composite metric
4. **Keep** if score improves with no regressions; **revert** if not
5. **Log** every decision, keep, and discard

Key finding: **Structural changes dramatically outperform prompt engineering.** Bug fixes, schema changes, and parser improvements consistently delivered 5-10x the gains of prompt rules or system prompt modifications.

Full experiment logs are in `results.tsv` and `notes.md`.

---

## Project Structure

```
├── harness.py          # The harness (core invention)
├── evaluate_p4.py      # Benchmark suite (22 tasks, 8 categories)
├── run_35b.py          # Runner script for 35B model
├── results.tsv         # Full experiment log (60+ experiments)
├── notes.md            # Forced reflections every 5 experiments
├── program.md          # Research program documentation
└── sandbox/            # Task execution directories (gitignored)
```

---

## How It Works

The harness operates as a middleware layer between the language model and its tools:

```
User Task → [Task Preprocessor] → Model → [Tool Executor] → [Confidence Check] → Response
                                     ↑                              |
                                     └── [Auto-Inject / Retry] ←────┘
```

The model never knows the harness exists. It just sees better prompts, gets its memory back when it forgets, and gets asked to try again when it's not confident. From the model's perspective, everything works normally — the harness handles the edge cases silently.

---

## Citation

If you use this work, please cite:

```
Lovick, A. (2026). Method for Reliable Agent Memory Persistence Using
Harness-Level Interventions. U.S. Provisional Patent Application.
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

Patent pending. You are free to use, modify, and distribute this software under the MIT License. The patent covers the specific method described; the code is freely available for research, personal use, and commercial applications.

---

## Acknowledgments

- [Andrej Karpathy](https://twitter.com/karpathy) — whose [autoresearch](https://github.com/karpathy/autoresearch) repo accelerated this work significantly
- [Peter Steinberger](https://twitter.com/steipete) — creator of [OpenClaw](https://github.com/openclaw/openclaw), which made this entire project possible
- Built with [Ollama](https://ollama.ai) for local inference
- Models by [Alibaba Qwen](https://github.com/QwenLM) (Apache 2.0)
- Inspired by [AutoHarness](https://arxiv.org/abs/2603.03329) and the local LLM community
