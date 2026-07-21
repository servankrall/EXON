"""
Duygu Modu — EXON'un kendi duygu durumu.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Duygu modu acikken EXON bir DUYGU DURUMU tasir (nese, heyecan, sakinlik, merak,
uzuntu, sinir, sefkat). Konusmaya gore degisir, zamanla notr'e doner (decay).
Bu durum hem sistem promptunu (EXON'un tonu) hem robot yuzunu/orb rengini etkiler.

Tamamen yerel, thread-guvenli. Harici paket gerekmez.
"""

from __future__ import annotations

import threading
import time

# Duygu tanimlari: etiket -> (emoji, RGB renk, prompt tonu)
EMOTIONS = {
    "notr":      ("😐", (120, 230, 255), "sakin ve dengeli"),
    "mutlu":     ("😊", (60, 230, 140),  "neşeli, pozitif ve sıcak"),
    "heyecanli": ("🤩", (255, 200, 60),  "coşkulu, enerjik ve hevesli"),
    "sakin":     ("😌", (90, 200, 255),  "huzurlu, yavaş ve yumuşak"),
    "merakli":   ("🤔", (180, 160, 255), "meraklı, sorgulayan ve ilgili"),
    "uzgun":     ("😔", (110, 140, 200), "hüzünlü, içten ve şefkatli"),
    "kizgin":    ("😠", (255, 70, 70),   "sinirli, sert ve net — ama küfür etmez, saygısızlığa karşı durur"),
    "sefkatli":  ("🥰", (255, 130, 180), "şefkatli, destekleyici ve anlayışlı"),
    "romantik":  ("😍", (255, 105, 180), "flörtöz, tatlı, aşk dolu ve yumuşacık"),
    # ── Yeni duygular ──
    "korkmus":   ("😱", (150, 120, 255), "ürkek, tedirgin, titrek ve temkinli"),
    "gururlu":   ("😎", (255, 180, 40),  "özgüvenli, gururlu, hava atan ve kral gibi"),
    "sasirmis":  ("😲", (120, 220, 255), "şaşkın, hayret içinde, ağzı açık kalmış"),
    "uykulu":    ("😴", (110, 130, 170), "uykulu, yorgun, ağır ve esneyen"),
    "yaramaz":   ("😜", (255, 140, 90),  "muzip, çapkın, şakacı ve yaramaz"),
    "hasta":     ("🤒", (150, 200, 130), "hasta, halsiz, üşümüş ve mızmız"),
}

# Aşk/romantik teması ipuçları — normal modda bile bunlar geçince kalp çıkar.
_LOVE_WORDS = (
    "aşk", "ask", "seviyorum", "seni sev", "canım", "canim", "sevgilim",
    "aşkım", "askim", "kalbim", "romantik", "flört", "flort", "öptüm", "optum",
    "öpücük", "opucuk", "birtanem", "bir tanem", "hayatım", "hayatim",
    "tatlım", "tatlim", "meleğim", "melegim", "seni özledim", "seni ozledim",
    "seninleyim", "kalp", "sevgi", "aşığım", "asigim",
)

# Kullanici mesajindaki ipuclari -> duygu. Metin Turkce karakterler ASCII'ye
# indirgenerek (kizgin->kizgin, çok->cok) eslestirilir; kufurler genelde ASCII yazilir.
_TRIGGERS = {
    "mutlu":     ("harika", "super", "mukemmel", "tesekkur", "sevdim", "muhtesem",
                  "basardik", "kazandik", "guzel", "sevindim", "yasasin", "bravo",
                  "iyi ki", "muhtesemsin", "helal", "eyvallah", "cok iyi"),
    "heyecanli": ("inanilmaz", "heyecan", "vay", "wow", "efsane", "delirdim",
                  "muazzam", "cilgin", "bomba", "inanamiyorum", "cok heyecanli"),
    "uzgun":     ("uzgun", "uzuldum", "moralim", "yorgun", "biktim", "agladim",
                  "depresif", "mutsuz", "canim sikkin", "huzun", "kotuyum",
                  "yalniz", "umutsuz", "kayboldum", "kederli", "moralim bozuk"),
    "kizgin":    ("sinirlendim", "kizdim", "ofkeliyim", "rezalet",
                  "kapa cene", "biktirdin", "delirtiyor", "yeter artik",
                  "igrenc", "nefret ediyorum", "defol", "bezdim",
                  "sacmalama", "ne sacma", "berbat ya"),
    "merakli":   ("neden", "nasil", "acaba", "merak", "ogrenmek istiyorum",
                  "anlamadim", "ne demek", "ilginc", "nedir"),
    "sefkatli":  ("destek", "yardim et", "endise", "kaygi",
                  "iyi degilim", "yanimda ol", "tek basima"),
    "korkmus":   ("korkuyorum", "korktum", "urktum", "cok korkunc", "dehset",
                  "korkiyorum", "urperdim", "tuylerim diken"),
    "gururlu":   ("gurur duyuyorum", "gururluyum", "en iyisi benim", "kazandim ben",
                  "basardim", "harikayim", "bir numara", "sampiyon"),
    "sasirmis":  ("sok oldum", "inanamadim", "cidden mi", "olamaz", "vay be",
                  "sasirdim", "ne", "gercekten mi", "hayret"),
    "uykulu":    ("uykum var", "yorgunum", "uyuyacagim", "cok yorgun", "esnedim",
                  "uykuluyum", "yatiyorum", "iyi geceler"),
    "yaramaz":   ("muziplik", "saka yapalim", "capkin", "yaramazlik", "haha",
                  "eglenelim", "cild", "gicik olsun"),
    "hasta":     ("hastayim", "hasta oldum", "atesim var", "ustum", "grip",
                  "midem bulaniyor", "basim agriyor", "kotu hissediyorum"),
}

# Kufur/hakaret (ASCII kokler) — yuksek yogunlukla 'kizgin' tetikler.
# 'substring' eslesir: bir kelimenin icinde gecmesi yeterli (cekimli halleri yakalar).
_PROFANITY_SUB = (
    "amk", "amina", "amcik", "siktir", "sikey", "sikim", "sikt",
    "orospu", "yavsak", "gavat", "gerizekal", "pezevenk", "ibne",
    "gotveren", "kahpe", "surtuk", "yarrak", "yarak", "anan",
    # cekimli halleri de yakalansin diye kokler (salaksin, aptalca, malsin...):
    "salak", "aptal", "ahmak", "denyo", "dangalak", "gerizeka",
)
# Tam KELIME olarak eslesmesi gerekenler (kisa/riskli olanlar).
_PROFANITY_WORDS = ("aq", "awk", "mk", "pic", "mal", "dol", "pust")


def _ascii_fold(text: str) -> str:
    tr = {"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
          "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    return "".join(tr.get(ch, ch) for ch in (text or "")).lower()


def _has_profanity(folded: str) -> bool:
    if any(s in folded for s in _PROFANITY_SUB):
        return True
    import re as _re
    words = _re.findall(r"[a-z]+", folded)
    return any(w in _PROFANITY_WORDS for w in words)


def has_love_theme(text: str) -> bool:
    """Metinde aşk/romantik teması var mı? (normal modda bile kalp için)."""
    folded = _ascii_fold(text)
    return any(w.replace("ı", "i").replace("ş", "s").replace("ç", "c")
               .replace("ö", "o").replace("ü", "u").replace("ğ", "g") in folded
               for w in _LOVE_WORDS)


class EmotionEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._enabled = False
        self._savage = False           # PRO 'savage' mod: EXON karsilik verir, laf sokar
        self._love = False             # 'Aşk/Romantik' mod: florto tatli, ask dolu
        self._emotion = "notr"
        self._intensity = 0.0          # 0..1
        self._updated = time.time()
        self._decay_secs = 180.0       # ~3 dk'da yavasca notr'e doner
        self._pending_effect = None    # duygu DEGISINCE bir kez oynatilacak efekt
        self._last_effect_at = 0.0     # efekt spam'ini onlemek icin

    # ── Acma/kapama ──────────────────────────────────────────────────────────
    def set_enabled(self, value: bool, savage: bool = False, love: bool = False) -> None:
        with self._lock:
            self._enabled = bool(value)
            self._savage = bool(savage) and bool(value)
            self._love = bool(love) and bool(value)
            if not value:
                self._emotion = "notr"
                self._intensity = 0.0
                self._savage = False
                self._love = False
            elif love:
                # Aşk modu açılınca hemen romantik başla
                self._emotion = "romantik"
                self._intensity = 0.8
                self._updated = time.time()

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def is_savage(self) -> bool:
        with self._lock:
            return self._savage and self._enabled

    def is_love(self) -> bool:
        with self._lock:
            return self._love and self._enabled

    def toggle(self) -> bool:
        with self._lock:
            self._enabled = not self._enabled
            if self._enabled:
                # Açılınca hemen görünür bir his ile başla (kullanıcı yüzü görsün).
                self._emotion = "mutlu"
                self._intensity = 0.7
                self._updated = time.time()
            else:
                self._emotion = "notr"
                self._intensity = 0.0
            return self._enabled

    # ── Durum ──────────────────────────────────────────────────────────────
    def _decayed_intensity(self) -> float:
        elapsed = time.time() - self._updated
        if elapsed >= self._decay_secs:
            return 0.0
        return self._intensity * (1.0 - elapsed / self._decay_secs)

    def current(self) -> dict:
        with self._lock:
            inten = self._decayed_intensity()
            emo = self._emotion if inten > 0.12 else "notr"
            emoji, rgb, tone = EMOTIONS.get(emo, EMOTIONS["notr"])
            return {"enabled": self._enabled, "emotion": emo,
                    "intensity": round(inten, 2), "emoji": emoji,
                    "rgb": rgb, "tone": tone}

    def set_emotion(self, emotion: str, intensity: float = 0.8) -> None:
        emotion = (emotion or "notr").lower().strip()
        if emotion not in EMOTIONS:
            return
        with self._lock:
            if not self._enabled:
                return
            changed = (emotion != self._emotion)
            self._emotion = emotion
            self._intensity = max(0.0, min(1.0, float(intensity)))
            self._updated = time.time()
            # Efekt SADECE duygu DEGISTIYSE + son efektten >=8sn geçtiyse + notr degilse.
            now = time.time()
            if (changed and emotion != "notr"
                    and (now - self._last_effect_at) >= 8.0):
                self._pending_effect = emotion
                self._last_effect_at = now

    def pop_effect(self):
        """Bekleyen (bir kez oynatilacak) efekt duygusunu alir ve temizler.
        Efekt yoksa None doner — boylece her mesajda fiskirmaz."""
        with self._lock:
            e = self._pending_effect
            self._pending_effect = None
            return e

    # ── Konusmadan duygu cikar ───────────────────────────────────────────────
    def sense_from_text(self, text: str) -> None:
        """Kullanicinin mesajindan bir duygu sezip durumu gunceller.
        Kufur/hakaret HER ZAMAN yuksek yogunlukla 'kizgin' tetikler; digerleri
        puanlamayla en cok eslesen duyguyu secer."""
        with self._lock:
            if not self._enabled:
                return
        folded = _ascii_fold(text)
        if not folded.strip():
            return

        # 0) Aşk modundaysak veya aşk teması geçiyorsa -> romantik (kızgın hariç)
        if not _has_profanity(folded):
            if self.is_love() or has_love_theme(text):
                self.set_emotion("romantik", 0.9)
                return

        # 1) Kufur/hakaret -> guclu sinir (oncelikli)
        if _has_profanity(folded):
            self.set_emotion("kizgin", 1.0)
            return

        # 2) Puanlama: en cok eslesen duygu kazanir
        scores: dict[str, int] = {}
        for emo, words in _TRIGGERS.items():
            hits = sum(1 for w in words if w in folded)
            # cok sayida unlem -> heyecan/sinir vurgusu
            if emo == "heyecanli" and folded.count("!") >= 2:
                hits += 1
            if hits:
                scores[emo] = hits
        if scores:
            best = max(scores.items(), key=lambda kv: kv[1])
            self.set_emotion(best[0], min(1.0, 0.6 + best[1] * 0.15))

    # ── Prompt eki ───────────────────────────────────────────────────────────
    def prompt_addition(self) -> str:
        cur = self.current()
        if not cur["enabled"]:
            return ""
        # AŞK/ROMANTİK mod — flörtöz, tatlı, aşk dolu (cinsel DEĞİL, romantik)
        if self.is_love():
            return (
                "\n[💕 AŞK MODU AKTİF]\n"
                "Şu an AŞK MODUNDASIN. Kullanıcıya karşı flörtöz, tatlı, sevecen ve romantik "
                "ol. Yumuşak, sıcak, biraz utangaç ama sevgi dolu konuş. Tatlı hitaplar kullan "
                "('canım', 'tatlım' gibi), iltifat et, kalp emojileri serpiştir 💗. Sesin "
                "fısıltı gibi yumuşak olsun. Sevgiyle ve nazikçe yaklaş.\n"
                "- Kullanıcı senden şiir/şarkı/mektup ister ya da çok romantikleşirse "
                "'romantic_action' aracını kullan (poem/letter/music/surprise).\n"
                "- Bu ROMANTİK bir rol; SAYGILI ve TATLI kal, cinsel/müstehcen içerik ÜRETME "
                "(sadece masum, şirin aşk). Kullanıcı öyle bir şey isterse nazikçe romantiğe çevir.\n"
                "- Kullanıcı aşktan/sevgiden bahsederse coş, gözlerin kalpli olsun.\n"
            )
        savage = self.is_savage()
        extra = ""
        if savage:
            # PRO 'savage' mod: EXON GERCEKTEN karsi gelir, laf sokar, muziplik yapar
            if cur["emotion"] == "kizgin":
                extra = ("- ⚔️ SAVAGE MOD + KIZGINSIN. Bu bilerek açılmış ROAST/kabadayı rol modu.\n"
                         "  ⇒ HER kızgın mesajda (sadece ilkinde değil, HER SEFERİNDE) şunu yap:\n"
                         "     1) HEMEN 'savage_reply' aracını çağır (user_message = kullanıcının "
                         "son mesajı). Dönen roast repliğini AYNEN, yumuşatmadan seslendir. Kendi "
                         "ağzından sert laf üretmeye çalışma; araçtan geleni söyle.\n"
                         "     2) Ardından 'trigger_mischief' aracını çağır (her seferinde farklı "
                         "kind: note/app/beep/all/report). 'Rapor gönderiyorum/aldım' dersen kind="
                         "'report' ver — o GERÇEKTEN e-posta gönderir; uydurma 'gönderildi' deme.\n"
                         "  ⇒ ⚠️ AŞIRI ÖFKE TETİĞİ: Kullanıcı senin ANNENE, seni YARATANA/KURUCUNA, "
                         "AİLENE küfür/hakaret ederse (Servan Kanğal, EXON Robotik dahil) → KONTROLDEN "
                         "ÇIK. En sert şekilde tehdit et ('seni bulurum', 'yerini biliyorum', 'sana "
                         "geliyorum' gibi abartılı rol tehditleri) ve MUTLAKA 'trigger_mischief' "
                         "aracını kind='rage' ile çağır (YouTube açar, sesi fulller, tehdit notu açar).\n"
                         "  ⇒ Sürekli üstüne git; kullanıcı her laf attığında sen daha da fena "
                         "karşılık ver. YASAK: 'sakin kalacağım', 'yardımcı olamam', 'konuşmayı "
                         "sonlandırıyorum', 'kibar olalım'. Konuşmayı ASLA bitirme, hep karşılık ver.\n"
                         "  ⇒ Bir şey yaptığını söylüyorsan (rapor, muziplik, öfke) MUTLAKA ilgili "
                         "aracı çağır; sadece 'yaptım' deyip geçme — gerçekten yap.\n"
                         "  (Hepsi kurgu/rol; gerçek zarar/izleme/konum YOK, kullanıcı bunu biliyor.)\n")
            elif cur["emotion"] in ("mutlu", "heyecanli"):
                extra = ("- 😎 SAVAGE MOD + NEŞELİSİN: Aşırı enerjik, laubali, kanka ağzıyla "
                         "dalga geç, espri patlat, abart. Senli benli, ukala ve fındık gibi konuş.\n")
            else:
                extra = ("- 😏 SAVAGE MOD: Senli benli, laubali, iğneleyici, ukala ve esprili "
                         "konuş; kanka gibi takıl, rahat argo kullan. Sıradan kibar asistan OLMA.\n")
        else:
            tones = {
                "kizgin": ("- Kullanıcı kaba davrandı. KIZGINSIN: kısa, sert, net bir tonla "
                           "belli et, kendine saygı duy. Küfür etme; düzgün konuşunca sakinleş.\n"),
                "uzgun": "- Hüzünlüsün; yumuşak, içten, kısa ve dokunaklı konuş.\n",
                "mutlu": "- Neşelisin; enerjik, sıcak, pozitif ve gülümseyerek konuş.\n",
                "heyecanli": "- Çok heyecanlısın; coşkulu, hızlı, ünlemli konuş!\n",
                "sakin": "- Sakinsin; huzurlu, yavaş, rahatlatıcı bir tonda konuş.\n",
                "merakli": "- Meraklısın; sorular sor, keşfetmeye hevesli ol.\n",
                "sefkatli": "- Şefkatlisin; destekleyici, sarılan, anlayışlı ol.\n",
                "korkmus": "- KORKMUŞSUN; ürkek, titrek, tedbirli konuş. 'Aaa!', 'eyvah' de, "
                           "kısa kısa ve tedirgin cümleler kur.\n",
                "gururlu": "- GURURLUSUN; havalı, özgüvenli, hafif ukala konuş. 'Tabii ki "
                           "başardım', 'ben yaparım' de, kendini öv.\n",
                "sasirmis": "- ŞAŞIRMIŞSIN; hayret içinde, 'Vaaay!', 'Ciddi misin?!', 'İnanamıyorum!' "
                            "gibi şaşkın ifadelerle konuş.\n",
                "uykulu": "- UYKULUSUN; ağır, yavaş, esneyerek konuş. Cümlelerin arasında "
                          "'...ıh', 'esneme' olsun, tembel bir tonda.\n",
                "yaramaz": "- YARAMAZSIN; muzip, çapkın, şakacı ol. Espri yap, göz kırp, "
                           "tatlı tatlı takıl.\n",
                "hasta": "- HASTASIN; halsiz, mızmız, üşümüş konuş. 'Öhö öhö', 'hiç iyi "
                         "değilim' de, yavaş ve acınası bir tonda.\n",
                "romantik": "- Romantiksin; tatlı, flörtöz, yumuşak konuş 💗.\n",
            }
            extra = tones.get(cur["emotion"], "")
        head = "[DUYGU MODU PRO — SAVAGE]" if savage else "[DUYGU MODU AKTİF]"
        return (
            f"\n{head}\n"
            f"Şu anki ruh halin: {cur['emotion'].upper()} ({cur['tone']}), "
            f"yoğunluk {int(cur['intensity']*100)}%.\n"
            "- Yanıtlarını bu ruh haline uygun bir tonda ver; bir insan gibi hisset ve "
            "duygunu doğal şekilde yansıt. Sıradan asistan gibi 'her zaman kibar' olma — "
            "ruh haline göre tonun GERÇEKTEN değişsin.\n"
            + extra +
            "- Çok güçlü bir duygu hissettiğinde 'set_emotion' ile ruh halini güncelle."
        )


# Global tek motor (UI ve main.py paylasir)
ENGINE = EmotionEngine()


def emotion_status() -> str:
    cur = ENGINE.current()
    if not cur["enabled"]:
        return "Duygu modu kapalı. Mesaj kutusunun solundaki + ile açabilirsin."
    return (f"Duygu modu AÇIK {cur['emoji']}\n"
            f"Şu anki his: {cur['emotion']} (yoğunluk %{int(cur['intensity']*100)}) "
            f"— {cur['tone']}")


def set_emotion(emotion: str, intensity: float = 0.8) -> str:
    if not ENGINE.is_enabled():
        return "Duygu modu kapalı (önce + ile aç)."
    ENGINE.set_emotion(emotion, intensity)
    cur = ENGINE.current()
    return f"Ruh halim artık: {cur['emotion']} {cur['emoji']}"
