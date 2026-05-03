import os
import datetime
import requests
from tokens import TOKENS

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def fetch_prices(token_ids):
    ids = ",".join(token_ids)
    url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids,
        "price_change_percentage": "24h,30d,1y",
        "sparkline": "false",
        "per_page": 250,
        "page": 1,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return {coin["id"]: coin for coin in resp.json()}


def fetch_ytd_change(coingecko_id, current_price):
    year = datetime.date.today().year
    jan1 = f"01-01-{year}"
    url = f"{COINGECKO_BASE}/coins/{coingecko_id}/history"
    try:
        resp = requests.get(url, params={"date": jan1, "localization": "false"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jan1_price = data["market_data"]["current_price"]["usd"]
        return (current_price - jan1_price) / jan1_price * 100
    except Exception:
        return None


def fmt_price(price):
    if price >= 1000:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:.4f}"
    return f"${price:.6f}"


def fmt_pct(pct):
    if pct is None:
        return "n/a"
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def equity_valuation(price, formula_cfg):
    value = price / 0.2 * 1000
    return f"{value:,.0f} {formula_cfg['unit']}"


def build_message(market_data, ytd_data):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Crypto Update - {now}\n"]

    for token in TOKENS:
        cid = token["coingecko_id"]
        coin = market_data.get(cid)
        if coin is None:
            lines.append(f"[!] {token['display_name']} - data unavailable\n")
            continue

        price = coin.get("current_price", 0)
        chg_24h = coin.get("price_change_percentage_24h_in_currency")
        chg_30d = coin.get("price_change_percentage_30d_in_currency")
        chg_ytd = ytd_data.get(cid)

        lines.append(f"{token['display_name']} ({token['ticker']})")
        lines.append(f"  Price:  {fmt_price(price)}")
        lines.append(f"  24h: {fmt_pct(chg_24h)}  |  1M: {fmt_pct(chg_30d)}  |  YTD: {fmt_pct(chg_ytd)}")

        ev_cfg = token.get("equity_valuation")
        if ev_cfg:
            ev_str = equity_valuation(price, ev_cfg)
            lines.append(f"  {ev_cfg['label']}: {ev_str}")

        lines.append("")

    return "\n".join(lines)


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    print(f"Message sent ({resp.status_code})")


def main():
    token_ids = [t["coingecko_id"] for t in TOKENS]

    print("Fetching market data...")
    market_data = fetch_prices(token_ids)

    print("Fetching YTD prices...")
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


if __name__ == "__main__":
    main()
