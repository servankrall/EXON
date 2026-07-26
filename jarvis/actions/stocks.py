"""
Hisse senedi / endeks fiyati — Yahoo Finance (anahtarsiz), Stooq yedek.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Sembol ornekleri: AAPL, TSLA, MSFT (ABD); THYAO.IS, ASELS.IS (BIST);
^GSPC (S&P500); BTC-USD (kripto). BIST icin '.IS' ekini kullan.
"""

from __future__ import annotations

import requests


_HEADERS = {"User-Agent": "Mozilla/5.0 (EXON-Robotik)"}

# Sik kullanilan kisa adlar -> sembol
_ALIASES = {
    "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT", "google": "GOOGL",
    "amazon": "AMZN", "nvidia": "NVDA", "meta": "META", "netflix": "NFLX",
    "thy": "THYAO.IS", "türk hava yollari": "THYAO.IS", "turk hava yollari": "THYAO.IS",
    "aselsan": "ASELS.IS", "bist": "XU100.IS", "bist100": "XU100.IS",
    "sp500": "^GSPC", "s&p500": "^GSPC", "nasdaq": "^IXIC", "dow": "^DJI",
}


def _resolve(symbol: str) -> str:
    s = (symbol or "").strip()
    return _ALIASES.get(s.lower(), s).upper() if s.lower() in _ALIASES else s


def _yahoo(symbol: str) -> str | None:
    try:
        res = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        result = (((res.json().get("chart") or {}).get("result")) or [{}])[0]
        meta = result.get("meta") or {}
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        cur = meta.get("currency") or ""
        sym = meta.get("symbol") or symbol
        if price is None:
            return None
        line = f"{sym}: {price:g} {cur}".strip()
        if prev:
            change = price - prev
            pct = (change / prev) * 100 if prev else 0
            arrow = "▲" if change >= 0 else "▼"
            line += f"  ({arrow} {change:+.2f} / {pct:+.2f}%)"
        return line
    except Exception:
        return None


def _stooq(symbol: str) -> str | None:
    try:
        s = symbol.lower()
        if "." not in s and not s.startswith("^"):
            s = s + ".us"
        res = requests.get(
            "https://stooq.com/q/l/",
            params={"s": s, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        rows = res.text.strip().splitlines()
        if len(rows) < 2:
            return None
        cols = rows[1].split(",")
        # Symbol,Date,Time,Open,High,Low,Close,Volume
        if len(cols) >= 7 and cols[6] not in ("N/D", ""):
            return f"{cols[0].upper()}: {cols[6]} (kapanis)"
        return None
    except Exception:
        return None


def get_stock_price(symbol: str) -> str:
    """Verilen hisse/endeks/kripto sembolunun guncel fiyatini dondurur."""
    symbol = _resolve(symbol)
    if not symbol:
        return "Hangi hisseyi/sembolu istedigini belirt (orn. AAPL, THYAO.IS)."
    out = _yahoo(symbol) or _stooq(symbol)
    if out:
        return out
    return (f"'{symbol}' icin fiyat alinamadi. Sembolu kontrol et "
            "(ABD: AAPL, BIST: THYAO.IS, endeks: ^GSPC, kripto: BTC-USD).")
