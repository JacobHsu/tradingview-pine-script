"""
1H Williams Fractals detector for BTC / ETH (Binance) and
XAUT / SLVX / USOX / EWJX / EWYX (Pionex), matching jacobhsu/crypto-watch.

Mirrors Williams-Fractals.pine (n=2):
  upFractal at bar k <=> high[k] > high[k-2], high[k-1], high[k+1], high[k+2]
  dnFractal at bar k <=> low[k]  < low[k-2],  low[k-1],  low[k+1],  low[k+2]

For each symbol: prints current price + most recent confirmed fractal pivot.
Console gets ANSI-colored output. Telegram receives plain text when
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

sys.stdout.reconfigure(encoding="utf-8")

TAIPEI = ZoneInfo("Asia/Taipei")
LIMIT = 100
FOOTER_LINK = "https://jacobhsu.github.io/crypto-watch/eth"

# (display, source, market_symbol)
SYMBOLS: list[tuple[str, str, str]] = [
    ("BTCUSDT", "binance", "BTCUSDT"),
    ("ETHUSDT", "binance", "ETHUSDT"),
    ("XAUT", "pionex", "XAUT_USDT"),
    ("SLVX", "pionex", "SLVX_USDT_PERP"),
    ("USOX", "pionex", "USOX_USDT_PERP"),
    ("EWJX", "pionex", "EWJX_USDT_PERP"),
    ("EWYX", "pionex", "EWYX_USDT_PERP"),
]

# Normalized bar: (open_time_ms, high, low, close), oldest -> newest.
Bar = tuple[int, float, float, float]


def fetch_binance(symbol: str) -> list[Bar]:
    r = requests.get(
        "https://api.binance.com/api/v3/klines",
        params={"symbol": symbol, "interval": "1h", "limit": LIMIT},
        timeout=15,
    )
    r.raise_for_status()
    return [(int(k[0]), float(k[2]), float(k[3]), float(k[4])) for k in r.json()]


def fetch_pionex(symbol: str) -> list[Bar]:
    r = requests.get(
        "https://api.pionex.com/api/v1/market/klines",
        params={"symbol": symbol, "interval": "60M", "limit": LIMIT},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()
    if not payload.get("result"):
        raise RuntimeError(f"pionex error for {symbol}: {payload}")
    bars = list(reversed(payload["data"]["klines"]))
    return [
        (int(b["time"]), float(b["high"]), float(b["low"]), float(b["close"]))
        for b in bars
    ]


FETCHERS = {"binance": fetch_binance, "pionex": fetch_pionex}


def is_up_fractal(highs: list[float], k: int) -> bool:
    return (
        highs[k] > highs[k - 2]
        and highs[k] > highs[k - 1]
        and highs[k] > highs[k + 1]
        and highs[k] > highs[k + 2]
    )


def is_down_fractal(lows: list[float], k: int) -> bool:
    return (
        lows[k] < lows[k - 2]
        and lows[k] < lows[k - 1]
        and lows[k] < lows[k + 1]
        and lows[k] < lows[k + 2]
    )


def fmt_hm(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=TAIPEI).strftime("%H:%M")


def report_line(display: str, bars: list[Bar]) -> str | None:
    """Return a plain-text line for the symbol; None if not enough bars."""
    if len(bars) < 5:
        return None
    highs = [b[1] for b in bars]
    lows = [b[2] for b in bars]
    last_close = bars[-1][3]
    price_str = f"${last_close:,.0f}"
    prefix = f"{display:8s} {price_str:>8s}"

    for i in range(len(bars) - 3, 1, -1):
        if is_up_fractal(highs, i):
            return f"{prefix}  ▲  {fmt_hm(bars[i][0])}  High ${highs[i]:,.0f}"
        if is_down_fractal(lows, i):
            return f"{prefix}  ▼  {fmt_hm(bars[i][0])}  Low  ${lows[i]:,.0f}"
    return f"{prefix}  -  no fractal in scan window"


def colorize(line: str) -> str:
    return line.replace("▲", "\033[32m▲\033[0m").replace("▼", "\033[31m▼\033[0m")


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TG env not set; skip send", file=sys.stderr)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
    r.raise_for_status()


def main() -> int:
    fetched: list[tuple[str, list[Bar]]] = []
    for display, source, market_symbol in SYMBOLS:
        try:
            fetched.append((display, FETCHERS[source](market_symbol)))
        except Exception as e:
            print(f"{display}: fetch failed - {e}", file=sys.stderr)

    now_ts = datetime.now(TAIPEI).strftime("%Y-%m-%d %H:%M")
    header = f"🕐 {now_ts} (台北時間)"
    title = "【 Williams Fractals 】"

    rows = [line for display, bars in fetched if (line := report_line(display, bars))]

    tg_text = "\n".join([header, "", title, "", *rows, "", FOOTER_LINK])

    # Console: colored
    print(header)
    print()
    print(title)
    print()
    for r in rows:
        print(colorize(r))
    print()
    print(FOOTER_LINK)

    send_telegram(tg_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
