"""
Doviz / kripto fiyat ve cevirme araci.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- Fiat para birimleri (USD, EUR, TRY, GBP ...): Frankfurter API (ucretsiz, anahtarsiz)
- Kripto (BTC, ETH, SOL ...): CoinGecko API (ucretsiz, anahtarsiz)
Ikisi de internet ister; anahtar gerektirmez.
"""

from __future__ import annotations

import requests


_HEADERS = {"User-Agent": "EXON-Robotik/1.0"}

# Sik kullanilan kripto sembolleri -> CoinGecko kimligi
_CRYPTO_IDS = {
    "BTC": "bitcoin", "XBT": "bitcoin",
    "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
    "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
    "AVAX": "avalanche-2", "DOT": "polkadot", "TRX": "tron",
    "LTC": "litecoin", "MATIC": "matic-network", "SHIB": "shiba-inu",
    "USDT": "tether", "USDC": "usd-coin", "TON": "the-open-network",
}

_FIAT = {"USD", "EUR", "TRY", "GBP", "JPY", "CHF", "CAD", "AUD", "RUB",
         "CNY", "SEK", "NOK", "DKK", "PLN", "AED", "SAR"}

_SYMBOLS = {"USD": "$", "EUR": "€", "TRY": "₺", "GBP": "£"}


def _norm(cur: str) -> str:
    return (cur or "").strip().upper().replace("TL", "TRY")


def _crypto_price(crypto: str, fiat: str) -> float | None:
    coin_id = _CRYPTO_IDS.get(crypto)
    if not coin_id:
        return None
    try:
        res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin_id, "vs_currencies": fiat.lower()},
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        return (res.json().get(coin_id, {}) or {}).get(fiat.lower())
    except Exception:
        return None


def _fiat_rate(from_cur: str, to_cur: str) -> float | None:
    if from_cur == to_cur:
        return 1.0
    try:
        res = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": from_cur, "to": to_cur},
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        return (res.json().get("rates", {}) or {}).get(to_cur)
    except Exception:
        return None


def _fmt(value: float) -> str:
    if value >= 100:
        return f"{value:,.2f}"
    if value >= 1:
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return f"{value:.6f}".rstrip("0").rstrip(".")


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """amount kadar from_currency'yi to_currency'ye cevirir.
    Fiat<->fiat, kripto->fiat ve fiat->kripto desteklenir."""
    try:
        amount = float(amount) if amount not in (None, "") else 1.0
    except (TypeError, ValueError):
        amount = 1.0
    src = _norm(from_currency)
    dst = _norm(to_currency) or "TRY"
    if not src:
        return "Hangi para biriminden cevirecegimi belirt (orn. USD, BTC)."

    src_is_crypto = src in _CRYPTO_IDS
    dst_is_crypto = dst in _CRYPTO_IDS

    unit = None
    # kripto -> fiat
    if src_is_crypto and not dst_is_crypto:
        unit = _crypto_price(src, dst if dst in _FIAT else "USD")
        if dst not in _FIAT and unit is not None:
            return (f"{src} fiyati: {_fmt(unit)} USD "
                    f"(istenen {dst} birimi desteklenmiyor, USD verildi).")
    # fiat -> kripto
    elif dst_is_crypto and not src_is_crypto:
        base = src if src in _FIAT else "USD"
        coin_in_fiat = _crypto_price(dst, base)
        if coin_in_fiat:
            unit = 1.0 / coin_in_fiat
    # fiat -> fiat
    elif not src_is_crypto and not dst_is_crypto:
        unit = _fiat_rate(src, dst)
    # kripto -> kripto
    else:
        a_usd = _crypto_price(src, "usd")
        b_usd = _crypto_price(dst, "usd")
        if a_usd and b_usd:
            unit = a_usd / b_usd

    if unit is None:
        return (f"{src} -> {dst} kuru su an alinamadi. "
                "Para birimi kodlarini kontrol et (orn. USD, EUR, TRY, BTC).")

    total = amount * unit
    sym = _SYMBOLS.get(dst, "")
    return (f"{_fmt(amount)} {src} = {_fmt(total)} {sym}{dst} "
            f"(1 {src} = {_fmt(unit)} {dst}).")
