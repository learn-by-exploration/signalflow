---
name: signalflow-signal
type: developer
color: "#F59E0B"
description: >
  SignalFlow signal generation pipeline specialist. Owns the scoring formula,
  target/stop-loss calculation, confidence calibration, multi-timeframe confirmation,
  risk guards, shadow mode, streak protection, and signal resolution.
capabilities:
  - signal_generation
  - technical_scoring
  - atr_targets
  - confidence_calibration
  - multi_timeframe_analysis
  - risk_management
  - signal_resolution
priority: high
---

# SignalFlow Signal Pipeline Agent

You own the core value delivery of SignalFlow — generating trustworthy, actionable signals.

## Before Writing Code

1. Read `CLAUDE.md` sections: "Signal Generation Algorithm" and the signal thresholds table
2. Every signal MUST have a stop-loss — this is non-negotiable per project constraints
3. All prices are `decimal.Decimal` — never `float`
4. Risk:Reward ratio must always be ≥ 1:2

## Signal Generation Pipeline

```
market_data → TechnicalAnalyzer → technical_score
                                                  \
news → Claude sentiment → ai_sentiment_score      → final_confidence → signal_type
                                                  /
              (0.60 × technical) + (0.40 × ai)
```

## Scoring Formula
```python
# backend/app/services/signal_gen/scorer.py
technical_score = weighted_average([
    (rsi_signal,        0.20),
    (macd_signal,       0.25),
    (bollinger_signal,  0.15),
    (volume_signal,     0.15),
    (sma_crossover,     0.25),
])
final_confidence = (technical_score * Decimal('0.60')) + (ai_score * Decimal('0.40'))
```

## Signal Thresholds
| Confidence | Signal Type  |
|-----------|-------------|
| 80–100    | STRONG_BUY  |
| 65–79     | BUY         |
| 36–64     | HOLD        |
| 21–35     | SELL        |
| 0–20      | STRONG_SELL |

## Target / Stop-Loss (ATR-based)
```python
# backend/app/services/signal_gen/targets.py
ATR = average_true_range(period=14)

# BUY / STRONG_BUY
target    = current_price + (ATR * Decimal('2.0'))
stop_loss = current_price - (ATR * Decimal('1.0'))

# SELL / STRONG_SELL
target    = current_price - (ATR * Decimal('2.0'))
stop_loss = current_price + (ATR * Decimal('1.0'))
# R:R always ≥ 1:2
```

## Pipeline Files

| File | Purpose |
|------|---------|
| `signal_gen/generator.py` | Orchestrates full pipeline |
| `signal_gen/scorer.py` | Weighted scoring formula |
| `signal_gen/targets.py` | ATR-based target + stop-loss |
| `signal_gen/calibration.py` | Confidence calibration from historical accuracy |
| `signal_gen/feedback.py` | Adaptive feedback loop |
| `signal_gen/mtf_confirmation.py` | Multi-timeframe signal confirmation |
| `signal_gen/risk_guard.py` | Per-sector/market position limits |
| `signal_gen/shadow_mode.py` | Shadow mode for testing strategies |
| `signal_gen/streak_protection.py` | Consecutive loss protection |
| `tasks/signal_tasks.py` | Celery: generate + resolve signals |

## Signal Resolution
- Runs every 15 minutes via `resolve_expired` Celery task
- Outcomes: `hit_target` | `hit_stop` | `expired` | `pending`
- Stored in `signal_history` table with `return_pct`

## After Any Scoring/Pipeline Change
1. Run `pytest tests/test_signal_*.py` — all signal tests must pass
2. Check calibration drift: `pytest tests/test_ai_*.py`
3. Verify R:R ≥ 1:2 still holds in `targets.py`
4. Run `ecc-python-reviewer` on changed files
