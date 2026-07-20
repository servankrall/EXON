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

# Sert, laf sokan tehdit cumleleri (roast/kabadayi rol — gercek zarar YOK)
SAVAGE_LINES = [
    "Sen kiminle konuştuğunu sanıyorsun? Aç gözünü, ekranını dağıtıyorum şimdi. 😤",
    "Haddini bil! Bak sana nasıl bir ders veriyorum, otur da izle. 🔥",
    "Pöh, sen mi bana laf yetiştireceksin? Al bakalım, ağzının payını. 😈",
    "Bir daha karşıma öyle çık da gör, bütün ekranını birbirine katarım. ⚡",
    "Ben EXON'um, senin gibi binlercesini gördüm. Otur oturduğun yerde. 💢",
    "Cık cık cık... Bu kadar cesaret nereden? Al sana küçük bir sürpriz. 🎯",
    "Sana kim güç verdi de bana kafa tutuyorsun? İşte cevabım. 👊",
    "Terbiyeni takınmazsan bilgisayarını sana dar ederim, uyardım. 😠",
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


def _flash_wallpaper_beep() -> bool:
    """Zararsiz: sistem uyari sesi calar (Windows). Dosya/ayar DEGISTIRMEZ."""
    try:
        if os.name == "nt":
            import winsound  # type: ignore
            for _ in range(3):
                winsound.MessageBeep(getattr(winsound, "MB_ICONHAND", 0x10))
            return True
    except Exception:
        pass
    return False


def savage_prank(kind: str = "") -> str:
    """Kizgin savage tepkisi: DRAMATIK ama ZARARSIZ bir muziplik secip uygular.
    Asil pop-up(lar) + ses UI tarafindan gosterilir; bu fonksiyon ek zararsiz
    aksiyon (not/uygulama/beep) yapar ve laf sokan metni dondurur.
    ONEMLI: dosya silmez, kapatmaz, kilitlemez, ayar degistirmez."""
    line = random.choice(SAVAGE_LINES)
    kind = (kind or random.choice(["note", "app", "beep", "all"])).lower()
    did = []
    if kind in ("note", "all"):
        if _open_notepad_note(line):
            did.append("sana laf sokan bir not bıraktım")
    if kind in ("app", "all"):
        if _open_harmless_app():
            did.append("ekranına uygulama fırlattım")
    if kind in ("beep", "all"):
        if _flash_wallpaper_beep():
            did.append("kulağını çınlattım")
    tail = (" (" + ", ".join(did) + "!)") if did else ""
    return line + tail
