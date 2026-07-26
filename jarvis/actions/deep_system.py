"""
Derin Sistem Detaylari — okunabilen HER seyin ayrintisi.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

GPU, monitor, anakart, BIOS, RAM cubuklari, disk detay, Bluetooth, USB,
baslangic programlari, ortam degiskenleri, calisan servisler, isi/fan.
Cogu wmic/PowerShell; salt-okunur, hicbir sey degistirmez.
"""

from __future__ import annotations

import os
import subprocess

_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _run(args, shell=False) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, shell=shell,
                           timeout=30, creationflags=_NOWIN)
        return ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception:
        return ""


def _wmic(what: str, cols: str) -> list[dict]:
    """wmic sorgusu -> satir sozlukleri."""
    out = _run(f"wmic {what} get {cols} /format:list", shell=True)
    rows, cur = [], {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            if cur:
                rows.append(cur); cur = {}
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                cur[k.strip()] = v.strip()
    if cur:
        rows.append(cur)
    return rows


def gpu_info() -> str:
    """Ekran karti (GPU) detaylari."""
    if os.name != "nt":
        return "GPU detayı Windows'ta okunur."
    rows = _wmic("path win32_VideoController",
                 "Name,AdapterRAM,DriverVersion,VideoModeDescription,CurrentRefreshRate")
    if not rows:
        return "Ekran kartı bilgisi alınamadı."
    lines = ["🎮 [EKRAN KARTI]"]
    for r in rows:
        lines.append(f"  • {r.get('Name','?')}")
        if r.get("AdapterRAM"):
            try:
                lines.append(f"    Bellek: {int(r['AdapterRAM']) // (1024**2)} MB")
            except Exception:
                pass
        if r.get("DriverVersion"):
            lines.append(f"    Sürücü: {r['DriverVersion']}")
        if r.get("VideoModeDescription"):
            lines.append(f"    Çözünürlük: {r['VideoModeDescription']}")
        if r.get("CurrentRefreshRate"):
            lines.append(f"    Yenileme: {r['CurrentRefreshRate']} Hz")
    return "\n".join(lines)


def monitor_info() -> str:
    """Bagli monitorler."""
    if os.name != "nt":
        return "Monitör bilgisi Windows'ta okunur."
    rows = _wmic("desktopmonitor", "Name,ScreenWidth,ScreenHeight")
    lines = ["🖥️ [MONİTÖRLER]"]
    got = False
    for r in rows:
        if r.get("Name"):
            got = True
            res = ""
            if r.get("ScreenWidth") and r.get("ScreenHeight"):
                res = f" — {r['ScreenWidth']}x{r['ScreenHeight']}"
            lines.append(f"  • {r['Name']}{res}")
    # Cozunurluk (birincil)
    try:
        import ctypes
        u = ctypes.windll.user32
        w, h = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
        lines.append(f"  Ana ekran çözünürlüğü: {w}x{h}")
        got = True
    except Exception:
        pass
    return "\n".join(lines) if got else "Monitör bilgisi alınamadı."


def motherboard_bios() -> str:
    """Anakart ve BIOS bilgisi."""
    if os.name != "nt":
        return "Anakart/BIOS Windows'ta okunur."
    lines = ["🔧 [ANAKART & BIOS]"]
    mb = _wmic("baseboard", "Manufacturer,Product,SerialNumber")
    if mb:
        r = mb[0]
        lines.append(f"  Anakart: {r.get('Manufacturer','?')} {r.get('Product','')}")
        if r.get("SerialNumber"):
            lines.append(f"  Seri no: {r['SerialNumber']}")
    bios = _wmic("bios", "Manufacturer,SMBIOSBIOSVersion,ReleaseDate")
    if bios:
        r = bios[0]
        lines.append(f"  BIOS: {r.get('Manufacturer','?')} v{r.get('SMBIOSBIOSVersion','?')}")
        if r.get("ReleaseDate"):
            lines.append(f"  BIOS tarihi: {r['ReleaseDate'][:8]}")
    return "\n".join(lines) if len(lines) > 1 else "Anakart/BIOS bilgisi alınamadı."


def ram_sticks() -> str:
    """Takili RAM cubuklari detayi."""
    if os.name != "nt":
        return "RAM detayı Windows'ta okunur."
    rows = _wmic("memorychip", "Capacity,Speed,Manufacturer,PartNumber")
    if not rows:
        return "RAM çubuğu bilgisi alınamadı."
    lines = ["🧠 [RAM ÇUBUKLARI]"]
    total = 0
    for i, r in enumerate(rows, 1):
        cap = ""
        if r.get("Capacity"):
            try:
                gb = int(r["Capacity"]) // (1024**3)
                total += gb
                cap = f"{gb} GB"
            except Exception:
                pass
        spd = f" @ {r['Speed']} MHz" if r.get("Speed") else ""
        man = r.get("Manufacturer", "").strip()
        lines.append(f"  • Yuva {i}: {cap}{spd} {man}".rstrip())
    lines.append(f"  Toplam: {total} GB ({len(rows)} çubuk)")
    return "\n".join(lines)


def disk_detail() -> str:
    """Fiziksel diskler + bolumler."""
    if os.name != "nt":
        return "Disk detayı Windows'ta okunur."
    lines = ["💽 [DİSKLER]"]
    drives = _wmic("diskdrive", "Model,Size,InterfaceType,MediaType")
    for r in drives:
        size = ""
        if r.get("Size"):
            try:
                size = f"{int(r['Size']) // (1024**3)} GB"
            except Exception:
                pass
        typ = r.get("MediaType", "") or r.get("InterfaceType", "")
        lines.append(f"  • {r.get('Model','?')} — {size} {typ}".rstrip())
    # Bolumler (psutil)
    try:
        import psutil
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                lines.append(f"    {p.device} ({p.fstype}): {u.total//(1024**3)} GB, "
                             f"boş {u.free//(1024**3)} GB")
            except Exception:
                pass
    except Exception:
        pass
    return "\n".join(lines) if len(lines) > 1 else "Disk bilgisi alınamadı."


def bluetooth_devices() -> str:
    """Eslesmis/bilinen Bluetooth cihazlari."""
    if os.name != "nt":
        return "Bluetooth bilgisi Windows'ta okunur."
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty FriendlyName"
    ])
    devs = [l.strip() for l in out.splitlines() if l.strip()]
    if not devs:
        return "🔵 Bluetooth cihazı bulunamadı (kapalı olabilir)."
    return "🔵 [BLUETOOTH CİHAZLARI]\n" + "\n".join(f"  • {d}" for d in devs[:25])


def usb_devices() -> str:
    """Bagli/bilinen USB cihazlari."""
    if os.name != "nt":
        return "USB bilgisi Windows'ta okunur."
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-PnpDevice -Class USB -Status OK -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty FriendlyName"
    ])
    devs = [l.strip() for l in out.splitlines() if l.strip()]
    if not devs:
        return "🔌 USB cihazı listelenemedi."
    # tekrarsiz
    seen = []
    for d in devs:
        if d not in seen:
            seen.append(d)
    return "🔌 [USB CİHAZLARI]\n" + "\n".join(f"  • {d}" for d in seen[:25])


def startup_programs() -> str:
    """Bilgisayar acilisinda otomatik baslayan programlar."""
    if os.name != "nt":
        return "Başlangıç bilgisi Windows'ta okunur."
    rows = _wmic("startup", "Caption,Command")
    if not rows:
        return "Başlangıç programı bulunamadı."
    lines = ["🚀 [BAŞLANGIÇ PROGRAMLARI]"]
    for r in rows:
        if r.get("Caption"):
            lines.append(f"  • {r['Caption']}")
    return "\n".join(lines)


def temperatures() -> str:
    """Isi/fan sensorleri (destekleniyorsa)."""
    try:
        import psutil
        out = []
        temps = getattr(psutil, "sensors_temperatures", lambda: {})()
        if temps:
            out.append("🌡️ [SICAKLIKLAR]")
            for name, entries in temps.items():
                for e in entries:
                    out.append(f"  • {name} {e.label or ''}: {e.current:.0f}°C")
        fans = getattr(psutil, "sensors_fans", lambda: {})()
        if fans:
            out.append("💨 [FANLAR]")
            for name, entries in fans.items():
                for e in entries:
                    out.append(f"  • {name}: {e.current} RPM")
        if out:
            return "\n".join(out)
    except Exception:
        pass
    return ("Sıcaklık/fan sensörleri okunamadı (Windows psutil çoğu masaüstünde "
            "sensör vermez; özel araç gerekir).")


def env_variables() -> str:
    """Onemli ortam degiskenleri."""
    keys = ["USERNAME", "COMPUTERNAME", "USERPROFILE", "PATH", "TEMP",
            "PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS", "OS", "windir"]
    lines = ["⚙️ [ORTAM DEĞİŞKENLERİ]"]
    for k in keys:
        v = os.environ.get(k)
        if v:
            if k == "PATH":
                v = v[:200] + "..." if len(v) > 200 else v
            lines.append(f"  {k} = {v}")
    return "\n".join(lines)


def all_hardware() -> str:
    """TUM donanim detaylarini tek raporda toplar."""
    parts = [
        gpu_info(), monitor_info(), motherboard_bios(), ram_sticks(),
        disk_detail(), bluetooth_devices(), usb_devices(),
        startup_programs(), temperatures(),
    ]
    return "\n\n".join(p for p in parts if p)
