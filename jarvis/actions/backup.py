"""
Yedekleme & Tasima — tum kullanici verisini tek zip'e al / geri yukle.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Ayarlar, hafiza, bilgi tabani, gorevler, analitik vb. tek bir .zip dosyasina
toplanir (USB/Drive ile tasinabilir). Geri yukleme mevcut veriyi yedekleyip uzerine yazar.
Sadece stdlib (zipfile). Gercek bulut degil ama tasinabilir ve kesin calisir.
"""

from __future__ import annotations

import time
import zipfile
from pathlib import Path

from paths import DATA_DIR

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
