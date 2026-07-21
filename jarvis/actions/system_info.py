"""
Sistem Bilgi Karti — bilgisayar hakkinda GERCEKTEN okunabilen tum bilgiler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

ONEMLI: Windows GIRIS sifresi OKUNAMAZ (Windows onu hash olarak saklar, geri
donusturulemez). Ama WiFi sifreleri OKUNABILIR (geri donusturulebilir saklanir).
Bu modul: kunye, ag/IP, WiFi sifreleri, kurulu program, lisans, hesap bilgisi.
Salt-okunur, hicbir sey degistirmez.
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess

_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _run(args, shell=False) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, shell=shell,
                           timeout=25, creationflags=_NOWIN)
        return ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception:
        return ""


# ── Bilgisayar kunyesi ───────────────────────────────────────────────────────
def computer_info() -> str:
    lines = ["🖥️ [BİLGİSAYAR KÜNYESİ]"]
    try:
        import getpass
        lines.append(f"Kullanıcı adı : {getpass.getuser()}")
    except Exception:
        pass
    try:
        lines.append(f"Cihaz adı     : {socket.gethostname()}")
    except Exception:
        pass
    lines.append(f"İşletim sist. : {platform.system()} {platform.release()} ({platform.version()})")
    lines.append(f"Mimari        : {platform.machine()}")
    proc = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "?")
    lines.append(f"İşlemci       : {proc}")
    try:
        import psutil
        ram = psutil.virtual_memory()
        lines.append(f"RAM           : {ram.total // (1024**3)} GB (kullanım %{ram.percent:.0f})")
        cores = psutil.cpu_count(logical=True)
        lines.append(f"Çekirdek      : {cores} (mantıksal)")
        try:
            disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
            lines.append(f"Disk (C:)     : {disk.total // (1024**3)} GB, boş {disk.free // (1024**3)} GB")
        except Exception:
            pass
        import time as _t
        up = int(_t.time() - psutil.boot_time())
        h, rem = divmod(up, 3600); m, _ = divmod(rem, 60)
        lines.append(f"Açık süre     : {h} saat {m} dakika")
        batt = psutil.sensors_battery()
        if batt:
            lines.append(f"Pil           : %{batt.percent:.0f}" + (" (şarjda)" if batt.power_plugged else ""))
    except Exception:
        pass
    # Windows seri no / model
    if os.name == "nt":
        model = _run(["wmic", "computersystem", "get", "manufacturer,model"], shell=True)
        if model:
            parts = [l.strip() for l in model.splitlines() if l.strip() and "Manufacturer" not in l]
            if parts:
                lines.append(f"Model         : {parts[0]}")
        serial = _run(["wmic", "bios", "get", "serialnumber"], shell=True)
        if serial:
            sp = [l.strip() for l in serial.splitlines() if l.strip() and "SerialNumber" not in l]
            if sp:
                lines.append(f"Seri no       : {sp[0]}")
    return "\n".join(lines)


# ── Ag & WiFi (WiFi sifreleri DAHIL) ─────────────────────────────────────────
def network_info() -> str:
    lines = ["🌐 [AĞ & WIFI BİLGİSİ]"]
    # IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        lines.append(f"Yerel IP      : {local_ip}")
    except Exception:
        try:
            lines.append(f"Yerel IP      : {socket.gethostbyname(socket.gethostname())}")
        except Exception:
            pass
    if os.name != "nt":
        lines.append("(WiFi şifreleri yalnızca Windows'ta okunabilir.)")
        return "\n".join(lines)
    # Bagli WiFi
    iface = _run(["netsh", "wlan", "show", "interfaces"])
    cur_ssid = ""
    for line in iface.splitlines():
        low = line.lower()
        if "ssid" in low and "bssid" not in low and ":" in line:
            cur_ssid = line.split(":", 1)[1].strip()
            lines.append(f"Bağlı WiFi    : {cur_ssid}")
            break
    # Kayitli tum WiFi + sifreleri
    profiles = _run(["netsh", "wlan", "show", "profiles"])
    names = []
    for line in profiles.splitlines():
        if ":" in line and ("profil" in line.lower() or "profile" in line.lower()):
            n = line.split(":", 1)[1].strip()
            if n:
                names.append(n)
    if names:
        lines.append("\n📶 Kayıtlı WiFi ağları ve şifreleri:")
        for n in names[:25]:
            detail = _run(["netsh", "wlan", "show", "profile", f"name={n}", "key=clear"])
            pw = "(şifre yok / açık ağ)"
            for dl in detail.splitlines():
                if "anahtar" in dl.lower() or "key content" in dl.lower():
                    if ":" in dl:
                        pw = dl.split(":", 1)[1].strip()
            lines.append(f"  • {n} → {pw}")
    return "\n".join(lines)


# ── Kurulu programlar / tarayici ─────────────────────────────────────────────
def installed_programs(limit: int = 40) -> str:
    if os.name != "nt":
        return "Bu özellik Windows'ta çalışır."
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*, "
        "HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* "
        "| Where-Object {$_.DisplayName} | Select-Object -ExpandProperty DisplayName "
        "| Sort-Object -Unique"
    ])
    progs = [l.strip() for l in out.splitlines() if l.strip()]
    if not progs:
        return "Kurulu program listesi alınamadı."
    try:
        limit = max(5, min(int(limit or 40), 100))
    except (TypeError, ValueError):
        limit = 40
    head = f"📦 Kurulu programlar ({len(progs)} adet, ilk {min(limit,len(progs))}):"
    return head + "\n" + "\n".join(f"  • {p}" for p in progs[:limit])


# ── Hesap & lisans ───────────────────────────────────────────────────────────
def account_license() -> str:
    lines = ["🔑 [HESAP & LİSANS]"]
    if os.name != "nt":
        return "Bu özellik Windows'ta çalışır."
    # Kullanici hesaplari
    users = _run(["net", "user"])
    if users:
        names = []
        capture = False
        for line in users.splitlines():
            if "----" in line:
                capture = True; continue
            if "komut" in line.lower() or "command completed" in line.lower():
                break
            if capture:
                names.extend([w for w in line.split() if w])
        if names:
            lines.append("Kullanıcı hesapları: " + ", ".join(names[:15]))
    # Windows lisans durumu
    lic = _run(["cscript", "//nologo", r"C:\Windows\System32\slmgr.vbs", "/dli"], shell=True)
    for line in lic.splitlines():
        low = line.lower()
        if "durum" in low or "license status" in low:
            lines.append("Lisans: " + line.split(":", 1)[-1].strip())
            break
    if len(lines) == 1:
        lines.append("(Lisans/hesap detayı okunamadı — yönetici gerekebilir.)")
    return "\n".join(lines)


# ── Hepsi bir arada ──────────────────────────────────────────────────────────
def full_system_report() -> str:
    """Tum sistem bilgilerini tek raporda toplar."""
    parts = [computer_info(), network_info(), account_license()]
    note = ("\n📌 NOT: Windows GİRİŞ (oturum açma) şifresi teknik olarak OKUNAMAZ — "
            "Windows onu geri döndürülemez şekilde (hash) saklar. WiFi şifreleri ise "
            "yukarıda gösterildi (onlar okunabilir).")
    return "\n\n".join(parts) + note
