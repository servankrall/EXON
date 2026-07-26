"""
Ek Sistem Detaylari — daha da fazla okunabilir bilgi.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Ses/kamera/mikrofon aygitlari, ag adaptorleri, yazicilar, guvenlik (Defender/
firewall), Windows guncellemeleri, pil sagligi, guc plani, islemci detay,
zaman/bolge, kullanici klasorleri, servisler, fontlar. Salt-okunur.
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


def _ps(cmd: str) -> str:
    return _run(["powershell", "-NoProfile", "-Command", cmd])


def _lines(text, limit=30):
    return [l.strip() for l in text.splitlines() if l.strip()][:limit]


def audio_devices() -> str:
    """Ses cikis/giris (hoparlor, mikrofon) aygitlari."""
    if os.name != "nt":
        return "Ses aygıtları Windows'ta okunur."
    out = _ps("Get-PnpDevice -Class AudioEndpoint,Media -Status OK -ErrorAction SilentlyContinue "
              "| Select-Object -ExpandProperty FriendlyName")
    devs = _lines(out, 25)
    if not devs:
        return "🔊 Ses aygıtı listelenemedi."
    return "🔊 [SES AYGITLARI (hoparlör/mikrofon)]\n" + "\n".join(f"  • {d}" for d in devs)


def camera_devices() -> str:
    """Kamera/webcam aygitlari."""
    if os.name != "nt":
        return "Kamera bilgisi Windows'ta okunur."
    out = _ps("Get-PnpDevice -Class Camera,Image -Status OK -ErrorAction SilentlyContinue "
              "| Select-Object -ExpandProperty FriendlyName")
    devs = _lines(out, 15)
    if not devs:
        return "📷 Kamera bulunamadı (yok veya kapalı olabilir)."
    return "📷 [KAMERALAR]\n" + "\n".join(f"  • {d}" for d in devs)


def network_adapters() -> str:
    """Ag adaptorleri: MAC, hiz, durum."""
    if os.name != "nt":
        return "Ağ adaptörü Windows'ta okunur."
    out = _ps("Get-NetAdapter -ErrorAction SilentlyContinue | "
              "ForEach-Object { \"$($_.Name) | $($_.MacAddress) | $($_.LinkSpeed) | $($_.Status)\" }")
    rows = _lines(out, 20)
    if not rows:
        return "🌐 Ağ adaptörü bilgisi alınamadı."
    lines = ["🌐 [AĞ ADAPTÖRLERİ]"]
    for r in rows:
        p = [x.strip() for x in r.split("|")]
        if len(p) >= 4:
            lines.append(f"  • {p[0]} — MAC {p[1]}, {p[2]}, {p[3]}")
    return "\n".join(lines)


def printers() -> str:
    """Kurulu yazicilar."""
    if os.name != "nt":
        return "Yazıcı bilgisi Windows'ta okunur."
    out = _ps("Get-Printer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name")
    devs = _lines(out, 20)
    if not devs:
        return "🖨️ Yazıcı bulunamadı."
    return "🖨️ [YAZICILAR]\n" + "\n".join(f"  • {d}" for d in devs)


def security_status() -> str:
    """Windows Defender + Guvenlik Duvari durumu."""
    if os.name != "nt":
        return "Güvenlik durumu Windows'ta okunur."
    lines = ["🛡️ [GÜVENLİK DURUMU]"]
    d = _ps("(Get-MpComputerStatus -ErrorAction SilentlyContinue) | "
            "ForEach-Object { \"AV:$($_.AntivirusEnabled) RT:$($_.RealTimeProtectionEnabled) \"+"
            "\"Imza:$($_.AntivirusSignatureLastUpdated)\" }")
    if d.strip():
        lines.append("  Defender: " + d.strip())
    fw = _ps("(Get-NetFirewallProfile -ErrorAction SilentlyContinue) | "
             "ForEach-Object { \"$($_.Name):$($_.Enabled)\" }")
    if fw.strip():
        lines.append("  Güvenlik Duvarı: " + " ".join(_lines(fw, 5)))
    if len(lines) == 1:
        lines.append("  (Durum okunamadı — yönetici gerekebilir.)")
    return "\n".join(lines)


def windows_updates() -> str:
    """Son yuklenen Windows guncellemeleri."""
    if os.name != "nt":
        return "Güncelleme bilgisi Windows'ta okunur."
    out = _ps("Get-HotFix -ErrorAction SilentlyContinue | Sort-Object InstalledOn -Descending | "
              "Select-Object -First 10 | ForEach-Object { \"$($_.HotFixID) - $($_.InstalledOn)\" }")
    rows = _lines(out, 12)
    if not rows:
        return "🔄 Güncelleme geçmişi alınamadı."
    return "🔄 [SON WINDOWS GÜNCELLEMELERİ]\n" + "\n".join(f"  • {r}" for r in rows)


def battery_health() -> str:
    """Pil sagligi (tasarim vs mevcut kapasite)."""
    if os.name != "nt":
        return "Pil sağlığı Windows'ta okunur."
    design = _ps("(Get-WmiObject -Class BatteryStaticData -Namespace root\\wmi "
                 "-ErrorAction SilentlyContinue).DesignedCapacity")
    full = _ps("(Get-WmiObject -Class BatteryFullChargedCapacity -Namespace root\\wmi "
               "-ErrorAction SilentlyContinue).FullChargedCapacity")
    try:
        d = int(_lines(design, 1)[0]); f = int(_lines(full, 1)[0])
        if d > 0:
            health = f / d * 100
            return (f"🔋 [PİL SAĞLIĞI]\n  Tasarım kapasitesi: {d} mWh\n"
                    f"  Şu anki tam kapasite: {f} mWh\n"
                    f"  Sağlık: %{health:.0f} " +
                    ("(iyi)" if health > 80 else "(orta)" if health > 60 else "(zayıf — eskiyor)"))
    except Exception:
        pass
    return "🔋 Pil sağlığı okunamadı (masaüstü olabilir veya erişim yok)."


def power_plan() -> str:
    """Aktif guc plani."""
    if os.name != "nt":
        return "Güç planı Windows'ta okunur."
    out = _run(["powercfg", "/getactivescheme"])
    if out and "(" in out:
        name = out.split("(")[-1].split(")")[0]
        return f"⚡ Aktif güç planı: {name}"
    return "⚡ Güç planı okunamadı."


def cpu_detail() -> str:
    """Islemci ayrintili bilgi."""
    lines = ["🧮 [İŞLEMCİ DETAYI]"]
    if os.name == "nt":
        out = _run("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,L2CacheSize,L3CacheSize /format:list", shell=True)
        d = {}
        for line in out.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if v.strip():
                    d[k.strip()] = v.strip()
        if d.get("Name"):
            lines.append(f"  {d['Name']}")
        if d.get("NumberOfCores"):
            lines.append(f"  Çekirdek: {d['NumberOfCores']} fiziksel / {d.get('NumberOfLogicalProcessors','?')} mantıksal")
        if d.get("MaxClockSpeed"):
            lines.append(f"  Max hız: {d['MaxClockSpeed']} MHz")
        if d.get("L3CacheSize"):
            lines.append(f"  L3 önbellek: {d['L3CacheSize']} KB")
    try:
        import psutil
        freq = psutil.cpu_freq()
        if freq:
            lines.append(f"  Anlık hız: {freq.current:.0f} MHz")
        lines.append(f"  Anlık kullanım: %{psutil.cpu_percent(interval=0.3):.0f}")
    except Exception:
        pass
    return "\n".join(lines) if len(lines) > 1 else "İşlemci detayı alınamadı."


def locale_info() -> str:
    """Zaman dilimi, bolge, dil."""
    import time as _t
    import locale as _loc
    lines = ["🌍 [BÖLGE & ZAMAN]"]
    try:
        lines.append(f"  Saat dilimi: {_t.tzname[0]}")
    except Exception:
        pass
    if os.name == "nt":
        tz = _ps("(Get-TimeZone -ErrorAction SilentlyContinue).Id")
        if tz.strip():
            lines.append(f"  Windows saat dilimi: {tz.strip()}")
    try:
        lines.append(f"  Dil/yerel: {_loc.getdefaultlocale()[0]}")
    except Exception:
        pass
    return "\n".join(lines)


def user_folders() -> str:
    """Onemli kullanici klasorleri ve yollari."""
    from pathlib import Path
    home = Path.home()
    lines = ["📂 [KULLANICI KLASÖRLERİ]", f"  Ev: {home}"]
    for name in ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"):
        p = home / name
        if p.exists():
            try:
                cnt = sum(1 for _ in p.iterdir())
                lines.append(f"  {name}: {p} ({cnt} öğe)")
            except Exception:
                lines.append(f"  {name}: {p}")
    return "\n".join(lines)


def running_services(limit: int = 20) -> str:
    """Calisan Windows servisleri."""
    if os.name != "nt":
        return "Servis bilgisi Windows'ta okunur."
    out = _ps("Get-Service -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq 'Running'} "
              "| Select-Object -ExpandProperty DisplayName")
    devs = _lines(out, max(5, min(int(limit or 20), 60)))
    if not devs:
        return "Çalışan servis alınamadı."
    return f"⚙️ [ÇALIŞAN SERVİSLER ({len(devs)} gösteriliyor)]\n" + "\n".join(f"  • {d}" for d in devs)


def everything_report() -> str:
    """MEGA rapor — tum ek sistem detaylarini birlestirir."""
    parts = [
        cpu_detail(), audio_devices(), camera_devices(), network_adapters(),
        printers(), security_status(), windows_updates(), battery_health(),
        power_plan(), locale_info(), user_folders(),
    ]
    return "\n\n".join(p for p in parts if p)
