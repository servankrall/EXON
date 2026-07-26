"""
Yedekleme & Tasima — tum kullanici verisini tek zip'e al / geri yukle.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Ayarlar, hafiza, bilgi tabani, gorevler, analitik vb. tek bir .zip dosyasina
toplanir (USB/Drive ile tasinabilir). Geri yukleme mevcut veriyi yedekleyip uzerine yazar.
Sadece stdlib (zipfile). Gercek bulut degil ama tasinabilir ve kesin calisir.
"""

from __future__ import annotations

import os
import shutil
import time
import zipfile
from pathlib import Path

from paths import DATA_DIR
from app_config import get_app_config_value, save_app_config

_BACKUP_DIR = DATA_DIR / "backups"

# Yedeklenecek klasor/dosyalar (DATA_DIR'e gore)
_INCLUDE = ["config", "memory", "vectors", "security", "plugins",
            "analytics.json"]


def create_backup() -> str:
    """Tum kullanici verisini zaman damgali bir zip'e alir."""
    try:
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        zpath = _BACKUP_DIR / f"exon_yedek_{stamp}.zip"
        count = 0
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in _INCLUDE:
                src = DATA_DIR / item
                if src.is_file():
                    zf.write(src, item)
                    count += 1
                elif src.is_dir():
                    for f in src.rglob("*"):
                        if f.is_file():
                            zf.write(f, str(f.relative_to(DATA_DIR)))
                            count += 1
        size_kb = zpath.stat().st_size // 1024
        return (f"Yedek oluşturuldu: {zpath.name} ({count} dosya, {size_kb} KB).\n"
                f"Konum: {zpath}\nBu dosyayı USB/Drive ile taşıyabilirsin.")
    except Exception as exc:
        return f"Yedekleme başarısız: {exc}"


def list_backups() -> str:
    if not _BACKUP_DIR.exists():
        return "Henüz yedek yok. 'yedek al' diyerek oluşturabilirsin."
    backups = sorted(_BACKUP_DIR.glob("exon_yedek_*.zip"), reverse=True)
    if not backups:
        return "Henüz yedek yok."
    lines = ["[YEDEKLER]"]
    for b in backups[:10]:
        kb = b.stat().st_size // 1024
        when = time.strftime("%d.%m.%Y %H:%M", time.localtime(b.stat().st_mtime))
        lines.append(f"  • {b.name} ({kb} KB, {when})")
    return "\n".join(lines)


def restore_backup(filename: str = "") -> str:
    """Bir yedegi geri yukler. Once mevcut veriyi guvenlik icin yedekler."""
    if not _BACKUP_DIR.exists():
        return "Yedek klasörü yok."
    filename = (filename or "").strip()
    if filename:
        zpath = _BACKUP_DIR / filename
        if not zpath.exists():
            return f"Yedek bulunamadı: {filename}"
    else:
        backups = sorted(_BACKUP_DIR.glob("exon_yedek_*.zip"), reverse=True)
        if not backups:
            return "Geri yüklenecek yedek yok."
        zpath = backups[0]  # en yenisi

    # Once mevcut durumu guvenlik yedegine al
    safety = create_backup()
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            # zip-slip korumasi
            for member in zf.namelist():
                target = (DATA_DIR / member).resolve()
                if not str(target).startswith(str(DATA_DIR.resolve())):
                    return "Güvenlik: yedek şüpheli yol içeriyor, geri yükleme iptal."
            zf.extractall(DATA_DIR)
        return (f"Yedek geri yüklendi: {zpath.name}. "
                "EXON'u yeniden başlatman önerilir. "
                "(Önceki durumun güvenlik yedeği de alındı.)")
    except Exception as exc:
        return f"Geri yükleme başarısız: {exc}"


# ── Bulut klasor senkronizasyonu (OneDrive/Drive/Dropbox) ────────────────────
def _detect_cloud_dirs() -> list[Path]:
    """Bilgisayardaki bilinen bulut senkron klasorlerini bulur."""
    home = Path.home()
    candidates = [
        Path(os.environ.get("OneDrive", "")) if os.environ.get("OneDrive") else None,
        Path(os.environ.get("OneDriveConsumer", "")) if os.environ.get("OneDriveConsumer") else None,
        home / "OneDrive",
        home / "Google Drive",
        home / "GoogleDrive",
        home / "My Drive",
        home / "Dropbox",
        home / "iCloudDrive",
    ]
    found = []
    for c in candidates:
        if c and c.exists() and c.is_dir() and c not in found:
            found.append(c)
    return found


def cloud_sync(target_dir: str = "") -> str:
    """En son yedegi bir bulut klasorune (OneDrive/Drive/Dropbox) kopyalar.
    target_dir verilirse oraya; verilmezse otomatik bulunan ilk bulut klasorune."""
    # Once guncel yedek al
    create_backup()
    backups = sorted(_BACKUP_DIR.glob("exon_yedek_*.zip"), reverse=True)
    if not backups:
        return "Yedek oluşturulamadı, bulut kopyalama yapılamadı."
    latest = backups[0]

    # Hedef klasoru belirle
    target = (target_dir or str(get_app_config_value("cloud_backup_dir", "") or "")).strip()
    if target:
        base = Path(target).expanduser()
    else:
        clouds = _detect_cloud_dirs()
        if not clouds:
            return ("Bilgisayarda OneDrive/Google Drive/Dropbox klasörü bulamadım. "
                    "İstersen bir klasör yolu ver (cloud_sync target_dir=...), oraya yedeklerim.")
        base = clouds[0]

    dest_dir = base / "EXON_Yedekler"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / latest.name
        shutil.copy2(latest, dest)
        # Hedefi hatirla
        save_app_config({"cloud_backup_dir": str(base)})
        return (f"Yedek buluta kopyalandı ✓\n{dest}\n"
                f"({base.name} klasörü otomatik senkronize olur.)")
    except Exception as exc:
        return f"Bulut kopyalama başarısız: {exc}"


def cloud_status() -> str:
    """Bulut yedekleme durumu: tespit edilen klasorler + ayarli hedef."""
    lines = ["[BULUT YEDEKLEME]"]
    saved = str(get_app_config_value("cloud_backup_dir", "") or "").strip()
    if saved:
        lines.append(f"Ayarlı hedef: {saved}\\EXON_Yedekler")
    clouds = _detect_cloud_dirs()
    if clouds:
        lines.append("Bulunan bulut klasörleri:")
        for c in clouds:
            lines.append(f"  • {c}")
    else:
        lines.append("Bilgisayarda otomatik bulut klasörü bulunamadı.")
    lines.append("'buluta yedekle' diyerek en son yedeği oraya kopyalayabilirsin.")
    return "\n".join(lines)
