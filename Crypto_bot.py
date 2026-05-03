“””
crypto_bot.py — fetches prices from CoinGecko and pushes to Telegram.
Run directly or via cron / GitHub Actions (see README).
“””

import os
import sys
import datetime
import requests

# ── Config ────────────────────────────────────────────────────────────────────

from tokens import TOKENS

TELEGRAM_BOT_TOKEN = os.environ.get(“TELEGRAM_BOT_TOKEN”, “”)
TELEGRAM_CHAT_ID   = os.environ.get(“TELEGRAM_CHAT_ID”, “”)

COINGECKO_BASE = “https://api.coingecko.com/api/v3”

# CoinGecko free tier: 30 calls/min — one batched call is plenty.

# ──────────────────────────────────────────────────────────────────────────────

def fetch_prices(token_ids: list[str]) -> dict:
“””
Fetch current price, 24 h change, and market data for all tokens in one call.
Returns a dict keyed by coingecko_id.
“””
ids = “,”.join(token_ids)
url = f”{COINGECKO_BASE}/coins/markets”
params = {
“vs_currency”: “usd”,
“ids”: ids,
“price_change_percentage”: “24h,30d,1y”,
“sparkline”: “false”,
“per_page”: 250,
“page”: 1,
}
resp = requests.get(url, params=params, timeout=15)
resp.raise_for_status()
return {coin[“id”]: coin for coin in resp.json()}

def fetch_ytd_change(coingecko_id: str, current_price: float) -> float | None:
“””
Fetch price on Jan 1 of the current year and compute YTD % change.
Uses CoinGecko /coins/{id}/history endpoint.
“””
year = datetime.date.today().year
jan1 = f”01-01-{year}”
url = f”{COINGECKO_BASE}/coins/{coingecko_id}/history”
try:
resp = requests.get(url, params={“date”: jan1, “localization”: “false”}, timeout=15)
resp.raise_for_status()
data = resp.json()
jan1_price = data[“market_data”][“current_price”][“usd”]
return (current_price - jan1_price) / jan1_price * 100
except Exception:
return None

def fmt_price(price: float) -> str:
if price >= 1_000:
return f”${price:,.2f}”
if price >= 1:
return f”${price:.4f}”
return f”${price:.6f}”

def fmt_pct(pct: float | None) -> str:
if pct is None:
return “n/a”
sign = “+” if pct >= 0 else “”
return f”{sign}{pct:.1f}%”

def equity_valuation(price: float, formula_cfg: dict) -> str:
“”“Evaluate the equity valuation formula and return a formatted string.”””
# Only one formula supported for now; extend here if needed.
value = price / 0.2 * 1000          # price / 20% float * 1 000 tokens (in $m)
return f”{value:,.0f} {formula_cfg[‘unit’]}”

def build_message(market_data: dict, ytd_data: dict) -> str:
now = datetime.datetime.utcnow().strftime(”%Y-%m-%d %H:%M UTC”)
lines = [f”📊 *Crypto Update* — {now}\n”]

```
for token in TOKENS:
    cid = token["coingecko_id"]
    coin = market_data.get(cid)
    if coin is None:
        lines.append(f"⚠️ {token['display_name']} — data unavailable\n")
        continue

    price    = coin.get("current_price", 0)
    chg_24h  = coin.get("price_change_percentage_24h_in_currency")
    chg_30d  = coin.get("price_change_percentage_30d_in_currency")
    chg_ytd  = ytd_data.get(cid)

    name_line = f"*{token['display_name']}* ({token['ticker']})"
    price_line = f"  Price:  {fmt_price(price)}"
    chg_line   = (
        f"  24h:   {fmt_pct(chg_24h)}"
        f"  |  1M: {fmt_pct(chg_30d)}"
        f"  |  YTD: {fmt_pct(chg_ytd)}"
    )

    lines.append(name_line)
    lines.append(price_line)
    lines.append(chg_line)

    # Optional equity valuation block
    ev_cfg = token.get("equity_valuation")
    if ev_cfg:
        ev_str = equity_valuation(price, ev_cfg)
        lines.append(f"  {ev_cfg['label']}: {ev_str}")

    lines.append("")          # blank line between tokens

return "\n".join(lines)
```

def send_telegram(message: str) -> None:
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
raise EnvironmentError(
“TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set “
“(env vars or .env file).”
)
url = f”https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage”
payload = {
“chat_id”: TELEGRAM_CHAT_ID,
“text”: message,
“parse_mode”: “Markdown”,
}
resp = requests.post(url, json=payload, timeout=15)
resp.raise_for_status()
print(f”✅ Message sent ({resp.status_code})”)

def main() -> None:
token_ids = [t[“coingecko_id”] for t in TOKENS]

```
print("Fetching market data …")
market_data = fetch_prices(token_ids)

print("Fetching YTD prices …")
ytd_data = {}
for token in TOKENS:
    cid = token["coingecko_id"]
    price = market_data.get(cid, {}).get("current_price", 0)
    ytd_data[cid] = fetch_ytd_change(cid, price)

message = build_message(market_data, ytd_data)
print("\n--- Message preview ---")
print(message)
print("-----------------------\n")

send_telegram(message)
```

if **name** == “**main**”:
main()
