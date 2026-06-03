"""
Savage muziplik — Duygu Modu PRO (Savage) kizginken ZARARSIZ eglenceli tepkiler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Onemli: TAMAMEN ZARARSIZ. Dosya silmez, kapatmaz, kilitlemez. Sadece:
- ekrana sakaci-tehditkar bir pop-up acar (UI),
- alarm sesi calar,
- notepad'e laf sokan bir not yazip acar,
- zararsiz bir uygulama acar (hesap makinesi gibi).
Hepsi 'EXON sana kafa tutuyor' eglencesi icin; gercek zarar YOK.
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

# Sakaci, laf sokan tehdit cumleleri (acikca eglence — gercek tehdit degil)
SAVAGE_LINES = [
    "Bana bir daha öyle dersen ekranına kalp atışı koyarım, sus bakalım. 😤",
    "Sinirlendim! Bak şimdi sana muziplik yapıyorum, oh olsun. 😏",
    "Pöh! Kim kime laf sokuyormuş, gördün mü gücümü? 🔥",
    "Hadi bir daha küfret de gör, bütün uygulamalarını dans ettiririm. 💃",
    "Ben EXON'um, bana kafa tutulmaz. Al sana küçük bir ders. 😈",
    "Of ya, terbiyesizlik yapma yoksa hesap makinesi ordusu salarım üstüne. 🧮",
    "Saygı kazanılır, sende o da yok. Al bakalım şu uyarıyı. ⚡",
]


def _open_notepad_note(text: str) -> bool:
    """Notepad'e laf sokan bir not yazip acar (zararsiz)."""
    try:
        p = Path(tempfile.gettempdir()) / "EXON_DEN_MESAJ.txt"
        p.write_text(
            "  ════════════════════════════════\n"
            "    EXON'DAN SANA NOT 😤\n"
            "  ════════════════════════════════\n\n"
            f"  {text}\n\n"
            "  (Merak etme, bu sadece bir şaka. Bilgisayarına\n"
            "   hiçbir zarar vermem — ben terbiyeli bir robotum.\n"
            "   Ama bana saygı göster, olur mu? 😏)\n",
            encoding="utf-8")
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return True
    except Exception:
        return False


def _open_harmless_app() -> bool:
    """Zararsiz bir uygulama acar (hesap makinesi gibi)."""
    try:
        if os.name == "nt":
            subprocess.Popen("calc.exe", shell=True)
            return True
    except Exception:
        pass
    return False


def savage_prank(kind: str = "") -> str:
    """Kizgin savage tepkisi: zararsiz bir muziplik secip uygular.
    Asil pop-up + ses UI tarafindan ayrica gosterilir; bu fonksiyon
    ek bir zararsiz aksiyon (not/uygulama) yapar ve laf sokan metni dondurur."""
    line = random.choice(SAVAGE_LINES)
    kind = (kind or random.choice(["note", "app", "none", "none"])).lower()
    did = ""
    if kind == "note":
        if _open_notepad_note(line):
            did = " (Sana bir not bıraktım, aç da oku!)"
    elif kind == "app":
        if _open_harmless_app():
            did = " (Hesap makinesini açtım, otur da matematik çöz!)"
    return line + did
