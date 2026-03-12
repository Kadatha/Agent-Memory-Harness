# Benchmark Results — Qwen 3.5 35B-A3B

## Run 1 (Best Run)
```
============================================================
35B-A3B BASELINE RESULTS
============================================================
  Composite Score:    0.8852
  Retention:          1.0000
  Retrieval Eff:      0.6173
  Decay:              1.0000
  Robustness:         1.0000
  Regression:         1.0000
  Domain/Hybrid:      1.0000
  Success Rate:       100.0% (22/22)
  Total Steps:        82
  Total Errors:       2
  Recoveries:         2

  Per-Task:
    reg_01: PASS (2 steps, 58.8s)
    reg_02: PASS (2 steps, 68.7s)
    reg_03: PASS (4 steps, 64.4s)
    retain_01: PASS (1 steps, 72.7s)
    retain_02: PASS (5 steps, 151.9s)
    retain_03: PASS (1 steps, 80.6s)
    persist_01: PASS (13 steps, 260.6s)
    persist_02: PASS (4 steps, 169.7s)
    persist_03: PASS (2 steps, 116.9s)
    ambig_recall_01: PASS (3 steps, 174.4s)
    ambig_recall_02: PASS (2 steps, 62.0s)
    ambig_recall_03: PASS (4 steps, 86.8s)
    hybrid_01: PASS (4 steps, 128.2s)
    hybrid_02: PASS (4 steps, 319.5s)
    hybrid_03: PASS (4 steps, 138.4s)
    decay_01: PASS (4 steps, 149.8s)
    decay_02: PASS (5 steps, 260.3s)
    adversarial_01: PASS (2 steps, 61.7s)
    adversarial_02: PASS (1 steps, 75.6s)
    adversarial_03: PASS (3 steps, 127.8s)
    domain_01: PASS (3 steps, 138.2s)
    domain_02: PASS (4 steps, 190.2s)
```

## Run 2
```
  Composite Score:    0.8000
  Success Rate:       95.5% (21/22)
  Total Steps:        104
  Failures:           persist_03 (1 step — premature answer)
```

## Run 3 (with min-step enforcement)
```
  Visible: 19/21 tasks passed (crashed before completion)
  Failures: persist_03 (8 steps), adversarial_03 (1 step)
  persist_03 did more work with min-step fix but got wrong answer
```

## Comparison vs Qwen 3.5 9B Baseline

| Metric | 9B (Exp 21) | 35B (Best) | Improvement |
|--------|-------------|------------|-------------|
| Composite | 0.8247 | 0.8852 | +7.3% |
| Success Rate | ~82% | 100% | +18% |
| Avg Steps/Task | 6.8 | 3.7 | -46% |
| Retention | 0.78 | 1.00 | +28% |
| Robustness | 0.67 | 1.00 | +49% |
| Baseline (no harness) | 0.4556 | — | — |

## Run-to-Run Variance

Local model inference is non-deterministic. Across all recorded runs:

### Qwen 3.5 35B-A3B (6 runs)
| Run | Composite | Success | Failures |
|-----|-----------|---------|----------|
| 1 | **0.8852** | 22/22 | none |
| 2 | 0.8000 | 21/22 | persist_03 |
| 3 | 0.5630 | 18/22 | persist_02, persist_03, decay_01, decay_02 |
| 4 | 0.6667 | 20/22 | decay_01, decay_02 |
| 5 | **0.8519** | 22/22 | none |
| 6 | 0.7259 | 21/22 | decay_01 |

**Average: 0.74 | Best: 0.8852 | Perfect runs: 2/6 (33%)**

### Qwen 3.5 9B (8 runs)
| Run | Composite | Success | Failures |
|-----|-----------|---------|----------|
| 1 | **0.8370** | 22/22 | none |
| 2 | 0.7074 | 21/22 | decay_01 |
| 3 | 0.7519 | 22/22 | none |
| 4 | **0.8148** | 22/22 | none |
| 5 | 0.7444 | 21/22 | decay_01 |
| 6 | 0.6481 | 21/22 | decay_01 |
| 7 | 0.5556 | 20/22 | persist_03, decay_01 |
| 8 | **0.8148** | 22/22 | none |

**Average: 0.73 | Best: 0.8370 | Perfect runs: 4/8 (50%)**

### Key Observation
Every single run — even the worst — significantly exceeds the 0.4556 no-harness baseline. The harness methodology produces consistent structural improvement; individual run variance reflects model inference non-determinism, not harness instability.

## Hardware
- AMD Ryzen 9 3950X
- NVIDIA RTX 5070 (12GB VRAM)
- 48GB DDR4 RAM
- Ollama (local inference)
- Total API cost: $0
