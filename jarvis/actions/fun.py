"""
Bilgi & Eglence paketi — fikra, ilginc bilgi, bilmece, gunun sozu, tarihte bugun.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition
Yerel havuzlar (anahtarsiz, aninda). Gemini varsa daha cesitli uretebilir.
"""

from __future__ import annotations

import random
import datetime

from app_config import get_app_config_value

_JOKES = [
    "Temel denize düşmüş, 'imdat yüzme bilmiyorum!' demiş. Adam demiş 'ben de bilmiyorum ama bağırmıyorum.'",
    "Doktor: Günde kaç bardak su içiyorsun? Hasta: Bardağım yok ki doktor bey, şişeden içiyorum.",
    "Öğretmen: Bir cümlede 'ıspanak' kullan. Öğrenci: Ispanağı sevmem. Öğretmen: Aferin!",
    "Bilgisayar neden üşümüş? Çünkü pencereleri açık bırakmış! 🪟",
    "İki fasulye tartışıyormuş. Biri demiş: Sen niye böyle piştin? Öbürü: Sen niye çiğ kaldın!",
    "Adamın biri saatini denize düşürmüş, balıklar hâlâ tik tak diye dolaşıyormuş.",
]

_FACTS = [
    "Bir yıldırım, güneşin yüzeyinden 5 kat daha sıcaktır. ⚡",
    "Bal, bozulmayan tek gıdadır — binlerce yıl dayanır. 🍯",
    "Ahtapotların üç kalbi ve mavi kanı vardır. 🐙",
    "Bir günde ortalama 20.000 kez nefes alırsın. 🫁",
    "Gözlerin doğduğundan beri aynı boyutta, ama burnun ve kulakların hep büyür. 👂",
    "Muz, botanik olarak bir 'meyve' değil 'çilek' (berry) sınıfındadır. 🍌",
    "Deniz kızı diye bilinen manatiler, fillerle akrabadır. 🐘",
    "Uzayda iki metal parça değince kaynaşıp yapışır (soğuk kaynak). 🌌",
    "Bir çay kaşığı nötron yıldızı ~6 milyar ton ağırlığındadır. ⭐",
    "Karıncalar asla uyumaz, sadece kısa dinlenmeler yapar. 🐜",
]

_RIDDLES = [
    ("Kanadı var uçamaz, suyu var içemez. Nedir?", "Gemi / uçak (mecazi) — cevap: Uçak değil, 'yaprak' da denir; klasik cevap: gemi"),
    ("Bir odada 3 lamba var, dışarıda 3 düğme. Nasıl bulursun?", "Birini aç bekle-kapat, birini açık bırak, gir: yanan=açık, sıcak=kapattığın, soğuk=hiç açmadığın."),
    ("Aldıkça büyür, verdikçe küçülür. Nedir?", "Çukur 🕳️"),
    ("Sabah dört ayak, öğlen iki, akşam üç ayak. Nedir?", "İnsan (bebek/yetişkin/yaşlı-baston)."),
    ("Her şeyi yer ama su içince ölür. Nedir?", "Ateş 🔥"),
    ("Anahtarı var ama kapısı yok, odası var ama kimse yaşamaz. Nedir?", "Piyano 🎹"),
]

_QUOTES = [
    "\"Hayatta en hakiki mürşit ilimdir.\" — Atatürk",
    "\"Başarı, cesaretle başlar.\" — Anonim",
    "\"Bir şeyi yeterince çok istersen, tüm evren sana yardım eder.\" — Coelho",
    "\"Düşmeden yürümeyi öğrenen olmadı.\" — Anonim",
    "\"Bugün yapabileceğini yarına bırakma.\" — Franklin",
    "\"Zorluklar, gücünü keşfetmen için vardır.\" — Anonim",
]


def _maybe_gemini(kind_prompt: str) -> str:
    key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not key:
        return ""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash", contents=kind_prompt,
            config=types.GenerateContentConfig(temperature=1.0))
        return (getattr(resp, "text", "") or "").strip()
    except Exception:
        return ""


def tell_joke() -> str:
    g = _maybe_gemini("Bana kısa, temiz, güldürücü bir Türkçe fıkra/espri söyle. Sadece fıkrayı ver.")
    return "😄 " + (g or random.choice(_JOKES))


def fun_fact() -> str:
    g = _maybe_gemini("Bana şaşırtıcı, doğru, kısa bir 'biliyor muydun' bilgisi ver (Türkçe, tek cümle).")
    return "💡 " + (g or random.choice(_FACTS))


def riddle() -> str:
    q, a = random.choice(_RIDDLES)
    return f"🧩 Bilmece: {q}\n(İpucu istersen sor; cevap: {a})"


def quote_of_day() -> str:
    return "🌟 Günün sözü: " + random.choice(_QUOTES)


def this_day_in_history() -> str:
    """Tarihte bugun — Gemini varsa gercek olay, yoksa genel mesaj."""
    now = datetime.datetime.now()
    d = now.strftime("%d %B")
    g = _maybe_gemini(f"Tarihte bugün ({d}) yaşanmış 1-2 önemli olayı kısaca Türkçe söyle.")
    if g:
        return f"📅 Tarihte bugün ({d}):\n{g}"
    return (f"📅 Bugün {d}. Tarihte bu günle ilgili detay için internet/Gemini gerekli. "
            "İstersen 'deep_web_search' ile araştırabilirim.")
