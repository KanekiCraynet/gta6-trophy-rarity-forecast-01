"""Improved forecaster for gta6-trophy-rarity-forecast-01.

Features over baseline:
- Estimates logit trend (growth rate) from history via linear regression
- Tier-specific sigma (platinum/gold/silver/bronze, secret vs non-secret)
- Shrinkage toward tier-level prior for low-data trophies
- Proper 0.01..99.99 clamping with half-up rounding to 4 decimals
"""

import json
import math
import os
import sys
from pathlib import Path
from collections import defaultdict

# Grader's -P leaves /bot off sys.path: put it back first.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

# Tier-specific sigma (logit units per sqrt-day)
# Calibrated: platinum/gold more stable, bronze more volatile, secret extra volatile
SIGMA_BY_TIER = {
    ("platinum", False): 0.30,
    ("gold", False): 0.35,
    ("silver", False): 0.40,
    ("bronze", False): 0.50,
    ("platinum", True): 0.35,
    ("gold", True): 0.40,
    ("silver", True): 0.45,
    ("bronze", True): 0.60,
}

# Prior mean rates by tier (percent) - used for shrinkage when history is flat
PRIOR_BY_TIER = {
    ("platinum", False): 0.5,
    ("gold", False): 1.0,
    ("silver", False): 2.0,
    ("bronze", False): 1.5,
    ("platinum", True): 0.5,
    ("gold", True): 1.0,
    ("silver", True): 2.0,
    ("bronze", True): 1.5,
}

# Shrinkage strength: how many pseudo-observations the prior counts as
SHRINKAGE_N = 3.0


def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    p = clamp(pct)
    return math.log(p / (100 - p))


def inv_logit(l: float) -> float:
    return 100 / (1 + math.exp(-l))


def round4(x: float) -> float | int:
    """Round to 4 decimals, half up. Whole numbers returned as int."""
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value.is_integer() else value


def estimate_trend_and_rate(history: list, trophy_idx: int) -> tuple[float, float]:
    """Estimate current rate (percent) and logit trend (per day) from history.

    Returns (current_rate, trend_per_day) where trend_per_day is in logit units/day.
    """
    rates = [h["rates"][trophy_idx] for h in history if h["rates"][trophy_idx] is not None]
    times = []
    for h in history:
        if h["rates"][trophy_idx] is not None:
            # Convert ISO timestamp to fractional days since first read
            from datetime import datetime
            dt = datetime.fromisoformat(h["at"].replace("Z", "+00:00"))
            times.append(dt)

    if len(rates) < 2:
        return rates[-1] if rates else 0.0, 0.0

    # Use first timestamp as reference
    t0 = times[0]
    x = [(t - t0).total_seconds() / 86400.0 for t in times]  # days
    y = [logit(r) for r in rates]

    # Simple linear regression: y = a + b*x
    n = len(x)
    sx = sum(x)
    sy = sum(y)
    sxx = sum(xi * xi for xi in x)
    sxy = sum(xi * yi for xi, yi in zip(x, y))

    denom = n * sxx - sx * sx
    if denom == 0:
        return rates[-1], 0.0

    b = (n * sxy - sx * sy) / denom  # slope (logit per day)
    a = (sy - b * sx) / n  # intercept

    # Current rate = last observed (more robust than model prediction at endpoint)
    current_rate = rates[-1]
    trend_per_day = b
    return current_rate, trend_per_day


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    if not case["history"]:
        raise ValueError(f"{name} has no history")

    last = case["history"][-1]
    horizon_days = case["horizon_minutes"] / 1440.0

    # Build tier-level prior from this case's trophies
    tier_rates = defaultdict(list)
    for i, trophy in enumerate(case["trophies"]):
        rate = last["rates"][i]
        if rate is not None:
            key = (trophy["tier"], trophy["secret"])
            tier_rates[key].append(rate)

    tier_prior = {}
    for key, rates in tier_rates.items():
        tier_prior[key] = sum(rates) / len(rates)

    rows = []
    for i, trophy in enumerate(case["trophies"]):
        tier_key = (trophy["tier"], trophy["secret"])
        sigma = SIGMA_BY_TIER.get(tier_key, 0.5)

        # Estimate trend from history
        current_rate, trend = estimate_trend_and_rate(case["history"], i)

        # Shrinkage toward tier prior (if history is flat/short)
        if current_rate is not None:
            prior_rate = tier_prior.get(tier_key, PRIOR_BY_TIER.get(tier_key, 1.0))
            # Weight: more history observations = less shrinkage
            n_obs = sum(1 for h in case["history"] if h["rates"][i] is not None)
            weight = n_obs / (n_obs + SHRINKAGE_N)
            shrunk_rate = weight * current_rate + (1 - weight) * prior_rate
        else:
            shrunk_rate = tier_prior.get(tier_key, PRIOR_BY_TIER.get(tier_key, 1.0))

        # Project forward: logit(rate) + trend * horizon_days
        lg = logit(shrunk_rate) + trend * horizon_days

        # Spread widens with sqrt(horizon_days)
        spread = sigma * math.sqrt(horizon_days)

        qs = [round4(inv_logit(lg + z * spread)) for z in Z]
        rows.append({"id": trophy["id"], "q": qs})

    return {"trophies": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()