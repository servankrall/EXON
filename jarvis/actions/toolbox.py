"""
EXON Araç Kutusu — gündelik pratik araçlar (stdlib, güvenli, hızlı).
EXON Robotik tarafından geliştirilmiştir — EXON Windows Edition

Hesap makinesi, birim çevirici, şifre üretici, zar/yazı-tura, pano,
metin araçları, masaüstü bildirimi. Harici paket gerektirmez
(pano için pyperclip lazy; bildirim için PowerShell).
"""

from __future__ import annotations

import ast
import operator
import os
import random
import secrets
import string
import subprocess

# ── Güvenli hesap makinesi (eval KULLANMAZ, ast ile) ─────────────────────────
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
import math as _math
_FUNCS = {k: getattr(_math, k) for k in
          ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "floor", "ceil", "fabs")}
_CONSTS = {"pi": _math.pi, "e": _math.e}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("geçersiz sabit")
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Name):
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise ValueError(f"bilinmeyen: {node.id}")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _FUNCS.get(node.func.id)
        if fn:
            return fn(*[_safe_eval(a) for a in node.args])
        raise ValueError(f"bilinmeyen fonksiyon: {node.func.id}")
    raise ValueError("desteklenmeyen ifade")


def calculate(expression: str) -> str:
    """Bir matematik ifadesini güvenle hesaplar. Örn: '2*(3+4)', 'sqrt(144)', 'sin(pi/2)'."""
    expr = (expression or "").strip().replace("^", "**").replace(",", ".").replace("×", "*").replace("÷", "/")
    if not expr:
        return "Hesaplanacak bir işlem ver."
    try:
        result = _safe_eval(ast.parse(expr, mode="eval").body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{expression} = {result}"
    except Exception:
        return f"'{expression}' hesaplanamadı. Örnek: 2*(3+4), sqrt(144), sin(pi/2)."


# ── Birim çevirici ───────────────────────────────────────────────────────────
# kategori -> {birim: temel_birime_carpan}
_UNITS = {
    "uzunluk": {"mm": 0.001, "cm": 0.01, "m": 1, "km": 1000, "inch": 0.0254,
                "in": 0.0254, "ft": 0.3048, "feet": 0.3048, "yard": 0.9144,
                "mil": 1609.34, "mile": 1609.34},
    "agirlik": {"mg": 1e-6, "g": 0.001, "kg": 1, "ton": 1000, "lb": 0.453592,
                "pound": 0.453592, "ons": 0.0283495, "oz": 0.0283495},
    "hacim":   {"ml": 0.001, "l": 1, "litre": 1, "m3": 1000, "gallon": 3.78541,
                "galon": 3.78541, "bardak": 0.2, "cup": 0.24},
    "alan":    {"cm2": 0.0001, "m2": 1, "km2": 1e6, "hektar": 10000, "donum": 1000,
                "acre": 4046.86, "dekar": 1000},
    "hiz":     {"m/s": 1, "km/h": 0.277778, "km/s": 0.277778, "mph": 0.44704,
                "knot": 0.514444},
    "veri":    {"byte": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4},
    "zaman":   {"sn": 1, "saniye": 1, "dk": 60, "dakika": 60, "saat": 3600,
                "gun": 86400, "gün": 86400, "hafta": 604800},
}


def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Bir değeri bir birimden diğerine çevirir (uzunluk, ağırlık, hacim, alan, hız, veri, zaman)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Geçerli bir sayı ver."
    f = (from_unit or "").strip().lower()
    t = (to_unit or "").strip().lower()

    # Sıcaklık özel (doğrusal değil)
    temps = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}
    if f in temps or t in temps:
        return _convert_temp(value, f, t)

    for cat, units in _UNITS.items():
        if f in units and t in units:
            base = value * units[f]
            out = base / units[t]
            return f"{value:g} {from_unit} = {out:g} {to_unit}"
    return (f"'{from_unit}' → '{to_unit}' çevrilemedi. Desteklenen: uzunluk, ağırlık, "
            "hacim, alan, hız, veri, zaman, sıcaklık.")


def _convert_temp(value: float, f: str, t: str) -> str:
    f = f[0] if f else "c"
    t = t[0] if t else "c"
    # önce Celsius'a
    if f == "c":
        c = value
    elif f == "f":
        c = (value - 32) * 5 / 9
    else:  # kelvin
        c = value - 273.15
    if t == "c":
        out = c
    elif t == "f":
        out = c * 9 / 5 + 32
    else:
        out = c + 273.15
    names = {"c": "°C", "f": "°F", "k": "K"}
    return f"{value:g}{names.get(f,'')} = {out:.2f}{names.get(t,'')}"


# ── Şifre üretici ────────────────────────────────────────────────────────────
def generate_password(length: int = 16, symbols: bool = True) -> str:
    """Güçlü, rastgele bir şifre üretir."""
    try:
        length = max(6, min(int(length or 16), 64))
    except (TypeError, ValueError):
        length = 16
    alpha = string.ascii_letters + string.digits
    if symbols:
        alpha += "!@#$%^&*-_=+?"
    pw = "".join(secrets.choice(alpha) for _ in range(length))
    return f"Yeni şifre ({length} karakter):\n{pw}"


# ── Rastgele karar ───────────────────────────────────────────────────────────
def random_decision(kind: str = "coin", options: str = "", low: int = 1, high: int = 100) -> str:
    """Rastgele karar: coin (yazı-tura), dice (zar), number (sayı), pick (listeden seç)."""
    kind = (kind or "coin").lower().strip()
    if kind in ("coin", "yazitura", "yazı tura", "para"):
        return "🪙 " + random.choice(["Yazı", "Tura"])
    if kind in ("dice", "zar"):
        d = random.randint(1, 6)
        pips = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][d]
        return f"🎲 Zar: {d} {pips}"
    if kind in ("number", "sayi", "sayı"):
        try:
            lo, hi = int(low), int(high)
        except (TypeError, ValueError):
            lo, hi = 1, 100
        if lo > hi:
            lo, hi = hi, lo
        return f"🔢 {lo}-{hi} arası: {random.randint(lo, hi)}"
    if kind in ("pick", "sec", "seç"):
        opts = [o.strip() for o in (options or "").replace(";", ",").split(",") if o.strip()]
        if not opts:
            return "Seçmem için seçenekleri ver (virgülle ayır)."
        return f"🎯 Seçtim: {random.choice(opts)}"
    return "kind: coin | dice | number | pick olmalı."


# ── Pano (clipboard) ─────────────────────────────────────────────────────────
def clipboard_action(action: str = "read", text: str = "") -> str:
    """Panoyu okur veya panoya yazar. action: read | write."""
    try:
        import pyperclip
    except Exception:
        return "Pano için pyperclip gerekli (pip install pyperclip)."
    action = (action or "read").lower().strip()
    try:
        if action in ("write", "copy", "kopyala", "yaz"):
            pyperclip.copy(text or "")
            return f"Panoya kopyalandı: {(text or '')[:60]}"
        content = pyperclip.paste()
        return f"Panodaki metin:\n{content[:1500]}" if content else "Pano boş."
    except Exception as exc:
        return f"Pano işlemi başarısız: {exc}"


# ── Metin araçları ───────────────────────────────────────────────────────────
def text_tools(action: str, text: str) -> str:
    """Metin işlemleri: count (say), upper, lower, title, reverse, slug."""
    action = (action or "count").lower().strip()
    text = text or ""
    if action in ("count", "say", "istatistik"):
        words = len(text.split())
        chars = len(text)
        chars_ns = len(text.replace(" ", ""))
        lines = len(text.splitlines()) or (1 if text else 0)
        return (f"Kelime: {words}, Karakter: {chars} (boşluksuz {chars_ns}), "
                f"Satır: {lines}")
    if action in ("upper", "buyuk", "büyük"):
        return text.upper()
    if action in ("lower", "kucuk", "küçük"):
        return text.lower()
    if action in ("title", "baslik", "başlık"):
        return text.title()
    if action in ("reverse", "ters"):
        return text[::-1]
    if action in ("slug",):
        import re
        s = text.lower()
        tr = {"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"}
        s = "".join(tr.get(c, c) for c in s)
        s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s or "(bos)"
    return "action: count | upper | lower | title | reverse | slug olmalı."


# ── Masaüstü bildirimi ───────────────────────────────────────────────────────
def desktop_notify(title: str = "EXON", message: str = "") -> str:
    """Windows masaüstü bildirimi gösterir (PowerShell balloon tip)."""
    title = (title or "EXON").replace("'", " ")
    message = (message or "").replace("'", " ")
    if os.name != "nt":
        return f"[Bildirim] {title}: {message}"
    try:
        ps = (
            "[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Information; "
            "$n.BalloonTipTitle = '" + title + "'; "
            "$n.BalloonTipText = '" + message + "'; "
            "$n.Visible = $true; $n.ShowBalloonTip(6000); "
            "Start-Sleep -Seconds 6; $n.Dispose()"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return f"🔔 Bildirim gönderildi: {title}"
    except Exception as exc:
        return f"Bildirim gösterilemedi: {exc}"
