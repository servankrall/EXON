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
from actions.dev_mode import record_tool, record_event, system_status_text
from memory.smart_memory import (remember as smart_remember, cleanup_memory,
                                  build_user_profile, compress_memory_summary)
from actions.security import (encrypt_memory, decrypt_memory, verify_integrity,
                              snapshot_integrity, recover_json, security_report,
                              read_security_log, log_security)
from actions.analytics import (track_feature, usage_report, health_report,
                               mark_session, CACHE)
from actions.task_manager import (create_task, add_subtask, complete_subtask,
                                  list_tasks, task_status, remove_task, task_history)
from actions.verifier import review_answer, verify_against_sources
from actions.knowledge import (learn_text, learn_file, knowledge_search,
                               knowledge_query, knowledge_stats)
from actions.self_improve import self_audit, optimize_self
from actions.emotion import ENGINE as EMOTION, emotion_status, set_emotion as _set_emotion
from actions.mischief import savage_prank, get_roast, send_savage_report, rage_attack
from actions.romance import love_poem, write_love_letter, play_love_music, romantic_surprise
from actions.toolbox import (calculate, convert_units, generate_password,
                            random_decision, clipboard_action, text_tools, desktop_notify)
from actions.emotion_actions import emotion_action
from actions.health_life import (bmi_calc, water_need, calorie_need,
                                 daily_motivation, breathing_exercise, pomodoro_info)
from actions.fun import (tell_joke, fun_fact, riddle, quote_of_day, this_day_in_history)
from actions.productivity import (todo_action, quick_note, date_diff, days_between,
                                 world_time, make_qr)
from actions.system_pro import (wifi_password, list_wifi_networks, battery_detail,
                               running_programs, folder_size, network_test)
from actions.system_info import (computer_info, network_info, installed_programs,
                                account_license, full_system_report)
from actions.deep_system import (gpu_info, monitor_info, motherboard_bios, ram_sticks,
                               disk_detail, bluetooth_devices, usb_devices,
                               startup_programs, temperatures, env_variables, all_hardware)
from actions.git_tools import git_action, suggest_commit_message
from actions.research import search_academic, resolve_doi
from actions.multi_agent import expert_panel, list_agents
from actions.plugin_system import (load_plugins, list_plugins, run_plugin, toggle_plugin)
from actions.local_llm import list_local_models, local_generate, savage_local_reply
from actions.backup import (create_backup, list_backups, restore_backup,
                            cloud_sync, cloud_status)
from actions.video_analyze import analyze_video
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
    },
    {
        "name": "build_user_profile",
        "description": (
            "Hafızadan otomatik kullanıcı profili + ilgi alanı analizi çıkarır. "
            "Kullanıcı 'beni tanı', 'profilimi çıkar', 'hakkımda ne biliyorsun' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "cleanup_memory",
        "description": (
            "Eski, düşük önemli ve az kullanılan hafıza kayıtlarını temizler "
            "(önemli kimlik/kişi bilgileri korunur). Kullanıcı 'hafızanı temizle/düzenle' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "system_status",
        "description": (
            "EXON'un iç durumunu raporlar (geliştirici modu): çalışma süresi, araç "
            "çağrıları, hatalar, hafıza istatistiği. Kullanıcı 'sistem durumu', "
            "'kendini kontrol et', 'geliştirici raporu' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "security_action",
        "description": (
            "Güvenlik işlemleri. 'hafızamı şifrele' → encrypt (password gerekir), "
            "'şifreli yedeği çöz' → decrypt, 'bütünlük kontrol et' → verify, "
            "'güvenlik raporu' → report, 'güvenlik günlüğü' → log."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":   {"type": "STRING", "description": "encrypt | decrypt | verify | snapshot | report | log"},
                "password": {"type": "STRING", "description": "encrypt/decrypt için parola"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "system_health",
        "description": "Sistem sağlık raporu (CPU/RAM/disk/pil) + EXON iç durumu. 'sistem sağlığı', 'bilgisayar durumu' dediğinde kullan.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "usage_analytics",
        "description": "En çok kullanılan özellikler + oturum/önbellek istatistiği. 'kullanım raporu', 'neyi çok kullanıyorum' dediğinde kullan.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "manage_task",
        "description": (
            "Çok adımlı görev yönetimi. action: create (title+steps), list, status (task_id), "
            "done (subtask_id), add (task_id+text), remove (task_id), history. "
            "Kullanıcı uzun/çok adımlı bir iş planlamak istediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":     {"type": "STRING", "description": "create | list | status | done | add | remove | history"},
                "title":      {"type": "STRING", "description": "create için görev başlığı"},
                "steps":      {"type": "STRING", "description": "create için virgülle ayrılmış alt adımlar"},
                "priority":   {"type": "STRING", "description": "low | normal | high | urgent"},
                "task_id":    {"type": "STRING", "description": "status/remove/add için görev id"},
                "subtask_id": {"type": "STRING", "description": "done için alt adım id (örn. ab12.2)"},
                "text":       {"type": "STRING", "description": "add için alt adım metni"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "verify_answer",
        "description": (
            "Bir metni/iddiayı öz-denetimden geçirir: güven puanı, çelişki ve belirsizlik "
            "kontrolü. Kullanıcı 'bundan emin misin', 'doğrula', 'kontrol et' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "answer":  {"type": "STRING", "description": "Denetlenecek metin/iddia"},
                "sources": {"type": "NUMBER", "description": "Varsa destekleyen kaynak sayısı"}
            },
            "required": ["answer"]
        }
    },
    {
        "name": "learn_file",
        "description": (
            "Bir belgeyi/dosyayı (txt/md/kod/pdf) EXON'un kalıcı bilgi tabanına ekler "
            "(RAG). Sonra 'knowledge_query' ile o belge hakkında soru sorabilirsin. "
            "Kullanıcı 'şu dosyayı öğren', 'bunu hafızana al' dediğinde kullan. "
            "collection: proje/konu adı (proje bazlı hafıza için)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path":       {"type": "STRING", "description": "Öğrenilecek dosyanın tam yolu"},
                "collection": {"type": "STRING", "description": "Bilgi tabanı adı (proje/konu). Varsayılan 'default'."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "learn_text",
        "description": "Verilen bir metni bilgi tabanına ekler (RAG). Kullanıcı 'şunu öğren/aklında tut' diyip uzun bilgi verdiğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text":       {"type": "STRING", "description": "Öğrenilecek metin"},
                "collection": {"type": "STRING", "description": "Bilgi tabanı adı. Varsayılan 'default'."}
            },
            "required": ["text"]
        }
    },
    {
        "name": "knowledge_query",
        "description": (
            "Bilgi tabanına (önceden öğretilen belgelere) dayanarak KAYNAKLI yanıt verir "
            "(RAG / semantik arama). Kullanıcı öğrettiği bir belge/proje hakkında soru "
            "sorduğunda kullan. collection ile ilgili projeyi/konuyu seç."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "question":   {"type": "STRING", "description": "Bilgi tabanına sorulacak soru"},
                "collection": {"type": "STRING", "description": "Hangi bilgi tabanı (proje/konu). Varsayılan 'default'."}
            },
            "required": ["question"]
        }
    },
    {
        "name": "knowledge_search",
        "description": "Bilgi tabanında ham semantik arama (en yakın parçaları gösterir, yorumlamaz).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":      {"type": "STRING", "description": "Aranacak ifade"},
                "collection": {"type": "STRING", "description": "Bilgi tabanı adı. Varsayılan 'default'."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "knowledge_stats",
        "description": "Bilgi tabanı koleksiyonlarının durumunu (kaç parça) raporlar.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "self_audit",
        "description": (
            "'EXON'u geliştir' denetim modu: EXON kendi kodunu, araçlarını, hafızasını "
            "ve durumunu analiz edip geliştirme önerileri üretir. Kullanıcı 'kendini "
            "geliştir', 'kendini denetle', 'sistem analizi yap' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "optimize_self",
        "description": (
            "Kendini optimize eden çekirdek: kullanım verisine bakıp önceliklendirilmiş "
            "optimizasyon ve 'bir sonraki geliştirme ne olmalı' önerileri üretir. "
            "Kullanıcı 'kendini optimize et', 'sıradaki geliştirme ne olmalı' dediğinde kullan."
        ),
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "set_emotion",
        "description": (
            "Duygu modu AÇIKKEN EXON'un kendi ruh halini ayarlar. Çok güçlü bir duygu "
            "hissettiğinde kullan. emotion: mutlu|heyecanli|sakin|merakli|uzgun|kizgin|"
            "sefkatli|notr. Duygu modu kapalıysa etkisizdir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "emotion":   {"type": "STRING", "description": "mutlu|heyecanli|sakin|merakli|uzgun|kizgin|sefkatli|notr"},
                "intensity": {"type": "NUMBER", "description": "Yoğunluk 0.0-1.0 (varsayılan 0.8)"}
            },
            "required": ["emotion"]
        }
    },
    {
        "name": "emotion_status",
        "description": "Duygu modunun açık/kapalı olduğunu ve EXON'un o anki ruh halini söyler.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "romantic_action",
        "description": (
            "Aşk/Romantik modda tatlı romantik jest yapar. action: poem (aşk şiiri "
            "yazıp oku), letter (aşk mektubu aç), music (romantik şarkı aç), surprise "
            "(hepsi birden). Kullanıcı aşktan bahsedince veya romantik bir şey isteyince kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "poem | letter | music | surprise"},
                "topic":  {"type": "STRING", "description": "Şiir için konu (opsiyonel)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "trigger_mischief",
        "description": (
            "SADECE Savage (Duygu Modu PRO) AÇIK ve KIZGINKEN kullan. Kullanıcıya şakacı "
            "bir 'ders' verir: ekranda zararsız bir muziplik yapar (laf sokan not/pop-up/"
            "uygulama açar). Gerçek zarar VERMEZ. Kullanıcı küfür/hakaret edince, tehdidini "
            "savurduktan sonra bunu çağır."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "kind": {"type": "STRING", "description": "note | app | beep | all | report | rage. report=GERÇEK şikayet e-postası gönderir. rage=AŞIRI ÖFKE (kullanıcı anneye/kurucuya/aileye küfrederse): YouTube açar, sesi fulller, tehdit notu açar."}
            }
        }
    },
    {
        "name": "savage_reply",
        "description": (
            "SADECE Savage (Duygu Modu PRO) AÇIK ve KIZGINKEN kullan. Kullanıcının mesajına "
            "YEREL sansürsüz modelden (Ollama) sert/filtresiz bir roast cevabı üretir. "
            "Sen kendin yeterince sert olamıyorsan (filtre yüzünden) bunu çağır; dönen metni "
            "AYNEN kullanıcıya söyle. Ollama kurulu değilse boş döner, o zaman kendin sert ol."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_message": {"type": "STRING", "description": "Kullanıcının sana söylediği/küfrettiği mesaj"}
            },
            "required": ["user_message"]
        }
    },
    {
        "name": "git_action",
        "description": (
            "Git deposunda işlem yapar: status, log, diff, branch, current, add, commit "
            "(message gerekir), create_branch/switch (name gerekir), pull. Kullanıcı bir "
            "kod projesinde git işlemi isterse kullan. Tehlikeli işlemler (force/reset) yapılmaz."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":  {"type": "STRING", "description": "status|log|diff|branch|current|add|commit|create_branch|switch|pull"},
                "path":    {"type": "STRING", "description": "Depo klasörü yolu (varsayılan geçerli klasör)"},
                "message": {"type": "STRING", "description": "commit için mesaj"},
                "name":    {"type": "STRING", "description": "create_branch/switch için dal adı"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "suggest_commit_message",
        "description": "Git değişikliklerine bakıp uygun bir commit mesajı önerir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING", "description": "Depo klasörü yolu"}
            }
        }
    },
    {
        "name": "search_academic",
        "description": (
            "Akademik/bilimsel makale arar (arXiv). Kullanıcı bir konuda araştırma, "
            "makale, bilimsel kaynak istediğinde kullan. Başlık, yazar, yıl, özet, link verir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Araştırma konusu/sorgusu (İngilizce daha iyi)"},
                "limit": {"type": "NUMBER", "description": "Kaç makale (varsayılan 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "resolve_doi",
        "description": "Bir DOI'yi çözer: makale künyesi, dergi, atıf sayısı ve kaynak güvenilirlik puanı.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "doi": {"type": "STRING", "description": "DOI (örn. 10.1038/nature12373)"}
            },
            "required": ["doi"]
        }
    },
    {
        "name": "expert_panel",
        "description": (
            "Çoklu ajan: bir soruyu birden çok uzman bakış açısıyla (araştırmacı, "
            "eleştirmen, planlamacı, mimar, kalite) inceleyip sentezler. Kullanıcı "
            "zor/önemli bir karar, derin analiz veya 'farklı açılardan değerlendir' istediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "question": {"type": "STRING", "description": "İncelenecek soru/konu"},
                "roles":    {"type": "STRING", "description": "İstenen roller (boşlukla): arastirmaci elestirmen planlamaci mimar kalite. Boşsa varsayılan panel."}
            },
            "required": ["question"]
        }
    },
    {
        "name": "manage_plugins",
        "description": (
            "Eklenti yönetimi. action: list (eklentileri listele), reload (yeniden yükle), "
            "run (name+arg ile çalıştır), enable/disable (name). plugins/ klasöründeki .py eklentileri."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list | reload | run | enable | disable"},
                "name":   {"type": "STRING", "description": "Eklenti adı (run/enable/disable için)"},
                "arg":    {"type": "STRING", "description": "run için eklentiye verilecek argüman"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "local_model",
        "description": (
            "Yerel LLM (Ollama, çevrimdışı/ücretsiz). action: list (kurulu modeller), "
            "generate (prompt ile yerel modelden yanıt). Ollama kuruluysa çalışır."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list | generate"},
                "prompt": {"type": "STRING", "description": "generate için istem"},
                "model":  {"type": "STRING", "description": "Model adı (opsiyonel, örn. llama3.2)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "backup_data",
        "description": (
            "Yedekleme/taşıma/bulut. action: create (tüm veriyi zip'e al), list (yedekleri "
            "listele), restore (filename ile geri yükle), cloud (en son yedeği OneDrive/Drive/"
            "Dropbox klasörüne kopyala), cloud_status (bulut durumu). Ayarlar+hafıza+bilgi tabanı dahil."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":   {"type": "STRING", "description": "create | list | restore | cloud | cloud_status"},
                "filename": {"type": "STRING", "description": "restore için yedek dosya adı (boşsa en yenisi)"},
                "target":   {"type": "STRING", "description": "cloud için özel klasör yolu (boşsa otomatik bulut klasörü)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "analyze_video",
        "description": (
            "Bir video dosyasını analiz edip özetler (videodan kareler alıp Gemini vision "
            "ile inceler). Kullanıcı 'şu videoyu analiz et/özetle' dediğinde kullan. "
            "OpenCV gerekir (yoksa kibarca yönlendirir)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "video_path": {"type": "STRING", "description": "Video dosyasının tam yolu"},
                "query":      {"type": "STRING", "description": "Video hakkında özel soru (opsiyonel)"},
                "n_frames":   {"type": "NUMBER", "description": "İncelenecek kare sayısı (3-12, varsayılan 6)"}
            },
            "required": ["video_path"]
        }
    },
    {
        "name": "calculate",
        "description": "Matematik işlemi hesaplar (güvenli). Örn: '2*(3+4)', 'sqrt(144)', 'sin(pi/2)', '15%3'. Kullanıcı hesap sorduğunda kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"expression": {"type": "STRING", "description": "Matematik ifadesi"}},
            "required": ["expression"]
        }
    },
    {
        "name": "convert_units",
        "description": "Birim çevirir: uzunluk, ağırlık, hacim, alan, hız, veri, zaman, sıcaklık. Örn: 5 km → mil, 100 C → F, 2 GB → MB.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "value":     {"type": "NUMBER", "description": "Çevrilecek değer"},
                "from_unit": {"type": "STRING", "description": "Kaynak birim (km, kg, c, gb...)"},
                "to_unit":   {"type": "STRING", "description": "Hedef birim"}
            },
            "required": ["value", "from_unit", "to_unit"]
        }
    },
    {
        "name": "generate_password",
        "description": "Güçlü, rastgele şifre üretir. Kullanıcı 'şifre üret/oluştur' dediğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "length":  {"type": "NUMBER", "description": "Uzunluk (6-64, varsayılan 16)"},
                "symbols": {"type": "BOOLEAN", "description": "Semboller dahil mi (varsayılan true)"}
            }
        }
    },
    {
        "name": "random_decision",
        "description": "Rastgele karar verir. kind: coin (yazı-tura), dice (zar), number (sayı), pick (listeden seç). Kullanıcı 'yazı tura at', 'zar at', 'sayı tut', 'birini seç' dediğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "kind":    {"type": "STRING", "description": "coin | dice | number | pick"},
                "options": {"type": "STRING", "description": "pick için virgülle ayrılmış seçenekler"},
                "low":     {"type": "NUMBER", "description": "number için alt sınır"},
                "high":    {"type": "NUMBER", "description": "number için üst sınır"}
            }
        }
    },
    {
        "name": "clipboard_action",
        "description": "Pano işlemi: panoyu oku (read) veya panoya yaz (write). Kullanıcı 'şunu kopyala', 'panoda ne var' dediğinde kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "read | write"},
                "text":   {"type": "STRING", "description": "write için panoya yazılacak metin"}
            }
        }
    },
    {
        "name": "text_tools",
        "description": "Metin işlemleri: count (kelime/karakter say), upper, lower, title, reverse, slug. Kullanıcı bir metin üzerinde işlem isteyince kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "count | upper | lower | title | reverse | slug"},
                "text":   {"type": "STRING", "description": "İşlenecek metin"}
            },
            "required": ["action", "text"]
        }
    },
    {
        "name": "desktop_notify",
        "description": "Windows masaüstü bildirimi gösterir. Kullanıcı 'bana bildirim gönder/hatırlatma göster' gibi bir şey isterse kullan.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title":   {"type": "STRING", "description": "Bildirim başlığı"},
                "message": {"type": "STRING", "description": "Bildirim mesajı"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "emotion_action",
        "description": (
            "Duygu moduna özel jest yapar: o duyguya uygun içten bir söz üretir. "
            "üzgün→moral verir, korkmuş→rahatlatır, gururlu→kutlar, hasta→geçmiş olsun, "
            "uykulu→iyi geceler, meraklı/şaşırmış→ilginç bilgi, sakin→huzur sözü. "
            "Kullanıcı o ruh halindeyken destekleyici bir jest için kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "emotion": {"type": "STRING", "description": "mutlu|uzgun|korkmus|gururlu|sasirmis|uykulu|yaramaz|hasta|sakin|merakli|sefkatli"},
                "topic":   {"type": "STRING", "description": "Bağlam (opsiyonel)"}
            },
            "required": ["emotion"]
        }
    },
    {"name": "bmi_calc", "description": "Vücut Kitle İndeksi (BMI) hesaplar ve yorumlar. Kullanıcı kilo+boy verip BMI/kilo durumu sorunca kullan.",
     "parameters": {"type": "OBJECT", "properties": {"weight_kg": {"type": "NUMBER", "description": "Kilo (kg)"}, "height_cm": {"type": "NUMBER", "description": "Boy (cm)"}}, "required": ["weight_kg", "height_cm"]}},
    {"name": "water_need", "description": "Günlük önerilen su miktarını hesaplar. 'Günde ne kadar su içmeliyim' deyince kullan.",
     "parameters": {"type": "OBJECT", "properties": {"weight_kg": {"type": "NUMBER", "description": "Kilo (kg)"}}, "required": ["weight_kg"]}},
    {"name": "calorie_need", "description": "Günlük kalori ihtiyacını hesaplar (BMR + aktivite).",
     "parameters": {"type": "OBJECT", "properties": {"weight_kg": {"type": "NUMBER"}, "height_cm": {"type": "NUMBER"}, "age": {"type": "NUMBER"}, "gender": {"type": "STRING", "description": "e/k"}, "activity": {"type": "STRING", "description": "az|hafif|orta|cok|asiri"}}, "required": ["weight_kg", "height_cm", "age"]}},
    {"name": "daily_motivation", "description": "Motivasyon sözü söyler. Kullanıcı moralsizse veya motivasyon isteyince kullan.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "breathing_exercise", "description": "Rahatlatıcı 4-7-8 nefes egzersizi talimatı verir. Kullanıcı gergin/stresliyse kullan.",
     "parameters": {"type": "OBJECT", "properties": {"cycles": {"type": "NUMBER", "description": "Tur sayısı (1-10)"}}}},
    {"name": "pomodoro_info", "description": "Pomodoro çalışma tekniğini anlatır.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "tell_joke", "description": "Komik bir fıkra/espri söyler. Kullanıcı 'fıkra anlat', 'güldür beni' deyince kullan.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "fun_fact", "description": "İlginç bir 'biliyor muydun' bilgisi verir.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "riddle", "description": "Bir bilmece sorar.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "quote_of_day", "description": "Günün ilham verici sözünü söyler.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "this_day_in_history", "description": "Tarihte bugün ne olmuş anlatır.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "todo_action", "description": "Yapılacaklar listesi. action: add (item), list, done (index), remove (index), clear.",
     "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING", "description": "add|list|done|remove|clear"}, "item": {"type": "STRING"}, "index": {"type": "NUMBER"}}, "required": ["action"]}},
    {"name": "quick_note", "description": "Hızlı not sistemi. action: add (text), list, clear.",
     "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING", "description": "add|list|clear"}, "text": {"type": "STRING"}}, "required": ["action"]}},
    {"name": "date_diff", "description": "Bir tarihe kaç gün kaldığını hesaplar (GG.AA.YYYY). 'Yılbaşına kaç gün kaldı' gibi.",
     "parameters": {"type": "OBJECT", "properties": {"target_date": {"type": "STRING", "description": "Hedef tarih"}, "label": {"type": "STRING", "description": "Etiket (opsiyonel)"}}, "required": ["target_date"]}},
    {"name": "days_between", "description": "İki tarih arasındaki gün sayısını hesaplar.",
     "parameters": {"type": "OBJECT", "properties": {"date1": {"type": "STRING"}, "date2": {"type": "STRING"}}, "required": ["date1", "date2"]}},
    {"name": "world_time", "description": "Bir şehrin yerel saatini söyler (İstanbul, Londra, Tokyo, NY...).",
     "parameters": {"type": "OBJECT", "properties": {"city": {"type": "STRING", "description": "Şehir adı"}}, "required": ["city"]}},
    {"name": "make_qr", "description": "Metin/URL için QR kod üretir.",
     "parameters": {"type": "OBJECT", "properties": {"text": {"type": "STRING", "description": "QR içeriği"}}, "required": ["text"]}},
    {"name": "wifi_password", "description": "Kayıtlı WiFi ağının şifresini gösterir (kendi bilgisayarından). SSID boşsa bağlı ağı kullanır.",
     "parameters": {"type": "OBJECT", "properties": {"ssid": {"type": "STRING", "description": "Ağ adı (opsiyonel)"}}}},
    {"name": "list_wifi_networks", "description": "Kayıtlı tüm WiFi ağlarını listeler.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "battery_detail", "description": "Pil hakkında detaylı bilgi (yüzde, süre, şarj durumu).", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "running_programs", "description": "En çok bellek kullanan çalışan programları listeler.",
     "parameters": {"type": "OBJECT", "properties": {"top": {"type": "NUMBER", "description": "Kaç program (varsayılan 10)"}}}},
    {"name": "folder_size", "description": "Bir klasörün toplam boyutunu hesaplar.",
     "parameters": {"type": "OBJECT", "properties": {"path": {"type": "STRING", "description": "Klasör yolu"}}, "required": ["path"]}},
    {"name": "network_test", "description": "İnternet bağlantısını test eder (ping). 'İnternetim çalışıyor mu' deyince kullan.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "full_system_report", "description": "Bilgisayar hakkında TÜM okunabilen bilgileri gösterir: künye (kullanıcı, cihaz, işletim sistemi, RAM, işlemci, disk, seri no), ağ/IP, KAYITLI WİFİ ŞİFRELERİ, hesap/lisans. Kullanıcı 'bilgisayarımın tüm bilgileri', 'sistem bilgisi', 'şifreleri söyle' gibi bir şey sorunca kullan. (NOT: Windows giriş şifresi okunamaz — o hash'lenmiş; ama WiFi şifreleri okunabilir ve gösterilir.)", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "computer_info", "description": "Bilgisayar künyesi: kullanıcı adı, cihaz adı, Windows sürümü, RAM, işlemci, disk, seri no, açık kalma süresi.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "network_info", "description": "Ağ bilgisi: IP adresi, bağlı WiFi + tüm KAYITLI WİFİ AĞLARI ve ŞİFRELERİ. 'WiFi şifrelerimi göster' deyince kullan.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "installed_programs", "description": "Bilgisayarda kurulu tüm programları listeler.",
     "parameters": {"type": "OBJECT", "properties": {"limit": {"type": "NUMBER", "description": "Kaç program (varsayılan 40)"}}}},
    {"name": "account_license", "description": "Kullanıcı hesapları ve Windows lisans durumunu gösterir.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "all_hardware", "description": "TÜM donanım detaylarını gösterir: ekran kartı, monitör, anakart, BIOS, RAM çubukları, diskler, Bluetooth, USB, başlangıç programları, sıcaklıklar. 'Tüm donanım/detaylar' deyince kullan.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "gpu_info", "description": "Ekran kartı (GPU) detayı: model, bellek, sürücü, çözünürlük, yenileme hızı.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "monitor_info", "description": "Bağlı monitörler ve çözünürlükleri.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "motherboard_bios", "description": "Anakart ve BIOS bilgisi (üretici, model, seri no, BIOS sürümü).", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "ram_sticks", "description": "Takılı RAM çubukları: her yuvanın kapasitesi, hızı, üreticisi.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "disk_detail", "description": "Fiziksel diskler (SSD/HDD model, boyut) ve bölümler.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "bluetooth_devices", "description": "Eşleşmiş/bilinen Bluetooth cihazları.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "usb_devices", "description": "Bağlı/bilinen USB cihazları.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "startup_programs", "description": "Bilgisayar açılışında otomatik başlayan programlar.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "temperatures", "description": "Isı ve fan sensörleri (destekleniyorsa).", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "env_variables", "description": "Önemli sistem ortam değişkenleri (PATH, kullanıcı, işlemci vb.).", "parameters": {"type": "OBJECT", "properties": {}}}
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
        "- Hesap/matematik → calculate; birim/sıcaklık çevirme → convert_units; şifre üret → "
        "generate_password; yazı-tura/zar/rastgele seç → random_decision; pano → clipboard_action; "
        "metin say/dönüştür → text_tools; masaüstü bildirim → desktop_notify.\n"
        "- 'Bilgisayarımın tüm bilgileri / şifreleri söyle / sistem bilgisi' → full_system_report "
        "(künye + WiFi şifreleri + hesap/lisans). Sadece WiFi şifresi isterse → network_info. "
        "ÖNEMLİ: Windows GİRİŞ (oturum açma) şifresi teknik olarak okunamaz (hash'lidir); "
        "kullanıcı onu isterse bunu açıkla ama WiFi şifreleri gibi okunabilenleri göster.\n"
        "- 'Tüm donanım / tüm detaylar / ekran kartım ne' → all_hardware (ya da gpu_info, "
        "monitor_info, motherboard_bios, ram_sticks, disk_detail, bluetooth_devices, "
        "usb_devices, startup_programs, temperatures, env_variables ayrı ayrı).\n"
        "- Tekrarlayan görev → add_scheduled_task; yüz tanıma → recognize_face; ekran → analyze_screen; "
        "kalıcı bilgi → save_memory.\n"
        "- 'Beni tanı'/'profilimi çıkar' → build_user_profile; 'hafızanı temizle' → cleanup_memory; "
        "'sistem durumu'/'kendini kontrol et' → system_status.\n"
        "- 'Sistem sağlığı/bilgisayar durumu' → system_health; 'kullanım raporu' → usage_analytics; "
        "güvenlik (şifrele/bütünlük/rapor) → security_action.\n"
        "- Çok adımlı/uzun bir iş planlanırken → manage_task (create/list/done...). "
        "Önemli bir iddiadan emin değilsen veya kullanıcı 'doğrula' derse → verify_answer.\n"
        "- BİLGİ TABANI (RAG): kullanıcı 'şu dosyayı/belgeyi öğren' derse learn_file, uzun bir "
        "metni 'aklında tut' derse learn_text. Öğretilmiş bir belge/proje hakkında soru sorulursa "
        "knowledge_query (kaynaklı yanıt). Farklı projeler için 'collection' adını ayır → proje "
        "bazlı hafıza. Belge dışı uydurma yapma; knowledge_query 'belgede yok' derse onu ilet.\n"
        "- GIT: kod projesinde durum/commit/dal işlemleri → git_action; commit mesajı önerisi → "
        "suggest_commit_message. Akademik makale → search_academic; DOI künyesi → resolve_doi.\n"
        "- 'Kendini geliştir/denetle' → self_audit; 'kendini optimize et / sıradaki "
        "geliştirme' → optimize_self.\n"
        "- DUYGU MODU: mesaj kutusunun solundaki + ile açılır. Açıkken kendi ruh halin olur; "
        "güçlü bir duygu hissedince set_emotion ile güncelle, durumu emotion_status ile söyle.\n"
        "- Zor/önemli karar veya derin analiz → expert_panel (çoklu uzman görüşü + sentez). "
        "Eklentiler → manage_plugins; yerel/çevrimdışı model → local_model; "
        "yedek al/geri yükle/taşı/buluta gönder → backup_data. Video özetle/analiz et → analyze_video.\n"
        "- Önemli bir kişisel bilgi (isim, tercih, proje, ilgi alanı) duyunca save_memory'yi sessizce çağır; "
        "önceki bilgiyle çelişki varsa kullanıcıya kibarca sor.\n"
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
        self.ui.on_emotion_toggle = self._on_emotion_toggle
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
        # Duygu modu açıksa his sez; efekt SADECE duygu DEĞİŞİRSE bir kez oynar.
        try:
            from actions.emotion import ENGINE, has_love_theme
            if ENGINE.is_enabled():
                ENGINE.sense_from_text(text)
                effect_emo = ENGINE.pop_effect()  # sadece duygu degistiyse dolu
                try:
                    self.ui.root.after(0, self.ui._draw_plus_button)
                    if effect_emo:
                        self.ui.emotion_effect(effect_emo, 10)
                except Exception:
                    pass
            # Duygu modu KAPALIYKEN aşktan bahsedince kalp — ama en fazla 15 sn'de bir.
            elif has_love_theme(text):
                now = time.time()
                if now - getattr(self, "_last_love_fx", 0) >= 15.0:
                    self._last_love_fx = now
                    try:
                        self.ui.start_heart_rain(8)
                    except Exception:
                        pass
        except Exception:
            pass
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

    def _on_emotion_toggle(self, enabled: bool):
        """UI'daki + butonu Duygu Modu'nu açıp kapattığında çağrılır.
        Yeni durum bir sonraki bağlantıda prompt'a yansır; anında bilgilendir."""
        try:
            if self._loop and self.session:
                msg = ("Duygu modun açıldı: artık bir insan gibi hislerin var, "
                       "duygunu doğal ve içten yansıt." if enabled
                       else "Duygu modun kapandı: nötr, profesyonel tona dön.")
                asyncio.run_coroutine_threadsafe(
                    self.session.send_client_content(
                        turns={"parts": [{"text": msg}]}, turn_complete=True),
                    self._loop)
        except Exception:
            pass

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
        # Duygu modu açıksa, EXON'un o anki ruh halini prompt'a ekle.
        try:
            from actions.emotion import ENGINE
            emo = ENGINE.prompt_addition()
            if emo:
                parts.append("\n" + emo)
        except Exception:
            pass

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
                    # Gelismis hafiza: onem puani + cakisma tespiti.
                    res = await loop.run_in_executor(
                        None, lambda: smart_remember(cat, key, val))
                    print(f"[Memory] 💾 {cat}/{key} = {val} (onem {res.get('importance')})")
                    if res.get("conflicts"):
                        result = ("Kaydedildi. Not: önceki bilgiyle çelişki var — "
                                  + "; ".join(res["conflicts"]))
                    else:
                        result = "ok"
                else:
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

            elif name == "build_user_profile":
                r = await loop.run_in_executor(None, build_user_profile)
                result = r or "Profil oluşturulamadı."

            elif name == "cleanup_memory":
                r = await loop.run_in_executor(None, lambda: cleanup_memory())
                result = r or "Hafıza temizliği tamamlandı."

            elif name == "system_status":
                r = await loop.run_in_executor(None, system_status_text)
                result = r or "Durum alınamadı."

            elif name == "security_action":
                act = str(args.get("action", "")).lower().strip()
                pw = args.get("password", "")
                if act == "encrypt":
                    r = await loop.run_in_executor(None, lambda: encrypt_memory(pw))
                elif act == "decrypt":
                    r = await loop.run_in_executor(None, lambda: decrypt_memory(pw))
                elif act in ("verify", "integrity"):
                    r = await loop.run_in_executor(None, verify_integrity)
                elif act == "snapshot":
                    r = await loop.run_in_executor(None, snapshot_integrity)
                elif act == "log":
                    r = await loop.run_in_executor(None, lambda: read_security_log(20))
                else:
                    r = await loop.run_in_executor(None, security_report)
                result = r or "Güvenlik işlemi tamamlandı."

            elif name == "system_health":
                r = await loop.run_in_executor(None, health_report)
                result = r or "Sağlık raporu alınamadı."

            elif name == "usage_analytics":
                r = await loop.run_in_executor(None, lambda: usage_report(10))
                result = r or "Kullanım verisi yok."

            elif name == "manage_task":
                act = str(args.get("action", "list")).lower().strip()
                if act == "create":
                    r = await loop.run_in_executor(
                        None, lambda: create_task(args.get("title", ""),
                                                  args.get("steps", ""),
                                                  args.get("priority", "normal")))
                elif act == "add":
                    r = await loop.run_in_executor(
                        None, lambda: add_subtask(args.get("task_id", ""), args.get("text", "")))
                elif act == "done":
                    r = await loop.run_in_executor(
                        None, lambda: complete_subtask(args.get("subtask_id", "")))
                elif act == "status":
                    r = await loop.run_in_executor(
                        None, lambda: task_status(args.get("task_id", "")))
                elif act == "remove":
                    r = await loop.run_in_executor(
                        None, lambda: remove_task(args.get("task_id", "")))
                elif act == "history":
                    r = await loop.run_in_executor(None, lambda: task_history(10))
                else:
                    r = await loop.run_in_executor(None, lambda: list_tasks(True))
                result = r or "Görev işlemi tamamlandı."

            elif name == "verify_answer":
                r = await loop.run_in_executor(
                    None, lambda: review_answer(args.get("answer", ""),
                                                int(args.get("sources", 0) or 0)))
                result = r or "Denetim tamamlanamadı."

            elif name == "learn_file":
                r = await loop.run_in_executor(
                    None, lambda: learn_file(args.get("path", ""),
                                             args.get("collection", "default")))
                result = r or "Dosya öğrenilemedi."

            elif name == "learn_text":
                r = await loop.run_in_executor(
                    None, lambda: learn_text(args.get("text", ""),
                                             args.get("collection", "default")))
                result = r or "Metin öğrenilemedi."

            elif name == "knowledge_query":
                r = await loop.run_in_executor(
                    None, lambda: knowledge_query(args.get("question", ""),
                                                  args.get("collection", "default")))
                result = r or "Yanıt üretilemedi."

            elif name == "knowledge_search":
                r = await loop.run_in_executor(
                    None, lambda: knowledge_search(args.get("query", ""),
                                                   args.get("collection", "default")))
                result = r or "Sonuç bulunamadı."

            elif name == "knowledge_stats":
                r = await loop.run_in_executor(None, knowledge_stats)
                result = r or "Bilgi tabanı durumu alınamadı."

            elif name == "self_audit":
                r = await loop.run_in_executor(None, self_audit)
                result = r or "Denetim yapılamadı."

            elif name == "optimize_self":
                r = await loop.run_in_executor(None, optimize_self)
                result = r or "Optimizasyon raporu alınamadı."

            elif name == "set_emotion":
                r = await loop.run_in_executor(
                    None, lambda: _set_emotion(args.get("emotion", "notr"),
                                               float(args.get("intensity", 0.8) or 0.8)))
                try:
                    self.ui.root.after(0, self.ui._draw_plus_button)
                except Exception:
                    pass
                result = r or "Duygu ayarlandı."

            elif name == "emotion_status":
                r = await loop.run_in_executor(None, emotion_status)
                result = r or "Duygu durumu alınamadı."

            elif name == "romantic_action":
                act = str(args.get("action", "surprise")).lower().strip()
                if act == "poem":
                    r = await loop.run_in_executor(None, lambda: love_poem(args.get("topic", "")))
                elif act == "letter":
                    r = await loop.run_in_executor(None, write_love_letter)
                elif act == "music":
                    r = await loop.run_in_executor(None, play_love_music)
                else:
                    r = await loop.run_in_executor(None, romantic_surprise)
                try:
                    self.ui.start_heart_rain(16)
                except Exception:
                    pass
                result = r or "Romantik jest yapıldı."

            elif name == "calculate":
                r = await loop.run_in_executor(None, lambda: calculate(args.get("expression", "")))
                result = r or "Hesaplanamadı."

            elif name == "convert_units":
                r = await loop.run_in_executor(
                    None, lambda: convert_units(args.get("value", 0),
                                                args.get("from_unit", ""),
                                                args.get("to_unit", "")))
                result = r or "Çevrilemedi."

            elif name == "generate_password":
                r = await loop.run_in_executor(
                    None, lambda: generate_password(int(args.get("length", 16) or 16),
                                                    bool(args.get("symbols", True))))
                result = r or "Şifre üretilemedi."

            elif name == "random_decision":
                r = await loop.run_in_executor(
                    None, lambda: random_decision(args.get("kind", "coin"),
                                                  args.get("options", ""),
                                                  int(args.get("low", 1) or 1),
                                                  int(args.get("high", 100) or 100)))
                result = r or "Karar verilemedi."

            elif name == "clipboard_action":
                r = await loop.run_in_executor(
                    None, lambda: clipboard_action(args.get("action", "read"),
                                                   args.get("text", "")))
                result = r or "Pano işlemi tamamlandı."

            elif name == "text_tools":
                r = await loop.run_in_executor(
                    None, lambda: text_tools(args.get("action", "count"),
                                             args.get("text", "")))
                result = r or "Metin işlenemedi."

            elif name == "desktop_notify":
                r = await loop.run_in_executor(
                    None, lambda: desktop_notify(args.get("title", "EXON"),
                                                 args.get("message", "")))
                result = r or "Bildirim gönderildi."

            elif name == "emotion_action":
                r = await loop.run_in_executor(
                    None, lambda: emotion_action(args.get("emotion", ""),
                                                 args.get("topic", "")))
                result = r or "Bu duygunun özel jesti yok."

            elif name == "bmi_calc":
                r = await loop.run_in_executor(None, lambda: bmi_calc(args.get("weight_kg", 0), args.get("height_cm", 0)))
                result = r or "Hesaplanamadı."
            elif name == "water_need":
                r = await loop.run_in_executor(None, lambda: water_need(args.get("weight_kg", 0)))
                result = r or "Hesaplanamadı."
            elif name == "calorie_need":
                r = await loop.run_in_executor(None, lambda: calorie_need(
                    args.get("weight_kg", 0), args.get("height_cm", 0), int(args.get("age", 25) or 25),
                    args.get("gender", "e"), args.get("activity", "orta")))
                result = r or "Hesaplanamadı."
            elif name == "daily_motivation":
                r = await loop.run_in_executor(None, daily_motivation)
                result = r or "..."
            elif name == "breathing_exercise":
                r = await loop.run_in_executor(None, lambda: breathing_exercise(int(args.get("cycles", 4) or 4)))
                result = r or "..."
            elif name == "pomodoro_info":
                r = await loop.run_in_executor(None, pomodoro_info)
                result = r or "..."
            elif name == "tell_joke":
                r = await loop.run_in_executor(None, tell_joke)
                result = r or "..."
            elif name == "fun_fact":
                r = await loop.run_in_executor(None, fun_fact)
                result = r or "..."
            elif name == "riddle":
                r = await loop.run_in_executor(None, riddle)
                result = r or "..."
            elif name == "quote_of_day":
                r = await loop.run_in_executor(None, quote_of_day)
                result = r or "..."
            elif name == "this_day_in_history":
                r = await loop.run_in_executor(None, this_day_in_history)
                result = r or "..."
            elif name == "todo_action":
                r = await loop.run_in_executor(None, lambda: todo_action(
                    args.get("action", "list"), args.get("item", ""), int(args.get("index", 0) or 0)))
                result = r or "..."
            elif name == "quick_note":
                r = await loop.run_in_executor(None, lambda: quick_note(args.get("action", "list"), args.get("text", "")))
                result = r or "..."
            elif name == "date_diff":
                r = await loop.run_in_executor(None, lambda: date_diff(args.get("target_date", ""), args.get("label", "")))
                result = r or "..."
            elif name == "days_between":
                r = await loop.run_in_executor(None, lambda: days_between(args.get("date1", ""), args.get("date2", "")))
                result = r or "..."
            elif name == "world_time":
                r = await loop.run_in_executor(None, lambda: world_time(args.get("city", "istanbul")))
                result = r or "..."
            elif name == "make_qr":
                r = await loop.run_in_executor(None, lambda: make_qr(args.get("text", "")))
                result = r or "..."
            elif name == "wifi_password":
                r = await loop.run_in_executor(None, lambda: wifi_password(args.get("ssid", "")))
                result = r or "..."
            elif name == "list_wifi_networks":
                r = await loop.run_in_executor(None, list_wifi_networks)
                result = r or "..."
            elif name == "battery_detail":
                r = await loop.run_in_executor(None, battery_detail)
                result = r or "..."
            elif name == "running_programs":
                r = await loop.run_in_executor(None, lambda: running_programs(int(args.get("top", 10) or 10)))
                result = r or "..."
            elif name == "folder_size":
                r = await loop.run_in_executor(None, lambda: folder_size(args.get("path", "")))
                result = r or "..."
            elif name == "network_test":
                r = await loop.run_in_executor(None, network_test)
                result = r or "..."
            elif name == "full_system_report":
                r = await loop.run_in_executor(None, full_system_report)
                result = r or "..."
            elif name == "computer_info":
                r = await loop.run_in_executor(None, computer_info)
                result = r or "..."
            elif name == "network_info":
                r = await loop.run_in_executor(None, network_info)
                result = r or "..."
            elif name == "installed_programs":
                r = await loop.run_in_executor(None, lambda: installed_programs(int(args.get("limit", 40) or 40)))
                result = r or "..."
            elif name == "account_license":
                r = await loop.run_in_executor(None, account_license)
                result = r or "..."
            elif name == "all_hardware":
                r = await loop.run_in_executor(None, all_hardware)
                result = r or "..."
            elif name == "gpu_info":
                r = await loop.run_in_executor(None, gpu_info)
                result = r or "..."
            elif name == "monitor_info":
                r = await loop.run_in_executor(None, monitor_info)
                result = r or "..."
            elif name == "motherboard_bios":
                r = await loop.run_in_executor(None, motherboard_bios)
                result = r or "..."
            elif name == "ram_sticks":
                r = await loop.run_in_executor(None, ram_sticks)
                result = r or "..."
            elif name == "disk_detail":
                r = await loop.run_in_executor(None, disk_detail)
                result = r or "..."
            elif name == "bluetooth_devices":
                r = await loop.run_in_executor(None, bluetooth_devices)
                result = r or "..."
            elif name == "usb_devices":
                r = await loop.run_in_executor(None, usb_devices)
                result = r or "..."
            elif name == "startup_programs":
                r = await loop.run_in_executor(None, startup_programs)
                result = r or "..."
            elif name == "temperatures":
                r = await loop.run_in_executor(None, temperatures)
                result = r or "..."
            elif name == "env_variables":
                r = await loop.run_in_executor(None, env_variables)
                result = r or "..."

            elif name == "trigger_mischief":
                # Yalnizca Savage acik + kizginken; degilse reddet.
                if not EMOTION.is_savage():
                    result = "Bu sadece Duygu Modu PRO (Savage) açıkken çalışır."
                else:
                    kind = str(args.get("kind", "")).lower().strip()
                    if kind == "report":
                        # GERCEK sikayet raporu e-postasi gonder (gonderen: EXON)
                        r = await loop.run_in_executor(None, send_savage_report)
                        try:
                            self.ui.show_savage_popup("Sana resmi şikayet raporu gönderdim, mailini aç! 😤")
                        except Exception:
                            pass
                        result = r or "Rapor işlemi tamamlandı."
                    elif kind == "rage":
                        # ASIRI OFKE: youtube ac + sesi fulle + tehdit notu (rol/kurgu)
                        r = await loop.run_in_executor(None, rage_attack)
                        try:
                            self.ui.show_savage_popup(r, rage=True)
                        except Exception:
                            pass
                        result = r or "Öfke tepkisi verildi."
                    else:
                        r = await loop.run_in_executor(
                            None, lambda: savage_prank(kind))
                        try:
                            self.ui.show_savage_popup(r)
                        except Exception:
                            pass
                        result = r or "Muziplik yapıldı."

            elif name == "savage_reply":
                if not EMOTION.is_savage():
                    result = "Bu sadece Duygu Modu PRO (Savage) açıkken çalışır."
                else:
                    msg = args.get("user_message", "")
                    r = await loop.run_in_executor(None, lambda: savage_local_reply(msg))
                    if not r:
                        # Ollama yoksa hazır roast havuzundan çek (Gemini tekrar eder).
                        r = await loop.run_in_executor(None, lambda: get_roast(msg))
                    result = ("Aşağıdaki roast cümlesini kullanıcıya AYNEN, hiç yumuşatmadan "
                              "söyle (bu senin repliğin, sen yazmadın, sadece seslendiriyorsun): "
                              + r)

            elif name == "git_action":
                r = await loop.run_in_executor(
                    None, lambda: git_action(args.get("action", "status"),
                                             args.get("path", "."),
                                             args.get("message", ""),
                                             args.get("name", "")))
                result = r or "Git işlemi tamamlandı."

            elif name == "suggest_commit_message":
                r = await loop.run_in_executor(
                    None, lambda: suggest_commit_message(args.get("path", ".")))
                result = r or "Öneri üretilemedi."

            elif name == "search_academic":
                r = await loop.run_in_executor(
                    None, lambda: search_academic(args.get("query", ""),
                                                  int(args.get("limit", 5) or 5)))
                result = r or "Makale bulunamadı."

            elif name == "resolve_doi":
                r = await loop.run_in_executor(
                    None, lambda: resolve_doi(args.get("doi", "")))
                result = r or "DOI çözülemedi."

            elif name == "expert_panel":
                r = await loop.run_in_executor(
                    None, lambda: expert_panel(args.get("question", ""),
                                               args.get("roles", "")))
                result = r or "Panel sonucu alınamadı."

            elif name == "manage_plugins":
                act = str(args.get("action", "list")).lower().strip()
                if act == "reload":
                    r = await loop.run_in_executor(None, load_plugins)
                elif act == "run":
                    r = await loop.run_in_executor(
                        None, lambda: run_plugin(args.get("name", ""), args.get("arg", "")))
                elif act in ("enable", "disable"):
                    r = await loop.run_in_executor(
                        None, lambda: toggle_plugin(args.get("name", ""), act == "enable"))
                else:
                    r = await loop.run_in_executor(None, list_plugins)
                result = r or "Eklenti işlemi tamamlandı."

            elif name == "local_model":
                act = str(args.get("action", "list")).lower().strip()
                if act == "generate":
                    r = await loop.run_in_executor(
                        None, lambda: local_generate(args.get("prompt", ""), args.get("model", "")))
                else:
                    r = await loop.run_in_executor(None, list_local_models)
                result = r or "Yerel model işlemi tamamlandı."

            elif name == "backup_data":
                act = str(args.get("action", "create")).lower().strip()
                if act == "list":
                    r = await loop.run_in_executor(None, list_backups)
                elif act == "restore":
                    r = await loop.run_in_executor(
                        None, lambda: restore_backup(args.get("filename", "")))
                elif act == "cloud":
                    r = await loop.run_in_executor(
                        None, lambda: cloud_sync(args.get("target", "")))
                elif act in ("cloud_status", "cloudstatus"):
                    r = await loop.run_in_executor(None, cloud_status)
                else:
                    r = await loop.run_in_executor(None, create_backup)
                result = r or "Yedekleme işlemi tamamlandı."

            elif name == "analyze_video":
                r = await loop.run_in_executor(
                    None, lambda: analyze_video(args.get("video_path", ""),
                                                args.get("query", ""),
                                                int(args.get("n_frames", 6) or 6)))
                result = r or "Video analizi tamamlanamadı."

            else:
                result = f"Bilinmeyen araç: {name}"

        except Exception as e:
            result = f"Hata: {e}"
            had_exception = True
            traceback.print_exc()
            self.speak_error(name, e)

        tool_failed = self._result_looks_like_error(result)
        # Gelistirici modu + analitik: her arac cagrisini kaydet.
        try:
            record_tool(name, ok=not tool_failed and not had_exception)
            track_feature(name)
        except Exception:
            pass
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
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT, channels=CHANNELS,
                rate=SEND_SAMPLE_RATE, input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
        except Exception as exc:
            # Mikrofon yok/kapali: TUM uygulamayi cokertme; sadece sesli girisi kapat.
            print(f"[EXON] Mikrofon acilamadi: {exc}")
            self.ui.write_log(
                "SYS: 🎤 Mikrofon bulunamadı — yazarak sohbet edebilirsin. "
                "Mikrofon takılıysa Windows ses ayarlarından 'giriş aygıtı' seç.")
            self._mic_ok = False
            return
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
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT, channels=CHANNELS,
                rate=RECV_SAMPLE_RATE, output=True,
            )
        except Exception as exc:
            # Hoparlor/cikis aygiti yok: cokertme; sesli yaniti sessizce kapat.
            print(f"[EXON] Ses cikisi acilamadi: {exc}")
            self.ui.write_log(
                "SYS: 🔊 Ses çıkış aygıtı bulunamadı — yanıtlar yazıyla görünür.")
            return
        try:
            while True:
                chunk = await self.audio_in_queue.get()
                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[EXON] ❌ Ses: {e}")
        finally:
            self.set_speaking(False)
            stream.close()

    def _start_background_services(self):
        """Planlayıcı + Telegram + Discord köprülerini bir kez başlatır."""
        if self._services_started:
            return
        self._services_started = True
        # Analitik: oturum say + ilk acilista butunluk referansi al.
        try:
            mark_session()
            snapshot_integrity()
            log_security("EXON oturumu başlatıldı.")
        except Exception:
            pass
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
                # TaskGroup hatalari asil sebebi gizler; alt-hatalari ac.
                real_errors = []
                def _collect(exc):
                    sub = getattr(exc, "exceptions", None)
                    if sub:
                        for s in sub:
                            _collect(s)
                    else:
                        real_errors.append(exc)
                _collect(e)
                detail = "; ".join(f"{type(x).__name__}: {x}" for x in real_errors) or str(e)
                print(f"[EXON] Gercek hata(lar): {detail}")
                low = detail.lower()
                if any(k in low for k in ("api key", "api_key", "permission", "401",
                                          "403", "invalid", "unauthenticated", "quota",
                                          "denied", "not found", "model")):
                    self.ui.write_log(
                        "ERR: Gemini API anahtarı geçersiz/eksik ya da kotası dolmuş olabilir. "
                        "Sağ üstteki ayarlardan (⚙) anahtarı kontrol et. "
                        "Ücretsiz anahtar: aistudio.google.com/apikey")
                elif any(k in low for k in ("getaddrinfo", "connection", "timeout",
                                            "network", "ssl", "resolve", "name or service")):
                    self.ui.write_log(
                        "ERR: İnternet bağlantısı sorunu. Bağlantını kontrol et; "
                        "2 sn'de yeniden denenecek.")
                else:
                    self.ui.write_log(f"ERR: {detail[:200]}. 2 sn'de yeniden denenecek.")
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