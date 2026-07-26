"""
Gelismis Sistem paketi — wifi sifre, pil detay, calisan programlar, klasor boyutu.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition
Cogu Windows komutlari (netsh, wmic) + psutil. Salt-okunur/guvenli.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _run(args, shell=False) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, shell=shell,
                           timeout=20, creationflags=_NOWIN)
        return ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as exc:
        return f"(hata: {exc})"


def wifi_password(ssid: str = "") -> str:
    """Kayitli WiFi aginin sifresini gosterir (kendi bilgisayarindaki kayittan)."""
    if os.name != "nt":
        return "Bu özellik Windows'ta çalışır."
    ssid = (ssid or "").strip()
    if not ssid:
        # Once mevcut agi bul
        out = _run(["netsh", "wlan", "show", "interfaces"])
        for line in out.splitlines():
            low = line.lower()
            if "ssid" in low and "bssid" not in low and ":" in line:
                ssid = line.split(":", 1)[1].strip()
                break
        if not ssid:
            return "Bağlı bir WiFi bulamadım. Ağ adını (SSID) belirt."
    out = _run(["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"])
    for line in out.splitlines():
        if "anahtar" in line.lower() or "key content" in line.lower():
            if ":" in line:
                pw = line.split(":", 1)[1].strip()
                return f"📶 '{ssid}' WiFi şifresi: {pw}"
    return f"'{ssid}' için şifre bulunamadı (kayıtlı olmayabilir veya yönetici gerekebilir)."


def list_wifi_networks() -> str:
    """Kayitli tum WiFi profillerini listeler."""
    if os.name != "nt":
        return "Bu özellik Windows'ta çalışır."
    out = _run(["netsh", "wlan", "show", "profiles"])
    nets = []
    for line in out.splitlines():
        if ":" in line and ("profil" in line.lower() or "profile" in line.lower()):
            n = line.split(":", 1)[1].strip()
            if n:
                nets.append(n)
    if not nets:
        return "Kayıtlı WiFi ağı bulunamadı."
    return "📶 Kayıtlı WiFi ağları:\n" + "\n".join(f"  • {n}" for n in nets[:30])


def battery_detail() -> str:
    """Pil hakkinda detayli bilgi."""
    try:
        import psutil
        b = psutil.sensors_battery()
        if not b:
            return "Pil bilgisi yok (masaüstü olabilir)."
        state = "🔌 Şarjda" if b.power_plugged else "🔋 Prizde değil"
        line = f"Pil: %{b.percent:.0f} — {state}"
        if b.secsleft and b.secsleft > 0 and not b.power_plugged:
            h, m = divmod(b.secsleft // 60, 60)
            line += f"\nKalan süre: ~{h} saat {m} dakika"
        if b.percent <= 20 and not b.power_plugged:
            line += "\n⚠️ Pil düşük, şarja takmayı düşün."
        return line
    except Exception as exc:
        return f"Pil bilgisi alınamadı: {exc}"


def running_programs(top: int = 10) -> str:
    """En cok bellek kullanan calisan programlari listeler."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["name", "memory_info"]):
            try:
                mem = p.info["memory_info"].rss if p.info.get("memory_info") else 0
                nm = p.info.get("name") or "?"
                procs.append((mem, nm))
            except Exception:
                continue
        # ayni isimleri birlestir
        agg = {}
        for mem, nm in procs:
            agg[nm] = agg.get(nm, 0) + mem
        top_list = sorted(agg.items(), key=lambda kv: -kv[1])[:max(1, min(int(top or 10), 20))]
        lines = ["🖥️ En çok bellek kullanan programlar:"]
        for nm, mem in top_list:
            lines.append(f"  • {nm}: {mem // (1024*1024)} MB")
        return "\n".join(lines)
    except Exception as exc:
        return f"Program listesi alınamadı: {exc}"


def folder_size(path: str = "") -> str:
    """Bir klasorun toplam boyutunu hesaplar."""
    path = (path or "").strip().strip('"')
    if not path:
        return "Bir klasör yolu ver."
    p = Path(path).expanduser()
    if not p.exists():
        return f"Klasör bulunamadı: {path}"
    if p.is_file():
        return f"{p.name}: {p.stat().st_size // 1024} KB"
    total = 0
    count = 0
    try:
        for f in p.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                    count += 1
                except Exception:
                    pass
                if count > 200000:  # cok buyukse dur
                    break
    except Exception as exc:
        return f"Boyut hesaplanamadı: {exc}"
    if total > 1024**3:
        size = f"{total / 1024**3:.2f} GB"
    elif total > 1024**2:
        size = f"{total / 1024**2:.1f} MB"
    else:
        size = f"{total / 1024:.0f} KB"
    return f"📁 {p.name}: {size} ({count} dosya)"


def network_test() -> str:
    """Basit internet baglanti/hiz teshisi (ping)."""
    if os.name == "nt":
        out = _run(["ping", "-n", "4", "8.8.8.8"])
    else:
        out = _run(["ping", "-c", "4", "8.8.8.8"])
    # ortalama gecikmeyi bul
    import re
    m = re.search(r"[Oo]rtalama\s*=\s*(\d+)ms|[Aa]verage\s*=\s*(\d+)ms|avg[^\d]*([\d.]+)", out)
    if "TTL" in out or "ttl" in out or "bytes from" in out:
        ms = ""
        if m:
            ms = next((g for g in m.groups() if g), "")
        return f"🌐 İnternet BAĞLI ✓" + (f" (ortalama gecikme ~{ms} ms)" if ms else "")
    return "🌐 İnternet bağlantısı YOK veya çok yavaş. Bağlantını kontrol et."
