"""
PC'de dosya/belge arama — Masaustu, Belgeler, Indirilenler vb.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Tum diski taramaz; kullanicinin yaygin klasorlerini, isim/uzanti eslesmesiyle
ve bir zaman butcesiyle tarar. Bulunan dosyalarin tam yolunu dondurur.
"""

from __future__ import annotations

import os
import time
from pathlib import Path


# Taranacak yaygin kok klasorler (Turkce/Ingilizce Windows adlari dahil)
def _search_roots() -> list[Path]:
    home = Path.home()
    names = ["Desktop", "Masaüstü", "Documents", "Belgeler",
             "Downloads", "İndirilenler", "Indirilenler",
             "Pictures", "Resimler", "Music", "Müzik",
             "Videos", "Videolar", "OneDrive"]
    roots: list[Path] = []
    for name in names:
        p = home / name
        if p.exists() and p.is_dir():
            roots.append(p)
    if not roots:
        roots.append(home)
    return roots


def _matches(name: str, terms: list[str]) -> bool:
    low = name.lower()
    return all(t in low for t in terms)


def find_file(query: str, max_results: int = 12) -> str:
    """Verilen ada/uzantiya gore dosya arar ve tam yollarini dondurur.
    Ornek sorgular: 'rapor.pdf', '2024 butce', 'sunum pptx'."""
    query = (query or "").strip()
    if not query:
        return "Aranacak dosya adini ver (orn. 'rapor pdf')."
    try:
        max_results = int(max_results) if max_results else 12
    except (TypeError, ValueError):
        max_results = 12
    max_results = max(1, min(max_results, 50))

    terms = [t for t in query.lower().split() if t]
    deadline = time.time() + 12.0  # en fazla ~12 sn tara
    found: list[str] = []
    skip_dirs = {"node_modules", ".git", "AppData", "$Recycle.Bin",
                 "Windows", "Program Files", "Program Files (x86)",
                 "__pycache__", ".cache", "venv", ".venv"}

    try:
        for root in _search_roots():
            if len(found) >= max_results or time.time() > deadline:
                break
            for dirpath, dirnames, filenames in os.walk(root):
                if time.time() > deadline or len(found) >= max_results:
                    break
                # gereksiz/buyuk klasorleri atla
                dirnames[:] = [d for d in dirnames if d not in skip_dirs
                               and not d.startswith(".")]
                for fname in filenames:
                    if _matches(fname, terms):
                        found.append(str(Path(dirpath) / fname))
                        if len(found) >= max_results:
                            break
    except Exception as exc:
        return f"Dosya aramada hata: {exc}"

    if not found:
        return (f"'{query}' ile eslesen dosya bulunamadi. "
                "Daha az kelime veya dogru uzanti (pdf, docx, jpg) ile dene.")

    lines = "\n".join(f"- {p}" for p in found)
    note = "" if len(found) < max_results else "\n(Daha fazla sonuc olabilir.)"
    return f"'{query}' icin {len(found)} dosya bulundu:\n{lines}{note}"
