# Agent Harness Research

Autonomous experimentation framework for optimizing local AI agent capabilities.
Same philosophy as Karpathy's autoresearch: one file, one metric, autonomous iteration.

## Goal
Discover the most reliable, capable local agent harness possible on consumer hardware (RTX 5070, 12GB VRAM). Everything runs locally, no cloud dependencies.

## Structure
- `harness.py` — the agent scaffold (AGENT MODIFIES THIS)
- `evaluate.py` — benchmark runner (FIXED, do not modify)
- `benchmarks/` — task definitions (FIXED, do not modify)
- `program.md` — agent instructions
- `results.tsv` — experiment log
- `tools/` — sandboxed tool implementations

## Hardware
- NVIDIA RTX 5070, 12GB VRAM
- Ryzen 9 3950X, 48GB RAM
- Local inference via Ollama (qwen3.5:9b)
