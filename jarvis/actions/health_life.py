"""
Saglik & Yasam paketi — su, pomodoro, BMI/kalori, nefes, motivasyon.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition
Tamamen stdlib; hesaplar yerel, hatirlaticilar EXON'un zamanlayicisina yazilir.
"""

from __future__ import annotations

import random


def bmi_calc(weight_kg: float, height_cm: float) -> str:
    """Vucut Kitle Indeksi (BMI) hesaplar ve yorumlar."""
    try:
        w = float(weight_kg); h = float(height_cm) / 100.0
    except (TypeError, ValueError):
        return "Geçerli kilo (kg) ve boy (cm) ver."
    if h <= 0 or w <= 0:
        return "Kilo ve boy pozitif olmalı."
    bmi = w / (h * h)
    if bmi < 18.5:
        cat, note = "Zayıf", "Biraz kilo almak iyi olabilir."
    elif bmi < 25:
        cat, note = "Normal", "Harika, sağlıklı aralıktasın! 👍"
    elif bmi < 30:
        cat, note = "Fazla kilolu", "Biraz hareket ve dengeli beslenme iyi gelir."
    else:
        cat, note = "Obez", "Bir uzmana danışman önerilir."
    return f"BMI: {bmi:.1f} — {cat}. {note}"


def water_need(weight_kg: float) -> str:
    """Gunluk onerilen su miktarini hesaplar (~35 ml/kg)."""
    try:
        w = float(weight_kg)
    except (TypeError, ValueError):
        return "Kilonu (kg) ver."
    liters = w * 0.035
    glasses = round(liters / 0.25)
    return (f"Günlük su ihtiyacın: ~{liters:.1f} litre (yaklaşık {glasses} bardak). "
            "Küçük yudumlarla, gün boyu iç. 💧")


def calorie_need(weight_kg: float, height_cm: float, age: int,
                 gender: str = "e", activity: str = "orta") -> str:
    """Gunluk kalori ihtiyaci (Mifflin-St Jeor + aktivite carpani)."""
    try:
        w = float(weight_kg); h = float(height_cm); a = int(age)
    except (TypeError, ValueError):
        return "Kilo, boy, yaş sayısal olmalı."
    g = (gender or "e").lower()[0]
    bmr = 10 * w + 6.25 * h - 5 * a + (5 if g in ("e", "m") else -161)
    mult = {"az": 1.2, "hafif": 1.375, "orta": 1.55, "cok": 1.725,
            "asiri": 1.9, "yüksek": 1.725}.get((activity or "orta").lower(), 1.55)
    total = bmr * mult
    return (f"Günlük kalori ihtiyacın: ~{int(total)} kcal "
            f"(kilo korumak için). Kilo vermek için ~{int(total-500)} kcal, "
            f"almak için ~{int(total+500)} kcal.")


# ── Motivasyon / gunluk soz ──────────────────────────────────────────────────
_MOTIVATION = [
    "Bugün, dünkü seni geçmek için yeni bir şans. Hadi! 💪",
    "Küçük adımlar büyük yolculuklar yapar. Bir adım at. 🚶",
    "Başarı, pes etmeyenlerin ödülüdür. Devam et! 🌟",
    "Zor olması, imkansız olduğu anlamına gelmez. Sen yaparsın. 🔥",
    "Her uzman bir zamanlar acemiydi. Öğrenmeye devam. 📚",
    "Bugün ekeceğin tohum, yarın gölgesinde dinleneceğin ağaç olur. 🌳",
    "Kendine inan; gerisi kendiliğinden gelir. ✨",
    "Yorulduğunda dur, ama asla vazgeçme. 🏁",
    "En karanlık gece bile sabaha erer. Dayan. 🌅",
    "Sen düşündüğünden çok daha güçlüsün. 💎",
]


def daily_motivation() -> str:
    """Gunluk motivasyon sozu."""
    return "💫 " + random.choice(_MOTIVATION)


# ── Nefes egzersizi (4-7-8 gibi) ─────────────────────────────────────────────
def breathing_exercise(cycles: int = 4) -> str:
    """Rahatlatici nefes egzersizi talimati (4-7-8 teknigi)."""
    try:
        cycles = max(1, min(int(cycles or 4), 10))
    except (TypeError, ValueError):
        cycles = 4
    return (f"🧘 4-7-8 Nefes Egzersizi ({cycles} tur):\n"
            "1) Burnundan 4 saniye NEFES AL\n"
            "2) 7 saniye TUT\n"
            "3) Ağzından 8 saniye yavaşça VER\n"
            f"Bunu {cycles} kez tekrarla. Omuzların gevşesin, sakinleş... 🍃")


# ── Pomodoro / su hatirlaticisi bilgisi ──────────────────────────────────────
def pomodoro_info() -> str:
    """Pomodoro teknigini anlatir (zamanlayici scheduler ile kurulabilir)."""
    return ("🍅 Pomodoro Tekniği:\n"
            "• 25 dk odaklan → 5 dk mola\n"
            "• 4 turda bir 15-30 dk uzun mola\n"
            "İstersen 'her 25 dakikada bir mola vermemi hatırlat' de, "
            "sana zamanlanmış hatırlatıcı kurayım. ⏱️")
