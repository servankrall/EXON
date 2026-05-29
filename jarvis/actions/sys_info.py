"""
Sistem bilgisi — Windows uyumlu psutil + subprocess (netsh, wmic)
macOS pmset/airport komutları kaldırıldı, Windows eşdeğerleri eklendi.
Servan Kanğal tarafından yapılmıştır
Windows portu: pmset → psutil, airport → netsh wlan
"""

import subprocess
import datetime
import socket

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def sys_info(query: str) -> str:
    query = query.lower().strip()

    results = []

    if query in ("battery", "pil", "all"):
        results.append(_battery())

    if query in ("cpu", "işlemci", "all"):
        results.append(_cpu())

    if query in ("ram", "bellek", "memory", "all"):
        results.append(_ram())

    if query in ("disk", "depolama", "all"):
        results.append(_disk())

    if query in ("time", "saat", "zaman", "all"):
        now = datetime.datetime.now()
        results.append(f"Saat: {now.strftime('%H:%M:%S')}")

    if query in ("date", "tarih", "all"):
        now = datetime.datetime.now()
        results.append(f"Tarih: {now.strftime('%d %B %Y, %A')}")

    if query in ("network", "ağ", "wifi", "all"):
        results.append(_network())

    if not results:
        results.append(f"Bilinmeyen sorgu: {query}. battery/cpu/ram/disk/time/date/network/all kullanın.")

    return "\n".join(r for r in results if r)


def _battery() -> str:
    if HAS_PSUTIL:
        bat = psutil.sensors_battery()
        if bat:
            status = "Şarj oluyor" if bat.power_plugged else "Pilde"
            secs = bat.secsleft
            if secs and secs > 0 and not bat.power_plugged:
                h, m = divmod(secs // 60, 60)
                time_str = f" — yaklaşık {h}s {m}d kaldı" if h else f" — yaklaşık {m}d kaldı"
            else:
                time_str = ""
            return f"Pil: %{bat.percent:.0f} — {status}{time_str}"
        return "Pil bilgisi alınamadı (masaüstü bilgisayar olabilir)."
    # WMIC fallback
    try:
        out = subprocess.check_output(
            ["wmic", "path", "Win32_Battery", "get", "EstimatedChargeRemaining,BatteryStatus"],
            text=True, timeout=5, stderr=subprocess.DEVNULL
        )
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if len(lines) >= 2:
            return f"Pil: {lines[1]}"
    except Exception:
        pass
    return "Pil bilgisi alınamadı."


def _cpu() -> str:
    if HAS_PSUTIL:
        usage = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count(logical=True)
        phys = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        freq_str = f", {freq.current:.0f} MHz" if freq else ""
        return f"CPU: %{usage:.1f} kullanım — {count} mantıksal ({phys} fiziksel) çekirdek{freq_str}"
    # PowerShell fallback
    try:
        out = subprocess.check_output(
            ["powershell", "-Command",
             "Get-WmiObject Win32_Processor | Select-Object -ExpandProperty LoadPercentage"],
            text=True, timeout=5, stderr=subprocess.DEVNULL
        )
        pct = out.strip()
        return f"CPU: %{pct} kullanım"
    except Exception:
        pass
    return "CPU bilgisi alınamadı."


def _ram() -> str:
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        total = vm.total / (1024 ** 3)
        used = vm.used / (1024 ** 3)
        pct = vm.percent
        return f"RAM: {used:.1f}GB / {total:.1f}GB kullanımda (%{pct:.0f})"
    return "RAM bilgisi alınamadı."


def _disk() -> str:
    if HAS_PSUTIL:
        try:
            du = psutil.disk_usage("C:\\")
            total = du.total / (1024 ** 3)
            used = du.used / (1024 ** 3)
            free = du.free / (1024 ** 3)
            return f"Disk (C:): {used:.1f}GB kullanıldı, {free:.1f}GB boş (toplam {total:.1f}GB)"
        except Exception:
            pass
    # WMIC fallback
    try:
        out = subprocess.check_output(
            ["wmic", "logicaldisk", "get", "DeviceID,FreeSpace,Size"],
            text=True, timeout=5, stderr=subprocess.DEVNULL
        )
        lines = [l.strip() for l in out.splitlines() if l.strip() and "DeviceID" not in l]
        if lines:
            return "Disk: " + " | ".join(lines[:3])
    except Exception:
        pass
    return "Disk bilgisi alınamadı."


def _network() -> str:
    # WiFi SSID — netsh wlan
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace"
        )
        for line in out.splitlines():
            stripped = line.strip()
            if stripped.startswith("SSID") and "BSSID" not in stripped:
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
                    if ssid:
                        return f"WiFi: {ssid} bağlı"
    except Exception:
        pass

    # Ethernet / IP fallback
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127."):
            return f"Ağ: IP {ip} ({hostname})"
    except Exception:
        pass

    return "Ağ bağlantısı bulunamadı."
