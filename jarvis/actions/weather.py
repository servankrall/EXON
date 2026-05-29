"""
Hava durumu ozeti + otomatik konum tespiti.
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Konum oncelik sirasi:
1. Cagriya verilen 'location' parametresi
2. EXON_WEATHER_LOCATION ortam degiskeni
3. IP tabanli otomatik konum tespiti (ip-api.com)
4. Hicbiri yoksa Istanbul
"""

from __future__ import annotations

import os
import threading

import requests


# IP tabanli konum tespiti tekrar tekrar cagrilmasin diye onbellege alinir.
_AUTO_LOCATION_CACHE: dict | None = None
_AUTO_LOCATION_LOCK = threading.Lock()


def detect_location(force: bool = False) -> dict:
    """
    Kullanicinin yaklasik konumunu IP adresi uzerinden tespit eder.
    Donen sozluk: {city, region, country, lat, lon, source}
    Hata olursa Istanbul'a duser.
    """
    global _AUTO_LOCATION_CACHE
    with _AUTO_LOCATION_LOCK:
        if _AUTO_LOCATION_CACHE is not None and not force:
            return _AUTO_LOCATION_CACHE

    fallback = {
        "city": "Istanbul", "region": "", "country": "Türkiye",
        "lat": None, "lon": None, "source": "fallback",
    }

    try:
        # ip-api.com ucretsiz ve anahtar gerektirmez (http).
        res = requests.get(
            "http://ip-api.com/json/",
            params={"fields": "status,city,regionName,country,lat,lon", "lang": "tr"},
            timeout=6,
        )
        data = res.json()
        if data.get("status") == "success" and data.get("city"):
            location = {
                "city": data.get("city") or "Istanbul",
                "region": data.get("regionName") or "",
                "country": data.get("country") or "",
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "source": "ip-api",
            }
        else:
            location = fallback
    except Exception:
        location = fallback

    with _AUTO_LOCATION_LOCK:
        _AUTO_LOCATION_CACHE = location
    return location


def get_auto_location_city() -> str:
    """Sadece sehir adini dondurur (UI etiketleri icin)."""
    return detect_location().get("city", "Istanbul")


def _resolve_target(location: str | None) -> str:
    if location and location.strip():
        return location.strip()
    env_loc = os.environ.get("EXON_WEATHER_LOCATION") or os.environ.get("JARVIS_WEATHER_LOCATION")
    if env_loc and env_loc.strip():
        return env_loc.strip()
    return get_auto_location_city()


def get_weather_summary(location: str | None = None) -> str:
    target = _resolve_target(location)
    try:
        response = requests.get(
            f"https://wttr.in/{target}",
            params={"format": "j1"},
            timeout=10,
            headers={"User-Agent": "EXON Windows"},
        )
        response.raise_for_status()
        payload = response.json()
        current = (payload.get("current_condition") or [{}])[0]
        temp_c = current.get("temp_C")
        feels_like = current.get("FeelsLikeC")
        weather_desc = ((current.get("weatherDesc") or [{}])[0]).get("value", "")
        humidity = current.get("humidity")
        wind = current.get("windspeedKmph")

        parts = []
        if temp_c:
            parts.append(f"{temp_c} derece")
        if weather_desc:
            parts.append(weather_desc.lower())
        if feels_like and feels_like != temp_c:
            parts.append(f"hissedilen {feels_like} derece")
        if humidity:
            parts.append(f"nem yüzde {humidity}")
        if wind:
            parts.append(f"rüzgar {wind} km/s")

        if not parts:
            return "Hava durumu bilgisi şu anda alınamadı."

        return f"{target} için hava durumu: " + ", ".join(parts) + "."
    except Exception:
        return "Hava durumu bilgisi şu anda alınamadı."
