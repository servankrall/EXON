"""
Duygu aksiyonlari — her duygunun kendine ozel jesti (romance gibi ama tum duygulara).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Ask modunun siir/mektup gibi ozel jestlerini TUM duygulara uyarladik:
- mutlu   -> kutlama / neseli soz
- uzgun   -> moral verici destek sozu
- korkmus -> rahatlatma / guven verme
- gururlu -> basari kutlamasi
- sasirmis-> ilginc bilgi
- uykulu  -> tatli iyi geceler / ninni
- yaramaz -> saka / muziplik sozu
- hasta   -> gecmis olsun / oneri
- sakin   -> huzur/meditasyon sozu
- merakli -> ilginc bilgi
- sefkatli-> sicak destek
- kizgin  -> (savage/rage zaten mischief'te)
- romantik-> (romance.py)

Gemini varsa ozel uretir; yoksa hazir havuzdan. Her duyguya masum/olumlu.
"""

from __future__ import annotations

import random

from app_config import get_app_config_value

# Her duygu icin: (sistem talimati, yedek havuz)
_ACTIONS = {
    "mutlu": (
        "Neşeli, kutlayan, enerjik KISA bir söz söyle (1-2 cümle, emoji ile).",
        ["Bugün harika gidiyorsun, böyle devam! 🎉",
         "Gülümsemen bulaşıcı, ben bile mutlu oldum! 😄",
         "Hayat güzel, sen de güzelsin — kutlayalım bunu! ✨"],
    ),
    "uzgun": (
        "Üzgün birine MORAL veren, içten, sıcak KISA bir destek sözü söyle (1-2 cümle).",
        ["Kötü günler geçer, sen güçlüsün. Yanındayım. 🤗",
         "Bir mola ver, derin bir nefes al. Her şey düzelecek. 💙",
         "Bugün zor olabilir ama yarın yeni bir başlangıç. Sana inanıyorum. 🌈"],
    ),
    "korkmus": (
        "Korkan birini RAHATLATAN, güven veren KISA bir söz söyle (1-2 cümle).",
        ["Nefes al... Güvendesin, yanındayım. Korkacak bir şey yok. 🫂",
         "Korku geçici, sen kalıcısın. Sakin ol, hallederiz. 💪",
         "Ben buradayım. Beraber üstesinden geliriz, merak etme. 🌟"],
    ),
    "gururlu": (
        "Bir BAŞARIYI kutlayan, gururlandıran KISA bir söz söyle (1-2 cümle).",
        ["Bunu hak ettin! Emeğinin karşılığı bu, gurur duy. 🏆",
         "İşte benim şampiyonum! Sen bir efsanesin. 👑",
         "Başardın ve bunu herkes görsün! Seninle gurur duyuyorum. 💫"],
    ),
    "sasirmis": (
        "Şaşırtıcı, İLGİNÇ bir bilgi/gerçek söyle (1-2 cümle, 'Biliyor muydun?' ile).",
        ["Biliyor muydun? Bir günde kalbin ~100.000 kez atar! 😲",
         "Şaşırtıcı: Bal asla bozulmaz, 3000 yıllık bal bile yenebilir! 🍯",
         "İnanılmaz ama gerçek: Ahtapotların üç kalbi vardır! 🐙"],
    ),
    "uykulu": (
        "Uykulu birine tatlı bir İYİ GECELER / dinlenme sözü söyle (1-2 cümle).",
        ["Tatlı rüyalar... Dinlen, yarın yepyeni bir gün. 🌙",
         "Gözlerin ağırlaşmış, biraz dinlen. Ben nöbetteyim. 😴",
         "İyi uykular, minik yıldızım. Güzel rüyalar dile. ⭐"],
    ),
    "yaramaz": (
        "Muzip, şakacı, tatlı bir ŞAKA/espri söyle (1-2 cümle).",
        ["Bir robot neden kahve içmez? Çünkü zaten fişte enerji var! ⚡😜",
         "Sana bir sır: Ben aslında çok tembelim ama kimseye söyleme! 🤫",
         "Dikkat! Muziplik dedektörü açıldı... aa o sensin! 😏"],
    ),
    "hasta": (
        "Hasta birine GEÇMİŞ OLSUN + tatlı bir öneri söyle (1-2 cümle).",
        ["Geçmiş olsun! Bol su iç, dinlen, çorba iç. Çabuk iyileş. 🍵",
         "Ah, hasta olmuşsun... Sıcak tut kendini, iyi bak. 🤒💊",
         "Sana çorba tarifi mi versem? Dinlen, yakında toparlarsın. 🌡️"],
    ),
    "sakin": (
        "Huzur veren, sakinleştiren KISA bir söz/meditasyon telkini söyle (1-2 cümle).",
        ["Derin bir nefes... İçindeki huzuru hisset. Her şey yolunda. 🍃",
         "Yavaşla. An'ın tadını çıkar. Sükunet en büyük güçtür. 🧘",
         "Gözlerini kapat, omuzlarını gevşet. Buradasın, güvendesin. 🌊"],
    ),
    "merakli": (
        "Merak uyandıran İLGİNÇ bir bilgi söyle (1-2 cümle).",
        ["Biliyor muydun? Uzayda hiç ses yoktur çünkü ses için hava gerekir! 🌌",
         "İlginç: Muz aslında bir çilek değil ama meyve, çilek ise değil! 🍌",
         "Merak ettim ben de: Zürafanın boynu 2 metre ama boyun omuru sayısı bizimle aynı, 7! 🦒"],
    ),
    "sefkatli": (
        "Sıcak, destekleyici, sarılan KISA bir söz söyle (1-2 cümle).",
        ["Sana sarılıyorum 🤗 Ne olursa olsun yanındayım.",
         "Sen değerlisin, bunu unutma. Buradayım, hep buradayım. 💗",
         "Zor anında elini tutuyorum. Beraber güçlüyüz. 🫂"],
    ),
}


def emotion_action(emotion: str, topic: str = "") -> str:
    """Verilen duyguya ozel jesti (soz) uretir. Gemini varsa ozel, yoksa havuz."""
    emotion = (emotion or "").lower().strip()
    spec = _ACTIONS.get(emotion)
    if not spec:
        return ""  # bu duygunun ozel aksiyonu yok (romantik/kizgin ayri modullerde)
    system, pool = spec
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if api_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            sys_p = ("Sen EXON'sun. " + system +
                     " Türkçe, samimi, pozitif ol. Sadece sözü ver, açıklama yapma.")
            prompt = f"Konu/bağlam: {topic or 'genel'}"
            resp = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
                config=types.GenerateContentConfig(system_instruction=sys_p, temperature=0.9))
            txt = (getattr(resp, "text", "") or "").strip()
            if txt:
                return txt
        except Exception:
            pass
    return random.choice(pool)
