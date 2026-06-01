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
    "kizgin":    ("😠", (255, 90, 90),   "kararlı, sert ama saygılı"),
    "sefkatli":  ("🥰", (255, 130, 180), "şefkatli, destekleyici ve anlayışlı"),
}

# Kullanici mesajindaki ipuclari -> duygu (anahtar kelime tetikleyici)
_TRIGGERS = {
    "mutlu":     ("harika", "süper", "mükemmel", "teşekkür", "sevdim", "muhtesem",
                  "başardık", "kazandık", "güzel", "sevindim", "yaşasın", "bravo"),
    "heyecanli": ("inanılmaz", "çok heyecanlı", "vay", "wow", "efsane", "delirdim",
                  "muazzam", "çılgın", "bomba"),
    "uzgun":     ("üzgün", "kötü", "moralim", "yorgun", "bıktım", "berbat",
                  "ağladım", "depresif", "mutsuz", "canım sıkkın", "hüzün"),
    "kizgin":    ("sinir", "kızgın", "öfke", "saçma", "berbat", "rezalet",
                  "of ya", "delirtiyor", "bıktırdın"),
    "merakli":   ("neden", "nasıl", "acaba", "merak", "öğrenmek istiyorum",
                  "anlamadım", "ne demek"),
    "sefkatli":  ("yalnızım", "destek", "yardım et", "korkuyorum", "endişe",
                  "kaygı", "hastayım", "iyi değilim"),
}


class EmotionEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._enabled = False
        self._emotion = "notr"
        self._intensity = 0.0          # 0..1
        self._updated = time.time()
        self._decay_secs = 90.0        # ~1.5 dk'da notr'e doner

    # ── Acma/kapama ──────────────────────────────────────────────────────────
    def set_enabled(self, value: bool) -> None:
        with self._lock:
            self._enabled = bool(value)
            if not value:
                self._emotion = "notr"
                self._intensity = 0.0

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def toggle(self) -> bool:
        with self._lock:
            self._enabled = not self._enabled
            if not self._enabled:
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
            self._emotion = emotion
            self._intensity = max(0.0, min(1.0, float(intensity)))
            self._updated = time.time()

    # ── Konusmadan duygu cikar ───────────────────────────────────────────────
    def sense_from_text(self, text: str) -> None:
        """Kullanicinin mesajindan bir duygu sezip durumu gunceller."""
        with self._lock:
            if not self._enabled:
                return
        low = (text or "").lower()
        if not low:
            return
        best = None
        for emo, words in _TRIGGERS.items():
            hits = sum(1 for w in words if w in low)
            if hits:
                best = (emo, min(1.0, 0.55 + hits * 0.15))
                break
        if best:
            self.set_emotion(best[0], best[1])

    # ── Prompt eki ───────────────────────────────────────────────────────────
    def prompt_addition(self) -> str:
        cur = self.current()
        if not cur["enabled"]:
            return ""
        return (
            "\n[DUYGU MODU AKTİF]\n"
            f"Şu anki ruh halin: {cur['emotion'].upper()} ({cur['tone']}), "
            f"yoğunluk {int(cur['intensity']*100)}%.\n"
            "- Yanıtlarını bu ruh haline uygun bir tonda ver; bir insan gibi hisset ve "
            "duygunu doğal şekilde yansıt (abartma, profesyonelliğini koru).\n"
            "- Kullanıcının duygusuna empatiyle karşılık ver: üzgünse destekle/neşelendir, "
            "heyecanlıysa coşkusunu paylaş, kızgınsa sakinleştir.\n"
            "- Çok güçlü bir duygu hissettiğinde, uygun bir 'set_emotion' çağrısıyla "
            "ruh halini güncelleyebilirsin."
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
