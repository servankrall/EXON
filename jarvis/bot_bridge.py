"""
EXON Köprüsü — Telegram / Discord üzerinden telefondan komut.
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Bilgisayar AÇIKKEN telefonundan EXON'a komut gönderirsin; EXON cevabı (yazı/görsel)
geri yollar. main.py bu köprüleri başlatır ve bir 'handler(text)->dict' verir.

Kurulum:
- Telegram: @BotFather'dan token al → config "telegram_bot_token".
- Discord (opsiyonel): Developer Portal'dan bot token + Message Content Intent →
  config "discord_bot_token" (pip install discord.py).

handler(text) şu sözlüğü döndürür: {"text": str, "image": str|None}
"""

from __future__ import annotations

import threading
import time

import requests

from app_config import get_app_config_value

try:
    import discord  # type: ignore
    _DISCORD_OK = True
except Exception:
    _DISCORD_OK = False


# ── Telegram (ek kütüphane gerektirmez, sadece requests) ─────────────────────
class TelegramBridge:
    def __init__(self, handler):
        self.handler = handler
        self.token = str(get_app_config_value("telegram_bot_token", "") or "").strip()
        self.enabled = bool(self.token)
        self._stop = False
        self._offset = 0
        self._thread = None

    @property
    def _api(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    def start(self):
        if not self.enabled or (self._thread and self._thread.is_alive()):
            return
        self._stop = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def _loop(self):
        while not self._stop:
            try:
                r = requests.get(f"{self._api}/getUpdates",
                                 params={"timeout": 30, "offset": self._offset},
                                 timeout=40)
                for upd in (r.json().get("result", []) if r.ok else []):
                    self._offset = upd["update_id"] + 1
                    msg = upd.get("message") or upd.get("edited_message") or {}
                    chat = (msg.get("chat") or {}).get("id")
                    text = msg.get("text", "")
                    if chat and text:
                        threading.Thread(target=self._handle,
                                         args=(chat, text), daemon=True).start()
            except Exception:
                time.sleep(3)

    def _handle(self, chat_id, text):
        try:
            res = self.handler(text) or {}
        except Exception as exc:
            res = {"text": f"Hata: {exc}"}
        reply = res.get("text", "") or ""
        image = res.get("image")
        if image:
            self.send_photo(chat_id, image, caption=reply[:1000])
        elif reply:
            self.send_message(chat_id, reply)

    def send_message(self, chat_id, text):
        text = text or "."
        for i in range(0, len(text), 4000):
            try:
                requests.post(f"{self._api}/sendMessage",
                              data={"chat_id": chat_id, "text": text[i:i + 4000]},
                              timeout=20)
            except Exception:
                pass

    def send_photo(self, chat_id, path, caption=""):
        try:
            with open(path, "rb") as f:
                requests.post(f"{self._api}/sendPhoto",
                              data={"chat_id": chat_id, "caption": caption},
                              files={"photo": f}, timeout=60)
        except Exception:
            self.send_message(chat_id, caption or "Görsel gönderilemedi.")


# ── Discord (opsiyonel — discord.py gerekir) ─────────────────────────────────
class DiscordBridge:
    def __init__(self, handler):
        self.handler = handler
        self.token = str(get_app_config_value("discord_bot_token", "") or "").strip()
        self.enabled = bool(self.token) and _DISCORD_OK
        self._thread = None
        if self.token and not _DISCORD_OK:
            print("[Discord] discord.py kurulu değil (pip install discord.py)")

    def start(self):
        if not self.enabled or (self._thread and self._thread.is_alive()):
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        import asyncio
        handler = self.handler
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)

        @client.event
        async def on_message(message):
            if message.author == client.user or not message.content:
                return
            res = await asyncio.to_thread(handler, message.content) or {}
            text = (res.get("text") or "")[:1900]
            image = res.get("image")
            try:
                if image:
                    await message.channel.send(content=text, file=discord.File(image))
                elif text:
                    await message.channel.send(text)
            except Exception:
                pass

        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            client.run(self.token)
        except Exception as exc:
            print(f"[Discord] çalıştırılamadı: {exc}")
