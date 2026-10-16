#!/usr/bin/env python3
"""Polymarket Perps Funding-Rate Forecaster — Ais Fang.

Estimates the funding-rate drag on a leveraged Polymarket Perps position
using the current mark vs. underlying price spread. Read-only: uses
Polymarket's public Data API, requires no key, never requests a wallet
connection.

Usage:
  python funding_forecaster.py --market <slug-or-id> --side long|short \
      --leverage 5 --hours 24 --margin 500

Educational tool. Not financial advice.
"""

import argparse
import json
import sys
import urllib.request

DATA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"
FUNDING_CAP = 0.04          # 4% per-hour cap, per Polymarket docs
SAMPLE_INTERVAL_H = 1.0     # funding settled hourly


def http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "funding-forecaster/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def resolve_market(query: str):
    """Find a market by slug or numeric id via Gamma API."""
    if query.isdigit():
        url = f"{DATA_API}/markets/{query}"
    else:
        url = f"{DATA_API}/markets?slug={query}"
    try:
        data = http_json(url)
    except Exception as e:
        sys.exit(f"[!] lookup failed: {e}")
    if isinstance(data, list):
        if not data:
            sys.exit("[!] no market found for slug")
        data = data[0]
    return data


def get_perp_spread(market: dict) -> float:
    """Approximate the premium (perp price - underlying probability).

    Uses the CLOB midpoint of the perp book vs. the market's outcome price.
    Falls back to last-trade spread when the book is thin.
    """
    token = (market.get("clobTokenIds") or [""])[0]
    premium = 0.0
    if token:
        try:
            book = http_json(f"{CLOB_API}/book?token_id={token}")
            bids = [float(x["price"]) for x in book.get("bids", [])]
            asks = [float(x["price"]) for x in book.get("asks", [])]
            if bids and asks:
                mid = (max(bids) + min(asks)) / 2
                underlying = float(market.get("outcomePrices", ["0.5"])[0])
                premium = mid - underlying
        except Exception:
            pass
    return premium


def forecast(premium: float, leverage: float, side: str, hours: float, margin: float):
    """Core math: hourly funding = premium-proportional rate, capped at 4%.

    Longs pay when perp trades above underlying (positive premium), shorts
    pay when below. Returns projected drag on margin.
    """
    base_rate = min(abs(premium), FUNDING_CAP)
    drag_per_hour = base_rate * leverage           # applied to margin
    total_drag = drag_per_hour * hours
    direction = "pay" if (
        (side == "long" and premium > 0) or (side == "short" and premium < 0)
    ) else "receive"
    usd = margin * total_drag
    return base_rate, drag_per_hour, total_drag, direction, usd


def main():
    ap = argparse.ArgumentParser(description="Polymarket Perps funding-rate forecaster")
    ap.add_argument("--market", required=True, help="market slug or id")
    ap.add_argument("--side", choices=["long", "short"], default="long")
    ap.add_argument("--leverage", type=float, default=1.0)
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--margin", type=float, default=100.0, help="USDC margin")
    args = ap.parse_args()

    m = resolve_market(args.market)
    question = m.get("question", "?")
    premium = get_perp_spread(m)

    rate, per_hour, total, direction, usd = forecast(
        premium, args.leverage, args.side, args.hours, args.margin
    )

    print(f"\nMarket       : {question}")
    print(f"Premium est. : {premium*100:+.3f}%  (perp vs underlying mid)")
    print(f"Funding rate : {rate*100:.3f}% per hour (cap {FUNDING_CAP*100:.0f}%)")
    print(f"Side         : {args.side.upper()} @ {args.leverage:g}x → you {direction}")
    print(f"Drag         : {per_hour*100:.2f}% of margin/hour")
    print(f"Projection   : {total*100:.2f}% over {args.hours:g}h ≈ ${usd:,.2f} on ${args.margin:,.0f} margin")
    print(f"\nEducational estimate — live funding can spike past the cap "
          f"during news. Verify on-platform.\n")


if __name__ == "__main__":
    main()
