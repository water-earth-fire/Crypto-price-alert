“””
Token configuration file.
Edit this file to add, remove, or update tokens.

Each entry in TOKENS is a dict with:

- coingecko_id: the CoinGecko API identifier (https://www.coingecko.com/en/api/documentation)
- display_name: how it appears in the Telegram message
- ticker: short symbol shown in parentheses
- equity_valuation: (optional) if True, calculate implied 100% equity valuation
  using: price / equity_pct * total_supply_units
  Set equity_pct and total_supply_units accordingly.
  “””

TOKENS = [
{
“coingecko_id”: “bitcoin”,
“display_name”: “Bitcoin”,
“ticker”: “BTC”,
},
{
“coingecko_id”: “ethereum”,
“display_name”: “Ethereum”,
“ticker”: “ETH”,
},
{
“coingecko_id”: “solana”,
“display_name”: “Solana”,
“ticker”: “SOL”,
},
{
“coingecko_id”: “ripple”,
“display_name”: “XRP”,
“ticker”: “XRP”,
},
{
“coingecko_id”: “binancecoin”,
“display_name”: “Binance Coin”,
“ticker”: “BNB”,
},
{
“coingecko_id”: “backpack-exchange”,
“display_name”: “Backpack”,
“ticker”: “BP”,
# Implied 100% equity valuation:
# price / 0.2 * 1000  →  displayed in $m
“equity_valuation”: {
“formula”: “price / 0.2 * 1000”,
“label”: “Impl. 100% EV”,
“unit”: “$m”,
},
},
]
