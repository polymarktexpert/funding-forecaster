# Funding-Rate Forecaster (Polymarket Perps)

CLI tool that estimates the **funding-rate drag** on a leveraged Polymarket
Perps position before you open it. Read-only: pulls the perp book and the
underlying market price from Polymarket's public APIs, computes the premium,
projects hourly funding against your margin.

**No wallet. No keys. No sign-in.** It only ever reads public endpoints.

## Why

At 20x leverage, funding — not the directional call — kills most perp
positions held through an event weekend. A 0.01%/hour drag at 20x is
~4.8% of margin per day. This tool answers "what does holding this cost
me per hour?" in seconds.

## Install

```bash
git clone https://github.com/polymarktexpert/funding-forecaster.git
cd funding-forecaster
python3 funding_forecaster.py --help
```

Python 3.10+, standard library only.

## Usage

```bash
python3 funding_forecaster.py \
  --market will-the-fed-cut-rates-in-december \
  --side long --leverage 5 --hours 24 --margin 500
```

Output:

```
Market       : Will the Fed cut rates in December?
Premium est. : +0.420%  (perp vs underlying mid)
Funding rate : 0.420% per hour (cap 4%)
Side         : LONG @ 5x → you pay
Drag         : 2.10% of margin/hour
Projection   : 50.40% over 24h ≈ $252.00 on $500 margin
```

## How the math works

- Premium = perp midpoint − underlying outcome price (both public).
- Funding rate = |premium|, clipped at the 4% hourly cap.
- Leverage multiplies the drag: a 5x long pays 5x the hourly rate.
- Longs pay when the perp trades above the underlying; shorts pay below.

Full write-up with worked examples:
- [Funding cost forecaster: full arithmetic + worked examples](https://brainresearchhub.net/research/perps/funding-cost-forecaster)
**[Funding rate mechanics — BrainResearchHub](https://brainresearchhub.net/research/perps/polymarket-perps-funding-rate)**

Related research from the same author:
- [Liquidation mechanics](https://brainresearchhub.net/research/perps/polymarket-perps-liquidation)
- [Margin modes: cross vs isolated](https://brainresearchhub.net/research/perps/polymarket-leverage-guide)

## Limitations

- Uses the current spread as a **static estimate**; live funding spikes
  during news windows can exceed it.
- Thin books produce noisy midpoints — treat sub-tick outputs as ranges.

## License

MIT — use it, fork it, cite it.

*Educational tool. Not financial advice. Not affiliated with Polymarket.*
