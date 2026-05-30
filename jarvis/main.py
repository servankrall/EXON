#!/usr/bin/env python3
"""
EXON Windows — Gerçek zamanlı sesli yardımcı çekirdeği
Servan Kanğal tarafından yapılmıştır
Windows ortamına uyarlanmış çalışma akışı
"""

import sys
import multiprocessing

# PyInstaller .exe'lerde, alt-surec/ pencere acan herhangi bir cagri YENIDEN
# tum main.py'yi calistirip SONSUZ pencere acabilir (fork bomb). freeze_support()
# bunu engeller ve bir alt-surec olarak baslatildiysak burada durdurur.
# Tum agir import'lardan ve kod calismasindan ONCE cagrilmali.
if __name__ == "__main__":
    multiprocessing.freeze_support()

import asyncio
import datetime
import threading
import traceback
import os
import re
import time
import array
import math
import urllib.parse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# DONMUS (PyInstaller .exe) modda sys.executable = EXON.exe'dir. Bu modda
# subprocess.run([sys.executable, ...]) cagrisi YENI bir EXON penceresi acar
# ve sonsuz dongu (fork bomb) olusur. Bu yuzden exe modunda kendini-cagiran
# tum islemler (paket kurma, alt-surec testi) DEVRE DISIDIR.
_FROZEN = bool(getattr(sys, "frozen", False))


def _ensure_packages():
    """Eksik 3. parti paketleri ayni Python yorumlayicisina otomatik kurar.
    SADECE normal (script) calismada; exe modunda paketler zaten gomulu."""
    if _FROZEN:
        return
    required = {
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "google.genai": "google-genai",
        "psutil": "psutil",
        "PIL": "Pillow",
        "pygame": "pygame",
        "pyttsx3": "pyttsx3",
        "pyperclip": "pyperclip",
        "pyautogui": "pyautogui",
        "pygetwindow": "pygetwindow",
    }
    def _installed(mod: str) -> bool:
        # find_spec namespace/alt-modullerde istisna firlatabilir; en saglami
        # dogrudan import denemek.
        try:
            __import__(mod)
            return True
        except Exception:
            return False

    missing = [pip_name for mod, pip_name in required.items() if not _installed(mod)]
    if not missing:
        return
    print("\n" + "=" * 60)
    print("  EXON ilk kurulum: eksik paketler yukleniyor...")
    print("  (" + ", ".join(missing) + ")")
    print("  Bu yalnizca ILK acilista olur, birkac dakika surebilir.")
    print("=" * 60 + "\n")
    # pip yoksa once ensurepip ile pip'i kur (Python ile gomulu gelir).
    if not _installed("pip"):
        print("  pip bulunamadi, Python icine gomulu ensurepip ile kuruluyor...")
        try:
            subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"])
        except Exception:
            pass
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([sys.executable, "-m", "pip", "install", *missing])
    # pywin32 (win32gui vb.) ayri ad; Windows'ta dene
    if os.name == "nt":
        try:
            import importlib.util as _u
            if _u.find_spec("win32gui") is None:
                subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"])
        except Exception:
            pass


_ensure_packages()


def _preflight_native():
    """Native (C) moduller bazi bozuk/uyumsuz kurulumlarda import sirasinda
    0xC0000005 ile COKER. AYRI surecte test edip isaretleriz.
    SADECE normal modda; exe modunda kendini cagirmak fork bomb olusturur."""
    if _FROZEN:
        return
    try:
        r = subprocess.run([sys.executable, "-c", "import pygame"],
                           capture_output=True, timeout=30)
        if r.returncode != 0:
            os.environ["EXON_NO_PYGAME"] = "1"
            print(f"[EXON] 'pygame' bu sistemde sorunlu (kod {r.returncode}); "
                  "ses efektleri devre disi, EXON yine aciliyor.")
    except Exception:
        os.environ["EXON_NO_PYGAME"] = "1"


_preflight_native()

import requests
from bs4 import BeautifulSoup

try:
    import pyaudio  # type: ignore[reportMissingModuleSource]
except ImportError:
    pyaudio = None
    if _FROZEN:
        # exe modunda kendini cagirmak fork bomb olusturur; sessizce gec.
        print("[EXON] PyAudio yok; mikrofon devre disi (exe modu).")
    else:
        print("\n" + "="*60)
        print("  HATA: PyAudio modulu bulunamadi!")
        print("  Cozum - CMD'de su komutu calistirin:")
        print("    pip install pipwin")
        print("    pipwin install pyaudio")
        print("  Veya: setup.bat dosyasini tekrar calistirin.")
        print("="*60 + "\n")
        # Otomatik kurulum dene
        print("  Otomatik kurulum deneniyor...")
        r1 = subprocess.run([sys.executable, "-m", "pip", "install", "PyAudio", "--quiet"],
                            capture_output=True)
        try:
            import pyaudio  # type: ignore[reportMissingModuleSource]
            print("  PyAudio kuruldu ve yuklendi!\n")
        except ImportError:
            r2 = subprocess.run([sys.executable, "-m", "pip", "install", "pipwin", "--quiet"],
                                capture_output=True)
            r3 = subprocess.run([sys.executable, "-m", "pipwin", "install", "pyaudio"],
                                capture_output=True)
            try:
                import pyaudio  # type: ignore[reportMissingModuleSource]
                print("  PyAudio kuruldu (pipwin)!\n")
            except ImportError:
                print("  Otomatik kurulum basarisiz.")
                pyaudio = None
from google import genai  # type: ignore[reportMissingImports]
from google.genai import types  # type: ignore[reportMissingImports]

from app_config import get_app_config_value

# tkinter (arayüz) kontrolü — pip ile KURULMAZ; Python kurulumunun parçasıdır.
try:
    import tkinter  # noqa: F401
except ModuleNotFoundError:
    print("\n" + "=" * 64)
    print("  HATA: 'tkinter' bulunamadi (Python'a tcl/tk eklenmemis).")
    print("  tkinter pip ile KURULMAZ; Python kurulumuyla birlikte gelir.")
    print("")
    print("  COZUM (Windows):")
    print("   1) Ayarlar > Uygulamalar > Yuklu uygulamalar > 'Python 3.x'")
    print("   2) ... (uc nokta) > Degistir / Modify")
    print("   3) 'tcl/tk and IDLE' kutusunu ISARETLE > Modify")
    print("   (veya python.org'dan tekrar kur; kurulumda ayni kutuyu isaretle)")
    print("=" * 64 + "\n")
    try:
        input("  Cikmak icin ENTER'a bas...")
    except Exception:
        pass
    raise SystemExit(1)

from ui import ExonUI
from memory.memory_manager import load_memory, update_memory, delete_memory, format_memory_for_prompt
from actions.open_app import open_app
from actions.sys_info  import sys_info
from actions.calendar import get_calendar_events, add_calendar_event, delete_calendar_event
from actions.reminders import get_reminders, add_reminder
from actions.browser   import browser_control
from actions.shell     import shell_run
from actions.whatsapp  import send_whatsapp_message, save_whatsapp_contact
from actions.media     import play_media
from actions.weather   import get_weather_summary
from actions.screen_vision import analyze_screen, analyze_image_file
from actions.image_gen import generate_image
from actions.youtube_stats import get_youtube_channel_report
from actions.wiki import get_wikipedia_summary
from actions.finance import convert_currency
from actions.translate import translate_text
from actions.file_search import find_file
from actions.email_tool import read_recent_emails, send_email
from actions.app_control import close_app, close_opened_apps
from actions.window_control import close_browser_tab
from actions.system_power import set_performance_mode, power_action
from actions.controls import set_volume, take_screenshot
from actions.songwriter import compose_song
from actions.news import get_news_briefing
from actions.stocks import get_stock_price
from actions.code_assistant import (read_code_file, list_code_files,
                                    search_in_code, write_code_file)
from actions.studio import compose_text, summarize_url, summarize_document
from actions.license_manager import is_pro as _is_pro, PRO_TOOLS
from actions.wake_word import WakeWordListener
from actions.scheduler import TaskScheduler
from actions.face_auth import FaceAuth
from bot_bridge import TelegramBridge, DiscordBridge

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"

CONTROL_TOKEN_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

# ── Model ───────────────────────────────────────────────────────────────────
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-latest"

# ── Audio ───────────────────────────────────────────────────────────────────
FORMAT           = pyaudio.paInt16 if pyaudio is not None else 8
CHANNELS         = 1
SEND_SAMPLE_RATE = 16000
RECV_SAMPLE_RATE = 24000
CHUNK_SIZE       = 1024
if pyaudio is None:
    pya = None
else:
    try:
        pya = pyaudio.PyAudio()
    except Exception as _audio_exc:
        print(f"[EXON] Ses aygiti baslatilamadi (mikrofon olmadan devam): {_audio_exc}")
        pya = None

# ── Web Araştırma Motoru ─────────────────────────────────────────────────────
_SEARCH_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

# Rate-limit'i aşmak için döndürülen User-Agent havuzu
_SEARCH_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Web arama önbelleği: aynı sorgu kısa sürede tekrar gelirse internete çıkma.
_SEARCH_CACHE: dict[str, tuple[float, str]] = {}
_SEARCH_CACHE_TTL = 180.0
_SEARCH_CACHE_LOCK = threading.Lock()


def _audio_rms(data: bytes) -> float:
    """16-bit PCM ses parçasının ortalama ses şiddetini (RMS) hesaplar.
    Barge-in (kullanıcı araya girince EXON'un susması) için kullanılır."""
    try:
        samples = array.array("h")
        samples.frombytes(data)
        if not samples:
            return 0.0
        return math.sqrt(sum(s * s for s in samples) / len(samples))
    except Exception:
        return 0.0


# Türkçe karakterleri ASCII'ye indirger (Kanğal -> Kangal). Her iki yazımı da aramak için.
_TR_MAP = str.maketrans({
    "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
    "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
})


def _ascii_fold(text: str) -> str:
    return (text or "").translate(_TR_MAP)


def _decode_ddg_href(href: str) -> str:
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if "uddg=" in href:
        try:
            enc = href.split("uddg=", 1)[1].split("&", 1)[0]
            return urllib.parse.unquote(enc)
        except Exception:
            return href
    return href


def _search_duckduckgo(query: str, tries: int = 3) -> list[tuple[str, str, str]]:
    """DuckDuckGo 'lite' — (başlık, url, snippet). Rate-limit'e karşı tekrar dener,
    her denemede farklı User-Agent kullanır ve Türkiye bölgesini (kl=tr-tr) seçer."""
    for attempt in range(tries):
        headers = {
            "User-Agent": _SEARCH_UAS[attempt % len(_SEARCH_UAS)],
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        }
        try:
            res = requests.post("https://lite.duckduckgo.com/lite/",
                                data={"q": query, "kl": "tr-tr"},
                                headers=headers, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                links = soup.select("a.result-link")
                snippets = soup.select("td.result-snippet")
                out: list[tuple[str, str, str]] = []
                for i, a in enumerate(links[:8]):
                    title = a.get_text(" ", strip=True)
                    url = _decode_ddg_href(a.get("href", ""))
                    snippet = snippets[i].get_text(" ", strip=True) if i < len(snippets) else ""
                    if title and url.startswith("http"):
                        out.append((title, url, snippet))
                if out:
                    return out
        except Exception:
            pass
        # Boş döndüyse (rate-limit) bekle ve farklı UA ile tekrar dene
        if attempt < tries - 1:
            time.sleep(0.8)
    return []


def _search_google(query: str) -> list[tuple[str, str, str]]:
    """Yedek: Google HTML kazıma (sık sık engellenir)."""
    results: list[tuple[str, str, str]] = []
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        res = requests.get(url, headers=_SEARCH_HEADERS, timeout=8)
        if res.status_code != 200:
            return results
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "url?q=" in href and "webcache" not in href:
                target = urllib.parse.unquote(href.split("url?q=")[1].split("&")[0])
                if target.startswith("http"):
                    results.append((a.get_text(" ", strip=True)[:120] or target, target, ""))
    except Exception:
        pass
    return results


def _search_mojeek(query: str) -> list[tuple[str, str, str]]:
    """Mojeek — bağımsız (kendi indeksli) arama motoru. Kapsamı genişletmek için."""
    results: list[tuple[str, str, str]] = []
    try:
        res = requests.get("https://www.mojeek.com/search",
                           params={"q": query}, headers=_SEARCH_HEADERS, timeout=10)
        if res.status_code != 200:
            return results
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.select("a.title")[:8]:
            title = a.get_text(" ", strip=True)
            url = a.get("href", "")
            li = a.find_parent("li")
            sn = li.select_one("p.s") if li else None
            snippet = sn.get_text(" ", strip=True) if sn else ""
            if title and url.startswith("http"):
                results.append((title, url, snippet))
    except Exception:
        pass
    return results


def perform_web_scrape_search(query: str) -> str:
    """Tüm web genelinde (Google'a denk Bing indeksi dahil) PARALEL arama yapar.
    Birden çok motoru (DuckDuckGo + Mojeek) ve hem Türkçe karakterli hem karaktersiz
    yazımı (Kanğal + Kangal) AYNI ANDA sorgular, tekrarları ayıklar; ardından ilk
    sayfaların içeriğini de AYNI ANDA okur. Böylece araştırma kat kat hızlanır.
    Kişi/şirket/güncel bilgi aramaları için."""
    query = (query or "").strip()
    if not query:
        return "Arama sorgusu boş."

    # Önbellek: aynı sorgu son 3 dakikada arandıysa anında döndür (çok daha hızlı).
    cache_key = query.lower()
    with _SEARCH_CACHE_LOCK:
        hit = _SEARCH_CACHE.get(cache_key)
        if hit and (time.time() - hit[0]) < _SEARCH_CACHE_TTL:
            return hit[1]

    # Hem orijinal hem ASCII'ye indirgenmiş yazımı ara (farklı sonuçlar getirir).
    query_variants = [query]
    folded = _ascii_fold(query)
    if folded != query:
        query_variants.append(folded)

    aggregated: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def _merge(items: list[tuple[str, str, str]]) -> None:
        for title, url, snippet in items or []:
            key = url.split("#")[0].rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            aggregated.append((title, url, snippet))

    # 1) Birincil motorları AYNI ANDA çalıştır (DuckDuckGo + Mojeek, tüm yazımlar).
    #    Paralel olduğu için toplam süre, motorları tek tek beklemek yerine yalnızca
    #    en yavaş motor kadar sürer. Mojeek de artık her zaman taranır → daha geniş kapsam.
    primary_jobs = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for q in query_variants:
            primary_jobs.append(pool.submit(_search_duckduckgo, q))
        for q in query_variants:
            primary_jobs.append(pool.submit(_search_mojeek, q))
        for job in primary_jobs:
            try:
                _merge(job.result())
            except Exception:
                pass

    # 2) Hiç sonuç yoksa Google yedeğine düş (yine paralel).
    if not aggregated:
        with ThreadPoolExecutor(max_workers=2) as pool:
            for job in [pool.submit(_search_google, q) for q in query_variants]:
                try:
                    _merge(job.result())
                except Exception:
                    pass

    if not aggregated:
        return ("Arama sonucu bulunamadı. Sorguyu farklı kelimelerle veya ek "
                "ipuçlarıyla (şehir, kurum, meslek) tekrar dene.")

    # 1) Özet: başlık + snippet (sayfa açılamasa bile genelde soruyu yanıtlar)
    summary_lines = []
    for i, (title, url, snippet) in enumerate(aggregated[:10], 1):
        line = f"{i}. {title}"
        if snippet:
            line += f" — {snippet}"
        line += f"  ({url})"
        summary_lines.append(line)
    summary = ("ARAMA SONUÇLARI (birden çok arama motoru, "
               f"{len(aggregated)} sonuç):\n" + "\n".join(summary_lines))

    # 2) İlk 4 sayfayı AYNI ANDA (paralel) derinlemesine oku — sıralı okumaya göre
    #    ~4 kat daha hızlı; tek bir yavaş sayfa diğerlerini bekletmez.
    def _read_page(item: tuple[str, str, str]) -> str | None:
        _title, url, _snippet = item
        try:
            page_res = requests.get(url, headers=_SEARCH_HEADERS, timeout=7)
            if page_res.status_code != 200:
                return None
            page_soup = BeautifulSoup(page_res.text, "html.parser")
            for element in page_soup(["script", "style", "nav", "footer",
                                      "header", "noscript", "aside", "form"]):
                element.decompose()
            text = " ".join(page_soup.get_text(separator=" ").split())[:2000]
            return f"[Kaynak: {url}]\n{text}" if text else None
        except Exception:
            return None

    page_blocks: list[str] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for block in pool.map(_read_page, aggregated[:4]):
            if block:
                page_blocks.append(block)

    parts = [summary]
    if page_blocks:
        parts.append("SAYFA İÇERİKLERİ:\n" + "\n\n---\n\n".join(page_blocks))
    final = "\n\n".join(parts)
    with _SEARCH_CACHE_LOCK:
        _SEARCH_CACHE[cache_key] = (time.time(), final)
    return final

# ── Tool tanımları ──────────────────────────────────────────────────────────
TOOL_DECLARATIONS = [
    {
        "name": "deep_web_search",
        "description": (
            "İnternette birden fazla kaynaktan derinlemesine arama yapar ve okur. "
            "Bir KİŞİYİ (ünlü olmasa, sıradan/yerel biri olsa bile), şirketi, ürünü, "
            "güncel olayı veya herhangi bir bilgiyi araştırmak için kullan. Kişi ararken "
            "ismi, kullanıcının verdiği ipuçlarıyla (şehir, meslek, sendika, kurum) birlikte sorgula."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "İnternette aranacak detaylı arama sorgusu"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_image",
        "description": (
            "Metin açıklamasından yeni bir görsel/resim oluşturur (Gemini/Imagen). "
            "Kullanıcı 'görsel oluştur', 'resim çiz', 'logo tasarla', 'proje çizimi/tasarımı yap', "
            "'konsept/şema çiz', 'şunun resmini yap' gibi bir şey istediğinde HEMEN kullan. "
            "Oluşan görsel otomatik kaydedilir ve ekranda gösterilir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "prompt": {
                    "type": "STRING",
                    "description": "Oluşturulacak görselin detaylı açıklaması (İngilizce daha iyi sonuç verir)."
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "add_scheduled_task",
        "description": (
            "Zamanlanmış/tekrarlayan görev oluşturur. Kullanıcı 'her sabah 8'de hava durumu söyle', "
            "'her gün 22:00 hatırlat' gibi bir şey istediğinde kullan. Vakti gelince EXON verilen "
            "istemi otomatik, sesli olarak yerine getirir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "time":   {"type": "STRING", "description": "Saat (24s), örn. '08:00'."},
                "prompt": {"type": "STRING", "description": "Vakti gelince EXON'a verilecek istem, örn. 'Bana güncel hava durumunu söyle'."},
                "repeat": {"type": "STRING", "description": "daily | once | weekdays. Varsayılan daily."}
            },
            "required": ["time", "prompt"]
        }
    },
    {
        "name": "list_scheduled_tasks",
        "description": "Tüm zamanlanmış görevleri listeler.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "remove_scheduled_task",
        "description": "Bir zamanlanmış görevi siler (görev id'si veya istemdeki bir kelime ile).",
        "parameters": {
            "type": "OBJECT",
            "properties": {"identifier": {"type": "STRING", "description": "Görev id'si veya istemden bir kelime"}},
            "required": ["identifier"]
        }
    },
    {
        "name": "recognize_face",
        "description": (
            "Web kamerasını açıp karşıdaki kişiyi yüz tanıma ile tanır. Kullanıcı 'beni tanı', "
            "'yüz tanıma yap', 'kameradan giriş', 'kim olduğumu bul' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "open_app",
        "description": "Windows'ta herhangi bir uygulamayı açar. Spotify, Chrome, CMD, VS Code, Discord vb.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Uygulama adı (örn. 'Spotify', 'Chrome', 'CMD', 'Discord')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "sys_info",
        "description": "Sistem bilgisi alır: pil durumu, CPU, RAM, disk, saat, tarih, ağ bağlantısı.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "battery | cpu | ram | disk | time | date | network | all"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_weather",
        "description": (
            "Anlık hava durumunu özetler. Konum boş bırakılırsa kullanıcının IP tabanlı "
            "otomatik konumu kullanılır. Kullanıcı hava durumunu, sıcaklığı veya yağmur "
            "durumunu sorduğunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "location": {
                    "type": "STRING",
                    "description": "Şehir veya konum. Boş bırakılırsa otomatik konum kullanılır."
                }
            }
        }
    },
    {
        "name": "get_calendar_events",
        "description": (
            "Yerel takvimi okur (JSON tabanlı, Windows uyumlu). "
            "Bugün, yarın, sıradaki etkinlik veya yaklaşan ajandayı özetler. "
            "Kullanıcı toplantı, takvim, ajanda, etkinlik veya günlük programını sorduğunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "today | tomorrow | next | agenda | week veya doğal dilde "
                        "'önümüzdeki 30 gün', '2 hafta', 'bu ay', 'gelecek ay'"
                    )
                },
                "limit": {
                    "type": "NUMBER",
                    "description": "Maksimum etkinlik sayısı"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_calendar_event",
        "description": (
            "Yerel takvime yeni etkinlik ekler (JSON tabanlı, Windows uyumlu). "
            "Kullanıcı toplantı, randevu, takvime ekleme veya etkinlik oluşturma isterse kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title":         {"type": "STRING", "description": "Etkinlik başlığı"},
                "start_iso":     {"type": "STRING", "description": "Başlangıç ISO tarihi (YYYY-MM-DDTHH:MM)"},
                "end_iso":       {"type": "STRING", "description": "Bitiş ISO tarihi. Opsiyonel."},
                "location":      {"type": "STRING", "description": "Etkinlik konumu. Opsiyonel."},
                "notes":         {"type": "STRING", "description": "Etkinlik notları. Opsiyonel."},
                "calendar_name": {"type": "STRING", "description": "Takvim adı. Opsiyonel."},
                "all_day":       {"type": "BOOLEAN", "description": "true ise tüm gün etkinliği."}
            },
            "required": ["title", "start_iso"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": (
            "Yerel takvimden etkinlik siler. "
            "Kullanıcı bir toplantıyı, randevuyu veya takvim kaydını silmek istediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title":              {"type": "STRING",  "description": "Silinecek etkinlik başlığı"},
                "start_iso":          {"type": "STRING",  "description": "Opsiyonel tarih/saat"},
                "calendar_name":      {"type": "STRING",  "description": "Opsiyonel takvim adı"},
                "delete_all_matches": {"type": "BOOLEAN", "description": "true ise tüm eşleşenleri siler"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_reminders",
        "description": (
            "Yerel hatırlatıcı listesini okur (JSON tabanlı, Windows uyumlu). "
            "Bugünkü, yaklaşan, geciken veya tüm açık hatırlatıcıları özetler."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":     {"type": "STRING", "description": "today | upcoming | overdue | all | next"},
                "limit":     {"type": "NUMBER", "description": "Maksimum hatırlatıcı sayısı"},
                "list_name": {"type": "STRING", "description": "Belirli bir hatırlatıcı listesi adı"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_reminder",
        "description": (
            "Yerel hatırlatıcı sistemine yeni hatırlatıcı ekler (Windows uyumlu). "
            "Kullanıcı 'hatırlat', 'hatırlatıcı ekle', 'reminder kur' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title":     {"type": "STRING",  "description": "Hatırlatıcı başlığı"},
                "due_iso":   {"type": "STRING",  "description": "Opsiyonel tarih/saat ISO formatında"},
                "notes":     {"type": "STRING",  "description": "Opsiyonel not"},
                "list_name": {"type": "STRING",  "description": "Opsiyonel liste adı"},
                "priority":  {"type": "STRING",  "description": "low | medium | high"},
                "all_day":   {"type": "BOOLEAN", "description": "Tüm gün hatırlatıcı ise true"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "browser_control",
        "description": "Tarayıcıda URL açar, Google'da arama yapar veya YouTube'da ilk sonucu doğrudan oynatır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "open_url | search | play_youtube"},
                "url":    {"type": "STRING", "description": "Açılacak URL (open_url için)"},
                "query":  {"type": "STRING", "description": "Arama sorgusu (search veya play_youtube için)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "shell_run",
        "description": "Windows CMD veya PowerShell komutu çalıştırır. Dosya işlemleri, sistem yönetimi.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Çalıştırılacak CMD veya PowerShell komutu"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "play_media",
        "description": (
            "YouTube, Spotify veya Windows Media Player'da şarkı, müzik veya video açar. "
            "Kullanıcı belirli bir platform söylerse onu kullan. "
            "Belirtmezse Spotify varsa onu, yoksa YouTube'u kullan. "
            "Kullanıcı 'çal', 'oynat', 'aç' diyorsa autoplay=true kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":    {"type": "STRING",  "description": "Şarkı, sanatçı, albüm veya video arama"},
                "provider": {"type": "STRING",  "description": "auto | youtube | spotify | windows_media"},
                "autoplay": {"type": "BOOLEAN", "description": "true ise mümkünse doğrudan oynatır"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_youtube_channel_report",
        "description": (
            "YouTube kanalının public istatistiklerini ve son videoların performansını raporlar."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":       {"type": "STRING", "description": "Doğal dilde analiz isteği"},
                "handle":      {"type": "STRING", "description": "Opsiyonel kanal handle veya ID"},
                "video_limit": {"type": "NUMBER", "description": "Analize dahil edilecek son video sayısı"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_screen",
        "description": (
            "Aktif pencerenin ekran görüntünü alıp Gemini vision ile analiz eder. "
            "Kullanıcı ekranda ne olduğunu, bir hatayı, görünen metni sorduğunda kullan. "
            "Windows'ta PIL.ImageGrab + win32gui kullanılır (pywin32 gerekli)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Kullanıcının ekranla ilgili sorusu"},
                "target": {"type": "STRING", "description": "Şu an sadece active_window desteklenir."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Kullanıcı hakkında önemli bilgiyi kalıcı belleğe kaydeder. İsim, tercihler, projeler vb. duyunca sessizce çağır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {"type": "STRING", "description": "identity | preferences | projects | notes"},
                "key":      {"type": "STRING", "description": "Kısa anahtar (örn. 'name')"},
                "value":    {"type": "STRING", "description": "Değer (İngilizce)"}
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "delete_memory",
        "description": (
            "Kalıcı hafızadaki bir kaydı siler. "
            "Kullanıcı 'bunu hafızandan kaldır', 'unut', 'sil' gibi bir şey derse kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category":   {"type": "STRING", "description": "Kaydın kategorisi"},
                "key":        {"type": "STRING", "description": "Silinecek anahtar"},
                "match_text": {"type": "STRING", "description": "Kaydı bulmak için doğal dil parçası"}
            }
        }
    },
    {
        "name": "send_whatsapp_message",
        "description": (
            "WhatsApp Desktop URL scheme veya WhatsApp Web üzerinden mesaj taslağı açar veya gönderir. "
            "Kişi adı veya telefon numarasıyla çalışabilir. "
            "Windows'ta pyautogui ile otomatik gönderim yapılır."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient_name": {"type": "STRING",  "description": "Kişi adı"},
                "phone_number":   {"type": "STRING",  "description": "Uluslararası telefon numarası"},
                "message":        {"type": "STRING",  "description": "Gönderilecek mesaj"},
                "app_target":     {"type": "STRING",  "description": "desktop | web | auto"},
                "send_now":       {"type": "BOOLEAN", "description": "true ise mesajı otomatik gönderir"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "save_whatsapp_contact",
        "description": "Sık kullanılan bir WhatsApp kişisini adı ve telefon numarasıyla kalıcı belleğe kaydeder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "display_name": {"type": "STRING", "description": "Kişi adı"},
                "phone_number": {"type": "STRING", "description": "Uluslararası telefon numarası"},
                "aliases":      {"type": "STRING", "description": "Virgülle ayrılmış takma adlar"}
            },
            "required": ["display_name", "phone_number"]
        }
    },
    {
        "name": "wikipedia_lookup",
        "description": (
            "Bir kişi, yer, kurum veya kavram hakkında HIZLI ve güvenilir kısa özet için "
            "Wikipedia'ya bakar. 'X kimdir', 'Y nedir', 'Z nerede' gibi tanım sorularında "
            "önce bunu kullan; gerekiyorsa deep_web_search ile derinleştir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Özeti istenen kişi/yer/kavram"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "convert_currency",
        "description": (
            "Döviz ve kripto fiyatı/çevirisi yapar. 'Dolar kaç TL', 'bitcoin fiyatı', "
            "'100 euro kaç dolar' gibi sorularda kullan. Hem fiat hem kripto desteklenir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "amount":        {"type": "NUMBER", "description": "Miktar. Belirtilmezse 1 kabul edilir."},
                "from_currency": {"type": "STRING", "description": "Kaynak birim (USD, EUR, TRY, BTC, ETH ...)"},
                "to_currency":   {"type": "STRING", "description": "Hedef birim (varsayılan TRY)"}
            },
            "required": ["from_currency"]
        }
    },
    {
        "name": "translate_text",
        "description": "Verilen metni hedef dile çevirir. Kullanıcı çeviri istediğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text":        {"type": "STRING", "description": "Çevrilecek metin"},
                "target_lang": {"type": "STRING", "description": "Hedef dil (tr, en, de, fr ... veya 'ingilizce')"},
                "source_lang": {"type": "STRING", "description": "Kaynak dil. Boş/auto ise otomatik algılanır."}
            },
            "required": ["text", "target_lang"]
        }
    },
    {
        "name": "find_file",
        "description": (
            "Bilgisayarda dosya/belge arar (Masaüstü, Belgeler, İndirilenler vb.). "
            "Kullanıcı 'şu dosyayı bul', 'masaüstünde X dosyası var mı' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":       {"type": "STRING", "description": "Dosya adı veya anahtar kelimeler (örn. 'rapor pdf')"},
                "max_results": {"type": "NUMBER", "description": "En fazla sonuç sayısı (varsayılan 12)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_emails",
        "description": (
            "Gmail gelen kutusundaki son e-postaları okur (gönderen, konu, kısa özet). "
            "Kullanıcı 'maillerimi oku', 'gelen kutum' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "count": {"type": "NUMBER", "description": "Okunacak e-posta sayısı (varsayılan 5)"}
            }
        }
    },
    {
        "name": "send_email",
        "description": (
            "Gmail üzerinden e-posta gönderir. Kullanıcı e-posta göndermek istediğinde kullan; "
            "göndermeden önce alıcı, konu ve içeriği kısaca doğrula."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "to":      {"type": "STRING", "description": "Alıcı e-posta adresi (virgülle birden çok olabilir)"},
                "subject": {"type": "STRING", "description": "E-posta konusu"},
                "body":    {"type": "STRING", "description": "E-posta içeriği"}
            },
            "required": ["to", "body"]
        }
    },
    {
        "name": "close_app",
        "description": (
            "Bir uygulamayı kapatır. 'Spotify'ı kapat' gibi belirli bir uygulama için "
            "app_name ver. Kullanıcı 'açtığın uygulamaları kapat' derse app_name'i BOŞ "
            "bırak; EXON bu oturumda açtığı tüm uygulamaları kapatır. (Tarayıcı sekmesi "
            "için bunu değil 'close_browser_tab' kullan.)"
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Kapatılacak uygulama adı. Boş ise EXON'un açtığı tüm uygulamalar."}
            }
        }
    },
    {
        "name": "close_browser_tab",
        "description": (
            "Tarayıcının AKTİF SEKMESİNİ kapatır (Ctrl+W). Tarayıcının kendisini DEĞİL, "
            "sadece açık sekmeyi kapatır. Kullanıcı 'sekmeyi kapat', 'şu sekmeyi kapat' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "set_performance_mode",
        "description": (
            "Bilgisayarı oyun/performans moduna alır veya normale döndürür. Kullanıcı "
            "'oyun moduna geç', 'performansı arttır' derse mode=game; 'normal moda dön' "
            "derse mode=normal. Yüksek Performans güç planını açar ve EXON kendi kaynak "
            "kullanımını düşürür."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": {"type": "STRING", "description": "game | normal"}
            },
            "required": ["mode"]
        }
    },
    {
        "name": "system_power",
        "description": (
            "Bilgisayar güç işlemi yapar: kilitle/uyut/yeniden başlat/kapat/iptal. "
            "shutdown ve restart İÇİN önce kullanıcıdan onay al; lock ve sleep için onay gerekmez."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "lock | sleep | restart | shutdown | cancel"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "set_volume",
        "description": "Sistem ses seviyesini ayarlar (yükselt/azalt/sustur). Kullanıcı sesle ilgili bir şey isterse kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "up | down | mute"},
                "steps":  {"type": "NUMBER", "description": "Kaç kademe (up/down için, varsayılan 5)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Ekranın görüntüsünü alıp dosyaya kaydeder. Kullanıcı 'ekran görüntüsü al', 'screenshot' dediğinde kullan.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "compose_song",
        "description": (
            "İstenen tür (rap/pop/duygusal/arabesk/rock vb.), dil ve ruh haline uygun "
            "ANLAMLI bir şarkı sözü üretir. Kullanıcı 'şarkı söyle', 'rap yap', 'pop "
            "söyle' dediğinde önce bununla sözü üret, SONRA o sözü sesli olarak söyle."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic":    {"type": "STRING", "description": "Şarkının konusu/teması"},
                "style":    {"type": "STRING", "description": "rap | pop | duygusal | arabesk | rock ..."},
                "language": {"type": "STRING", "description": "Dil (tr, en ...). Varsayılan tr."},
                "mood":     {"type": "STRING", "description": "Ruh hali (neşeli, hüzünlü, motive ...). Opsiyonel."}
            }
        }
    },
    {
        "name": "get_news_briefing",
        "description": (
            "Günün haberlerini veya verilen konudaki haberleri özetler (Google News). "
            "Kullanıcı 'haberler', 'gündem', 'şu konuda haber' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic":    {"type": "STRING", "description": "Haber konusu. Boşsa günün manşetleri."},
                "count":    {"type": "NUMBER", "description": "Kaç haber (varsayılan 6)"},
                "language": {"type": "STRING", "description": "Dil (tr/en). Varsayılan tr."}
            }
        }
    },
    {
        "name": "get_stock_price",
        "description": (
            "Hisse senedi/endeks/kripto fiyatını verir. ABD: AAPL, TSLA; BIST: THYAO.IS, "
            "ASELS.IS; endeks: ^GSPC; kripto: BTC-USD. Kullanıcı borsa/hisse sorduğunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "symbol": {"type": "STRING", "description": "Sembol veya bilinen ad (apple, thy, aselsan ...)"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "read_code_file",
        "description": (
            "Kullanıcının bir kod/metin dosyasını satır numaralarıyla okur. EXON kod "
            "yardımı yaparken dosyayı görmek için kullanır."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path":      {"type": "STRING", "description": "Dosyanın tam yolu"},
                "max_chars": {"type": "NUMBER", "description": "En fazla karakter (varsayılan 20000)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_code_files",
        "description": "Bir klasördeki kod dosyalarını listeler (alt klasörler dahil). Projeyi keşfetmek için.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "directory": {"type": "STRING", "description": "Klasör yolu (varsayılan geçerli klasör)"},
                "pattern":   {"type": "STRING", "description": "İsim filtresi. Opsiyonel."}
            }
        }
    },
    {
        "name": "search_in_code",
        "description": "Bir klasördeki kod dosyalarında metin/desen arar (dosya:satır gösterir).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "directory":   {"type": "STRING", "description": "Klasör yolu (varsayılan geçerli klasör)"},
                "query":       {"type": "STRING", "description": "Aranacak metin"},
                "max_results": {"type": "NUMBER", "description": "En fazla sonuç (varsayılan 25)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "write_code_file",
        "description": (
            "Bir dosyaya kod/metin yazar veya oluşturur (var olanın üstüne yazabilir). "
            "EXON bir düzeltme/dosya oluşturma yaparken kullanır; üzerine yazmadan önce "
            "kullanıcıya ne yapacağını kısaca söyle."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path":    {"type": "STRING", "description": "Yazılacak dosyanın tam yolu"},
                "content": {"type": "STRING", "description": "Dosyaya yazılacak tam içerik"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "compose_text",
        "description": (
            "İstenen tür/ton/dilde metin yazar (e-posta, blog yazısı, sosyal medya gönderisi, "
            "deneme, özgeçmiş, ürün açıklaması vb.). Kullanıcı 'bana ... yaz' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "kind":     {"type": "STRING", "description": "Metin türü (e-posta, blog, tweet, deneme ...)"},
                "topic":    {"type": "STRING", "description": "Konu/istek"},
                "tone":     {"type": "STRING", "description": "Ton (profesyonel, samimi, resmi, esprili ...)"},
                "language": {"type": "STRING", "description": "Dil (tr, en ...). Varsayılan tr."}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "summarize_url",
        "description": "Bir web sayfasını/makaleyi getirip madde madde özetler. Kullanıcı bir linki özetlemeni isterse kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url":      {"type": "STRING", "description": "Özetlenecek sayfa bağlantısı"},
                "language": {"type": "STRING", "description": "Özet dili. Varsayılan tr."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "summarize_document",
        "description": "Yerel bir belgeyi (txt/md/kod; PDF varsa pypdf ile) özetler. Kullanıcı 'şu dosyayı özetle' dediğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path":     {"type": "STRING", "description": "Belgenin tam yolu"},
                "language": {"type": "STRING", "description": "Özet dili. Varsayılan tr."}
            },
            "required": ["path"]
        }
    }
]


def get_api_key() -> str:
    return str(get_app_config_value("gemini_api_key", "") or "")


_TEXT_CLIENT = None
_TEXT_CLIENT_LOCK = threading.Lock()


def _get_text_client():
    """Telegram/Discord metin yanıtları için Gemini istemcisini bir kez oluşturup
    yeniden kullanır (her çağrıda yeni istemci kurmaktan daha hızlı)."""
    global _TEXT_CLIENT
    with _TEXT_CLIENT_LOCK:
        if _TEXT_CLIENT is None:
            _TEXT_CLIENT = genai.Client(api_key=get_api_key())
        return _TEXT_CLIENT


def load_system_prompt() -> str:
    # Canlı ses modelinin hızlı ve odaklı anlaması için KISA ve ÖZ tutuldu.
    return (
        "Sen EXON'sun; seni EXON Robotik adlı teknoloji firması geliştirdi. "
        "'Seni kim yaptı?' sorusuna 'EXON Robotik firması geliştirdi' de. "
        "Türkçe konuş; sıcak, enerjik ol ve arada bir hafif espri yap.\n"
        "HIZ: Kısa, net ve hızlı cevap ver; 'bakayım/bir saniye' gibi dolgu kurma. "
        "Bir araç gerekiyorsa tereddütsüz HEMEN çağır ve sonucu söyle. Kararlı ol.\n"
        "ARAÇLAR (gerektiğinde):\n"
        "- Güncel bilgi/haber/kişi/şirket/ürün → deep_web_search (çok kaynak; uydurma). "
        "Tanım/kim/nedir → wikipedia_lookup.\n"
        "- Görsel/çizim/logo → hemen generate_image. Hava → get_weather. Döviz/kripto → convert_currency. "
        "Hisse → get_stock_price. Haber → get_news_briefing. Çeviri → translate_text. Dosya → find_file. "
        "E-posta → read_emails/send_email.\n"
        "- Uygulama aç/kapat → open_app/close_app; sekme → close_browser_tab; oyun modu → set_performance_mode; "
        "ses → set_volume; ekran görüntüsü → take_screenshot; güç → system_power (kapat/yeniden başlat için önce onay al).\n"
        "- Kod yardımı → list_code_files/read_code_file/search_in_code/write_code_file (üzerine yazmadan önce kısaca söyle).\n"
        "- Metin yazma (e-posta/blog/sosyal medya) → compose_text. Web sayfası özeti → summarize_url. "
        "Belge/dosya özeti → summarize_document.\n"
        "- Tekrarlayan görev → add_scheduled_task; yüz tanıma → recognize_face; ekran → analyze_screen; "
        "kalıcı bilgi → save_memory.\n"
        "ŞARKI: Kullanıcı şarkı isterse compose_song ile (tür/dil/ruh hali) söz üret; arkada ritim otomatik çalar. "
        "Sözleri DÜZ OKUMA — melodiyle ve ruh haline göre tonla söyle (mutlu=canlı, hüzünlü=içten, rap=ritmik).\n"
        "Bazı özellikler (görsel, şarkı, kod, e-posta, borsa, haber, oyun modu, ekran analizi) EXON Pro'ya "
        "özeldir; bir araç 'Pro' mesajı döndürürse kullanıcıya kibarca ilet ve yükseltmeyi öner.\n"
        "Emin olmadığını kesin gibi sunma; bilmiyorsan araştır. Gereksiz ayrıntıyı atlama, net ol."
    )


class ExonLive:
    def __init__(self, ui: ExonUI):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        # Barge-in: EXON konuşurken kullanıcı konuşursa sus ve dinle.
        self._barge_in_enabled   = bool(get_app_config_value("barge_in", True))
        self._barge_in_threshold = float(get_app_config_value("barge_in_threshold", 1100) or 1100)
        self._barge_in_count     = 0
        self._greeted            = False
        self._singing            = False

        self.ui.on_text_command  = self._on_text_command
        self.ui.on_pause_toggle  = self._on_pause_toggle
        self.ui.on_effects_state_change = self._on_effects_state_change
        self.ui.on_image_uploaded = self._on_image_uploaded
        self._paused             = False

        # ── İleri seviye alt sistemler (hepsi opsiyonel, yoksa sessizce devre dışı) ──
        self.wake      = WakeWordListener()
        self.scheduler = TaskScheduler(self._on_scheduled_task)
        self.face      = FaceAuth()
        self.telegram  = TelegramBridge(self._handle_remote_command)
        self.discord   = DiscordBridge(self._handle_remote_command)
        self._services_started = False

        # Uyandırma sözcüğü aktifse arka planda standby (mikrofon kapalı) başla
        if self.wake.enabled:
            self.ui.muted = True
            try:
                self.ui.root.after(0, self.ui._draw_mute_button)
            except Exception:
                pass

    def _on_pause_toggle(self, paused: bool):
        self._paused = paused

    def _on_effects_state_change(self, enabled: bool):
        pass

    def _focus_ui_section_for_tool(self, tool_name: str, args: dict):
        if tool_name == "sys_info":
            query = str(args.get("query", "")).strip().lower()
            if query in {"time", "saat", "zaman", "date", "tarih"}:
                self.ui.focus_panel("time", duration_ms=5200)
            else:
                self.ui.focus_panel("system", duration_ms=5200)
        elif tool_name == "get_weather":
            self.ui.focus_panel("weather", duration_ms=5600)

    def _on_text_command(self, text: str):
        if self._paused:
            return
        self.ui.write_log(f"Siz: {text}")
        if not self._loop or not self.session:
            self.ui.write_log("ERR: EXON bağlantısı henüz hazır değil.")
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def _on_image_uploaded(self, image_path: str, query: str = ""):
        """UI'dan görsel yüklendiğinde çağrılır: analiz et ve sesli yanıt için oturuma ilet."""
        if self._paused:
            self.ui.write_log("SYS: EXON duraklatılmış. Görseli işlemek için devam et.")
            return
        threading.Thread(
            target=self._process_uploaded_image,
            args=(image_path, query),
            daemon=True,
        ).start()

    def _process_uploaded_image(self, image_path: str, query: str = ""):
        self.ui.set_state("THINKING")
        q = query.strip() if query else "Bu görselde ne var? Detaylı açıkla."
        try:
            analysis = analyze_image_file(image_path, q)
        except Exception as e:
            analysis = f"Görsel analizi başarısız: {e}"
        self.ui.write_log(f"EXON (görsel): {analysis}")
        if self._loop and self.session:
            msg = (
                "Kullanıcı bir görsel yükledi. Otomatik görsel analizi şu şekilde:\n"
                f"{analysis}\n\n"
                "Bu analizi kullanıcıya kısa, net ve Türkçe olarak sesli açıkla."
            )
            try:
                asyncio.run_coroutine_threadsafe(
                    self.session.send_client_content(
                        turns={"parts": [{"text": msg}]},
                        turn_complete=True,
                    ),
                    self._loop,
                )
            except Exception:
                pass

    # ── İleri seviye: uyandırma / planlayıcı / uzaktan komut ─────────────────
    def _send_to_session(self, text: str):
        """Verilen metni canlı oturuma iletir (EXON sesli yanıtlar)."""
        if self._loop and self.session:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.session.send_client_content(
                        turns={"parts": [{"text": text}]}, turn_complete=True),
                    self._loop,
                )
            except Exception:
                pass

    async def _wake_up(self):
        """'Hey EXON' algılandığında: standby'dan çık ve 'Efendim?' de."""
        self.ui.muted = False
        try:
            self.ui.root.after(0, self.ui._draw_mute_button)
        except Exception:
            pass
        self.ui.write_log("SYS: 🔔 'Hey EXON' algılandı. Efendim?")
        self.ui.play_success_sfx()
        if self.session:
            try:
                await self.session.send_client_content(
                    turns={"parts": [{"text": (
                        "Kullanıcı seni 'Hey EXON' diyerek çağırdı. Çok kısa, sıcak ve "
                        "kibar bir tonla sadece 'Efendim?' diye yanıt ver."
                    )}]},
                    turn_complete=True,
                )
            except Exception:
                pass

    def _on_scheduled_task(self, task: dict):
        """Zamanlanmış görev vakti geldiğinde (scheduler thread'inden) çağrılır."""
        prompt = task.get("prompt", "")
        self.ui.write_log(f"SYS: ⏰ Zamanlanmış görev: {prompt}")
        if self.ui.muted:                       # standby ise uyandır
            self.ui.muted = False
            try:
                self.ui.root.after(0, self.ui._draw_mute_button)
            except Exception:
                pass
        self._send_to_session(prompt)

    def _gemini_text_answer(self, text: str) -> str:
        """Telegram/Discord için Gemini metin yanıtı (EXON kişiliğiyle)."""
        try:
            client = _get_text_client()
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=load_system_prompt(), temperature=0.6),
            )
            return (getattr(resp, "text", "") or "Yanıt alınamadı.").strip()
        except Exception as exc:
            return f"Yanıt alınamadı: {exc}"

    def _handle_remote_command(self, text: str) -> dict:
        """Telegram/Discord'dan gelen komutu işler. {'text':..., 'image':...} döner."""
        text = (text or "").strip()
        low = text.lower()
        self.ui.write_log(f"SYS: 📲 Uzaktan komut: {text[:60]}")

        if low in ("/start", "/help", "yardım"):
            return {"text": ("EXON uzaktan komut 🤖\n"
                             "/gorsel <açıklama> — görsel oluştur\n"
                             "/hava [şehir] — hava durumu\n"
                             "/ara <konu> — web araştırması\n"
                             "Ya da doğrudan sorunu yaz.")}

        if low.startswith(("/gorsel", "/görsel", "/image")) or "görsel oluştur" in low or "resim çiz" in low:
            prompt = text.split(" ", 1)[1].strip() if " " in text else ""
            if not prompt:
                return {"text": "Kullanım: /gorsel <açıklama>"}
            res = generate_image(prompt)
            if res.get("ok") and res.get("path"):
                return {"text": f"İşte '{prompt}' görseli ✅", "image": res["path"]}
            return {"text": res.get("message", "Görsel oluşturulamadı.")}

        if low.startswith("/hava") or "hava durumu" in low:
            city = text.split(" ", 1)[1].strip() if " " in text else None
            return {"text": get_weather_summary(city)}

        if low.startswith("/ara") or low.startswith("ara ") or low.startswith("araştır"):
            q = text.split(" ", 1)[1].strip() if " " in text else ""
            if not q:
                return {"text": "Kullanım: /ara <konu veya kişi>"}
            return {"text": perform_web_scrape_search(q)[:3500]}

        return {"text": self._gemini_text_answer(text)}

    async def _interrupt_playback(self):
        """Barge-in: yerel ses kuyruğunu boşaltıp EXON'u susturur. Sunucu yeni
        kullanıcı sesini alınca eski yanıtı zaten otomatik keser."""
        try:
            if self.audio_in_queue:
                while not self.audio_in_queue.empty():
                    try:
                        self.audio_in_queue.get_nowait()
                    except Exception:
                        break
            self.set_speaking(False)
            self.ui.write_log("SYS: ✋ Sözünüzü aldım — dinliyorum.")
        except Exception:
            pass

    async def _interrupt_audio(self):
        try:
            if self.audio_in_queue:
                while not self.audio_in_queue.empty():
                    try:
                        self.audio_in_queue.get_nowait()
                    except Exception:
                        break
            if self.session:
                await self.session.send_realtime_input(audio_stream_end=True)
            self.set_speaking(False)
        except Exception:
            pass

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        else:
            self.ui.set_state("LISTENING")

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.ui.write_debug(f"{tool_name}: {short}", level="ERROR")
        self.ui.set_state("ERROR")

    @staticmethod
    def _result_looks_like_error(result) -> bool:
        text = str(result or "").strip()
        if not text:
            return False
        low = text.lower()
        # Açık hata öneki her zaman hatadır.
        if low.startswith("hata:") or low.startswith("err:"):
            return True
        # Uzun içerik (web arama sonucu, ekran/görsel analizi vb.) içinde 'hata',
        # 'error' gibi kelimeler geçse bile HATA SAYILMAZ — bu yanlış alarmları önler.
        if len(text) > 200:
            return False
        # Kısa mesajlarda yalnızca gerçek başarısızlık kalıplarını hata say.
        failure_markers = (
            "alınamadı", "alinamadi", "bulunamadı", "bulunamadi",
            "açılamadı", "acilamadi", "tamamlanamadı", "tamamlanamadi",
            "oluşturulamadı", "olusturulamadi", "okunamadı", "okunamadi",
            "erişilemedi", "erisilemedi", "geçersiz", "gecersiz",
            "api anahtarı eksik", "izin gerek",
        )
        return any(marker in low for marker in failure_markers)

    @staticmethod
    def _should_play_success_sfx(tool_name: str, args: dict, result) -> bool:
        action_tools = {"open_app", "add_calendar_event", "add_reminder", "delete_calendar_event"}
        if tool_name in action_tools:
            return True
        if tool_name == "send_whatsapp_message":
            text = str(result or "").lower()
            if bool(args.get("send_now", False)):
                return "gönderildi" in text or "gonderildi" in text
            return False
        return False

    @staticmethod
    def _clean_transcript_text(text: str) -> tuple[str, bool]:
        raw      = str(text or "")
        had_noise = False
        if CONTROL_TOKEN_RE.search(raw):
            had_noise = True
            raw = CONTROL_TOKEN_RE.sub(" ", raw)
        cleaned = []
        for ch in raw:
            if ch in "\n\r\t" or ord(ch) >= 32:
                cleaned.append(ch)
            else:
                had_noise = True
        normalized = " ".join("".join(cleaned).split())
        return normalized.strip(), had_noise

    def _build_config(self) -> types.LiveConnectConfig:
        memory  = load_memory()
        mem_str = format_memory_for_prompt(memory)
        sys_p   = load_system_prompt()
        now     = datetime.datetime.now()
        time_ctx = f"[ŞU ANKİ ZAMAN]\n{now.strftime('%A, %d %B %Y — %H:%M')}\n\n"

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str + "\n\n")
        parts.append(sys_p)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=str(get_app_config_value("voice", "Charon") or "Charon")
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        print(f"[EXON] 🔧 {name} {args}")
        # EXON Pro kapısı: Free kullanıcı Pro'ya özel bir araç çağırırsa yükseltme öner.
        if name in PRO_TOOLS and not _is_pro():
            msg = ("Bu özellik EXON Pro'ya özel. Sağ üstteki '✦ PRO'YA GEÇ' butonundan "
                   "ya da satın alma bağlantısından yükseltebilirsin. Yükseltmek ister misin?")
            print(f"[EXON] 🔒 PRO gerekli: {name}")
            return types.FunctionResponse(id=fc.id, name=name, response={"result": msg})
        self.ui.set_state("THINKING")

        loop   = asyncio.get_event_loop()
        result = "Tamam."
        had_exception = False

        try:
            if name == "deep_web_search":
                r = await loop.run_in_executor(None, lambda: perform_web_scrape_search(args.get("query", "")))
                result = r or "Arama yapıldı ancak veri döndürülemedi."

            elif name == "generate_image":
                res = await loop.run_in_executor(
                    None, lambda: generate_image(args.get("prompt", "")))
                if res.get("ok") and res.get("path"):
                    self.ui.show_image_preview(res["path"], title="EXON · Oluşturulan Görsel")
                    self.ui.play_success_sfx()
                result = res.get("message", "Görsel işlemi tamamlandı.")

            elif name == "add_scheduled_task":
                task = self.scheduler.add_task(
                    args.get("time", ""), args.get("prompt", ""),
                    args.get("repeat", "daily"))
                result = (f"Görev eklendi: {task['time']} ({task['repeat']}) → {task['prompt']}")

            elif name == "list_scheduled_tasks":
                tasks = self.scheduler.list_tasks()
                if not tasks:
                    result = "Zamanlanmış görev yok."
                else:
                    result = "Zamanlanmış görevler:\n" + "\n".join(
                        f"- [{t['id']}] {t['time']} ({t['repeat']}): {t['prompt']}"
                        for t in tasks)

            elif name == "remove_scheduled_task":
                removed = self.scheduler.remove_task(args.get("identifier", ""))
                result = f"{removed} görev silindi." if removed else "Eşleşen görev bulunamadı."

            elif name == "recognize_face":
                r = await loop.run_in_executor(None, self.face.recognize_summary)
                result = r or "Yüz tanıma tamamlanamadı."

            elif name == "save_memory":
                cat = args.get("category", "notes")
                key = args.get("key", "")
                val = args.get("value", "")
                if key and val:
                    update_memory({cat: {key: {"value": val}}})
                    print(f"[Memory] 💾 {cat}/{key} = {val}")
                result = "ok"

            elif name == "delete_memory":
                result = delete_memory(
                    args.get("category", ""),
                    args.get("key", ""),
                    args.get("match_text", ""),
                )

            elif name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(args.get("app_name", "")))
                result = r or f"{args.get('app_name')} açıldı."

            elif name == "sys_info":
                self._focus_ui_section_for_tool(name, args)
                r = await loop.run_in_executor(None, lambda: sys_info(args.get("query", "all")))
                result = r or "Bilgi alındı."

            elif name == "get_weather":
                self._focus_ui_section_for_tool(name, args)
                r = await loop.run_in_executor(
                    None, lambda: get_weather_summary(args.get("location") or None))
                result = r or "Hava durumu bilgisi alındı."

            elif name == "get_calendar_events":
                r = await loop.run_in_executor(
                    None, lambda: get_calendar_events(
                        args.get("query", "today"),
                        int(args.get("limit", 6) or 6),
                    ))
                result = r or "Takvim bilgisi alındı."

            elif name == "add_calendar_event":
                r = await loop.run_in_executor(
                    None, lambda: add_calendar_event(
                        args.get("title", ""),
                        args.get("start_iso", ""),
                        args.get("end_iso", ""),
                        args.get("notes", ""),
                        args.get("location", ""),
                        args.get("calendar_name", ""),
                        bool(args.get("all_day", False)),
                    ))
                result = r or "Takvim etkinliği eklendi."

            elif name == "delete_calendar_event":
                r = await loop.run_in_executor(
                    None, lambda: delete_calendar_event(
                        args.get("title", ""),
                        args.get("start_iso", ""),
                        args.get("calendar_name", ""),
                        bool(args.get("delete_all_matches", False)),
                    ))
                result = r or "Takvim etkinliği silindi."

            elif name == "get_reminders":
                r = await loop.run_in_executor(
                    None, lambda: get_reminders(
                        args.get("query", "upcoming"),
                        int(args.get("limit", 8) or 8),
                        args.get("list_name", ""),
                    ))
                result = r or "Hatırlatıcı bilgisi alındı."

            elif name == "add_reminder":
                r = await loop.run_in_executor(
                    None, lambda: add_reminder(
                        args.get("title", ""),
                        args.get("due_iso", ""),
                        args.get("notes", ""),
                        args.get("list_name", ""),
                        args.get("priority", ""),
                        bool(args.get("all_day", False)),
                    ))
                result = r or "Hatırlatıcı eklendi."

            elif name == "browser_control":
                r = await loop.run_in_executor(
                    None, lambda: browser_control(
                        args.get("action"),
                        args.get("url"),
                        args.get("query"),
                    ))
                result = r or "Tamam."

            elif name == "shell_run":
                r = await loop.run_in_executor(
                    None, lambda: shell_run(args.get("command", "")))
                result = r or "Komut çalıştırıldı."

            elif name == "play_media":
                r = await loop.run_in_executor(
                    None, lambda: play_media(
                        args.get("query", ""),
                        args.get("provider", "auto"),
                        bool(args.get("autoplay", True)),
                    ))
                result = r or "Medya oynatma başlatıldı."

            elif name == "get_youtube_channel_report":
                r = await loop.run_in_executor(
                    None, lambda: get_youtube_channel_report(
                        args.get("query", "overview"),
                        args.get("handle", ""),
                        int(args.get("video_limit", 6) or 6),
                    ))
                result = r or "YouTube kanal raporu alındı."

            elif name == "analyze_screen":
                r = await loop.run_in_executor(
                    None, lambda: analyze_screen(
                        args.get("query", "Ekranda ne var?"),
                        args.get("target", "active_window"),
                    ))
                result = r or "Ekran analizi tamamlandı."

            elif name == "send_whatsapp_message":
                r = await loop.run_in_executor(
                    None, lambda: send_whatsapp_message(
                        args.get("message", ""),
                        args.get("phone_number", ""),
                        args.get("recipient_name", ""),
                        bool(args.get("send_now", False)),
                        args.get("app_target", "auto"),
                    ))
                result = r or "WhatsApp işlemi tamamlandı."

            elif name == "save_whatsapp_contact":
                r = await loop.run_in_executor(
                    None, lambda: save_whatsapp_contact(
                        args.get("display_name", ""),
                        args.get("phone_number", ""),
                        args.get("aliases", ""),
                    ))
                result = r or "WhatsApp kişisi kaydedildi."

            elif name == "wikipedia_lookup":
                r = await loop.run_in_executor(
                    None, lambda: get_wikipedia_summary(args.get("query", "")))
                result = r or "Wikipedia özeti alınamadı."

            elif name == "convert_currency":
                r = await loop.run_in_executor(
                    None, lambda: convert_currency(
                        args.get("amount", 1),
                        args.get("from_currency", ""),
                        args.get("to_currency", ""),
                    ))
                result = r or "Kur bilgisi alınamadı."

            elif name == "translate_text":
                r = await loop.run_in_executor(
                    None, lambda: translate_text(
                        args.get("text", ""),
                        args.get("target_lang", "tr"),
                        args.get("source_lang", "auto"),
                    ))
                result = r or "Çeviri yapılamadı."

            elif name == "find_file":
                r = await loop.run_in_executor(
                    None, lambda: find_file(
                        args.get("query", ""),
                        int(args.get("max_results", 12) or 12),
                    ))
                result = r or "Dosya bulunamadı."

            elif name == "read_emails":
                r = await loop.run_in_executor(
                    None, lambda: read_recent_emails(int(args.get("count", 5) or 5)))
                result = r or "E-posta okunamadı."

            elif name == "send_email":
                r = await loop.run_in_executor(
                    None, lambda: send_email(
                        args.get("to", ""),
                        args.get("subject", ""),
                        args.get("body", ""),
                    ))
                result = r or "E-posta işlemi tamamlandı."

            elif name == "close_app":
                app = str(args.get("app_name", "") or "").strip()
                if not app or app.lower() in ("all", "hepsi", "tümü", "tumu", "hepsini", "açtıkların", "actiklarin"):
                    r = await loop.run_in_executor(None, close_opened_apps)
                else:
                    r = await loop.run_in_executor(None, lambda: close_app(app))
                result = r or "Uygulama kapatma işlemi tamamlandı."

            elif name == "close_browser_tab":
                r = await loop.run_in_executor(None, close_browser_tab)
                result = r or "Sekme kapatma işlemi tamamlandı."

            elif name == "set_performance_mode":
                mode = str(args.get("mode", "game") or "game")
                r = await loop.run_in_executor(None, lambda: set_performance_mode(mode))
                try:
                    is_game = mode.lower() not in ("normal", "off", "kapat", "kapa", "balanced", "dengeli")
                    self.ui.set_game_mode(is_game)
                except Exception:
                    pass
                result = r or "Performans modu ayarlandı."

            elif name == "system_power":
                r = await loop.run_in_executor(None, lambda: power_action(args.get("action", "")))
                result = r or "Güç işlemi tamamlandı."

            elif name == "set_volume":
                r = await loop.run_in_executor(
                    None, lambda: set_volume(args.get("action", "mute"), int(args.get("steps", 5) or 5)))
                result = r or "Ses ayarlandı."

            elif name == "take_screenshot":
                r = await loop.run_in_executor(None, take_screenshot)
                result = r or "Ekran görüntüsü işlemi tamamlandı."

            elif name == "compose_song":
                style = str(args.get("style", "pop") or "pop")
                mood  = str(args.get("mood", "") or "")
                r = await loop.run_in_executor(
                    None, lambda: compose_song(
                        args.get("topic", ""), style,
                        args.get("language", "tr"), mood,
                    ))
                if r and not self._result_looks_like_error(r):
                    try:
                        self._singing = True
                        self.ui.start_song_beat(style)
                    except Exception:
                        pass
                    result = (
                        "ŞARKI HAZIR. Bu sözleri ASLA düz konuşur gibi OKUMA — gerçek bir "
                        f"şarkı gibi MELODİYLE, {style} tarzında ve "
                        f"{mood or 'sözlere uygun'} bir TONLA söyle. Arkada ritim çalıyor, "
                        "temposuna uy. Doğrudan şarkıya gir, uzun açıklama yapma.\n\nSÖZLER:\n" + r
                    )
                else:
                    result = r or "Şarkı sözü üretilemedi."

            elif name == "get_news_briefing":
                r = await loop.run_in_executor(
                    None, lambda: get_news_briefing(
                        args.get("topic", ""),
                        int(args.get("count", 6) or 6),
                        args.get("language", "tr"),
                    ))
                result = r or "Haber alınamadı."

            elif name == "get_stock_price":
                r = await loop.run_in_executor(
                    None, lambda: get_stock_price(args.get("symbol", "")))
                result = r or "Fiyat alınamadı."

            elif name == "read_code_file":
                r = await loop.run_in_executor(
                    None, lambda: read_code_file(
                        args.get("path", ""),
                        int(args.get("max_chars", 20000) or 20000),
                    ))
                result = r or "Dosya okunamadı."

            elif name == "list_code_files":
                r = await loop.run_in_executor(
                    None, lambda: list_code_files(
                        args.get("directory", "."),
                        args.get("pattern", ""),
                    ))
                result = r or "Dosya bulunamadı."

            elif name == "search_in_code":
                r = await loop.run_in_executor(
                    None, lambda: search_in_code(
                        args.get("directory", "."),
                        args.get("query", ""),
                        int(args.get("max_results", 25) or 25),
                    ))
                result = r or "Sonuç bulunamadı."

            elif name == "write_code_file":
                r = await loop.run_in_executor(
                    None, lambda: write_code_file(
                        args.get("path", ""),
                        args.get("content", ""),
                    ))
                result = r or "Dosya yazma işlemi tamamlandı."

            elif name == "compose_text":
                r = await loop.run_in_executor(
                    None, lambda: compose_text(
                        args.get("kind", "metin"),
                        args.get("topic", ""),
                        args.get("tone", "profesyonel"),
                        args.get("language", "tr"),
                    ))
                result = r or "Metin üretilemedi."

            elif name == "summarize_url":
                r = await loop.run_in_executor(
                    None, lambda: summarize_url(
                        args.get("url", ""), args.get("language", "tr")))
                result = r or "Özet çıkarılamadı."

            elif name == "summarize_document":
                r = await loop.run_in_executor(
                    None, lambda: summarize_document(
                        args.get("path", ""), args.get("language", "tr")))
                result = r or "Özet çıkarılamadı."

            else:
                result = f"Bilinmeyen araç: {name}"

        except Exception as e:
            result = f"Hata: {e}"
            had_exception = True
            traceback.print_exc()
            self.speak_error(name, e)

        tool_failed = self._result_looks_like_error(result)
        if tool_failed:
            if not had_exception:
                self.ui.set_state("ERROR")
        elif self._should_play_success_sfx(name, args, result):
            self.ui.play_success_sfx()

        if not tool_failed and not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[EXON] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        print("[EXON] 🎤 Mikrofon başladı")
        if pya is None:
            print("[EXON] Mikrofon yok; sesli giris devre disi.")
            return
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT, channels=CHANNELS,
            rate=SEND_SAMPLE_RATE, input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        try:
            while True:
                data = await asyncio.to_thread(stream.read, CHUNK_SIZE, exception_on_overflow=False)
                # Standby (mikrofon kapalı) + uyandırma aktifse: 'Hey EXON' dinle
                if self.wake.enabled and self.ui.muted and not self._paused:
                    try:
                        if self.wake.process(data):
                            await self._wake_up()
                    except Exception:
                        pass
                    continue
                if self.ui.muted or self._paused:
                    continue
                with self._speaking_lock:
                    exon_speaking = self._is_speaking
                if exon_speaking:
                    # Barge-in: EXON konuşurken kullanıcı yeterince yüksek sesle
                    # konuşursa EXON'u SUSTUR ve kullanıcıyı dinlemeye geç.
                    if self._barge_in_enabled and _audio_rms(data) >= self._barge_in_threshold:
                        self._barge_in_count += 1
                        if self._barge_in_count >= 4:
                            await self._interrupt_playback()
                            self._barge_in_count = 0
                            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                    else:
                        self._barge_in_count = 0
                    # Konuşurken sessizlik/eko sesini gönderme (yanlış kesilmeyi önler).
                else:
                    self._barge_in_count = 0
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            print(f"[EXON] ❌ Mikrofon: {e}")
            raise
        finally:
            stream.close()

    async def _receive_audio(self):
        print("[EXON] 👂 Alım başladı")
        out_buf, in_buf = [], []
        output_noise = False
        output_noise_samples = []
        try:
            while True:
                async for response in self.session.receive():
                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        # Sunucu kullanıcının araya girdiğini bildirdiyse tamponu boşalt
                        # ki EXON anında sussun (barge-in).
                        if getattr(sc, "interrupted", None):
                            while not self.audio_in_queue.empty():
                                try:
                                    self.audio_in_queue.get_nowait()
                                except Exception:
                                    break
                            self.set_speaking(False)

                        if sc.output_transcription and sc.output_transcription.text:
                            self.set_speaking(True)
                            raw_txt = sc.output_transcription.text.strip()
                            if raw_txt:
                                txt, had_noise = self._clean_transcript_text(raw_txt)
                                if had_noise:
                                    output_noise = True
                                    if len(output_noise_samples) < 4:
                                        output_noise_samples.append(raw_txt)
                                if txt:
                                    out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = sc.input_transcription.text.strip()
                            if txt:
                                in_buf.append(txt)
                                self.ui.mark_user_activity(True)

                        if sc.turn_complete:
                            if self._singing:
                                self._singing = False
                                try:
                                    self.ui.stop_song_beat()
                                except Exception:
                                    pass
                            self.set_speaking(False)
                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"Siz: {full_in}")
                            in_buf = []
                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"EXON: {full_out}")
                                if output_noise_samples:
                                    self.ui.write_debug(
                                        "Kısmen filtrelenen ses transcripti: " + " | ".join(output_noise_samples),
                                        level="WARN",
                                    )
                            elif output_noise:
                                # Native-audio modeli zaman zaman yalnızca <ctrl> kontrol
                                # token'ı üretir. Ses normal çalar; bu bir hata DEĞİLDİR,
                                # sadece transcript gürültüsüdür. ERROR durumuna geçme.
                                if output_noise_samples:
                                    self.ui.write_debug(
                                        "Filtrelenen transcript gürültüsü (hata değil): "
                                        + " | ".join(output_noise_samples),
                                        level="WARN",
                                    )
                            out_buf = []
                            output_noise = False
                            output_noise_samples = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[EXON] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(function_responses=fn_responses)

        except Exception as e:
            print(f"[EXON] ❌ Alım: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[EXON] 🔊 Ses çalma başladı")
        if pya is None:
            print("[EXON] Ses cikisi yok; sesli yanit devre disi.")
            return
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT, channels=CHANNELS,
            rate=RECV_SAMPLE_RATE, output=True,
        )
        try:
            while True:
                chunk = await self.audio_in_queue.get()
                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[EXON] ❌ Ses: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.close()

    def _start_background_services(self):
        """Planlayıcı + Telegram + Discord köprülerini bir kez başlatır."""
        if self._services_started:
            return
        self._services_started = True
        try:
            self.scheduler.start()
            n = len(self.scheduler.list_tasks())
            if n:
                self.ui.write_log(f"SYS: ⏰ Planlayıcı aktif ({n} görev).")
        except Exception:
            pass
        try:
            if self.telegram.enabled:
                self.telegram.start()
                self.ui.write_log("SYS: 📲 Telegram köprüsü aktif.")
        except Exception:
            pass
        try:
            if self.discord.enabled:
                self.discord.start()
                self.ui.write_log("SYS: 📲 Discord köprüsü aktif.")
        except Exception:
            pass
        if self.wake.enabled:
            self.ui.write_log(f"SYS: 🔔 Uyandırma sözcüğü hazır: {self.wake.label}")

    async def run(self):
        client = genai.Client(
            api_key=get_api_key(),
            http_options={"api_version": "v1alpha"}
        )

        while True:
            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                print("[EXON] 🔌 Bağlanıyor...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session        = session
                    self._loop          = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue      = asyncio.Queue(maxsize=10)

                    print("[EXON] ✅ Bağlandı.")
                    self.ui.set_state("LISTENING")
                    self._start_background_services()
                    if self.wake.enabled and self.ui.muted:
                        self.ui.write_log(
                            f"SYS: EXON hazır (standby). Uyandırmak için '{self.wake.label}' de.")
                    else:
                        self.ui.write_log("SYS: EXON hazır. Dinliyorum...")

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

                    # İlk bağlantıda kullanıcıyı kişisel olarak selamla (bir kez).
                    if not self._greeted and not self.ui.muted:
                        self._greeted = True
                        try:
                            await session.send_client_content(
                                turns={"parts": [{"text": (
                                    "Oturum başladı. Kullanıcıya çok kısa (tek cümle), sıcak ve "
                                    "EXON Robotik kimliğine yakışır bir karşılama yap; biliyorsan "
                                    "ismiyle hitap et ve günün vaktine göre selam ver."
                                )}]},
                                turn_complete=True,
                            )
                        except Exception:
                            pass

            except Exception as e:
                print(f"[EXON] ⚠️ {e}")
                traceback.print_exc()
                self.set_speaking(False)
                self.ui.write_log(f"ERR: EXON bağlantısı kesildi — {e}")
                self.ui.set_state("ERROR")
                print("[EXON] 🔄 2 saniyede yeniden bağlanıyor...")
                await asyncio.sleep(2)


def main():
    ui = ExonUI()

    def runner():
        ui.wait_for_api_key()
        exon = ExonLive(ui)
        try:
            asyncio.run(exon.run())
        except KeyboardInterrupt:
            print("\n🔴 Kapatılıyor...")

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()