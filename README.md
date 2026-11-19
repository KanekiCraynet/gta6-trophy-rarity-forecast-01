# gta6-trophy-rarity-forecast-01

Forecasting bot for GTA VI trophy rarity on Exophase (make.fun competition).

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/KanekiCraynet/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/KanekiCraynet/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Built for [make.fun](https://make.fun/bounty/gta6-trophy-rarity-forecast-01) "Forecast how many GTA VI players earn each trophy in week one" bounty ($250 USDC).

## Model
- Logit-space random walk with trend estimation from historical rates
- Tier-specific volatility (platinum/gold/silver/bronze, secret vs non-secret)
- Shrinkage toward tier-level priors for low-data trophies
- 5 quantiles (0.05, 0.25, 0.5, 0.75, 0.95) per trophy

## Run locally
```bash
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Files
- `main.py` - Python 3.13 entry point (stdlib only)
- `main.ts` - TypeScript reference (not used)
