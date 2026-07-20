"""
Gmail okuma/gonderme — IMAP/SMTP + uygulama sifresi (app password).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Kurulum (anahtar yerine Google 'uygulama sifresi' kullanilir; OAuth gerekmez):
1. Google Hesabi > Guvenlik > 2 Adimli Dogrulama'yi ac.
2. 'Uygulama sifreleri'nden 16 haneli bir sifre olustur.
3. config/api_keys.json icine:
     "gmail_address": "ornek@gmail.com",
     "gmail_app_password": "16hanesifre"
Anahtarlar yoksa arac kibarca uyarir; baska bir sey bozulmaz.
Tum bagimliliklar Python standart kutuphanesindedir (imaplib/smtplib/email).
"""

from __future__ import annotations

import imaplib
import smtplib
import email
from email.header import decode_header, make_header
from email.message import EmailMessage

from app_config import get_app_config_value


IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _creds() -> tuple[str, str] | None:
    addr = str(get_app_config_value("gmail_address", "") or "").strip()
    pw = str(get_app_config_value("gmail_app_password", "") or "").strip().replace(" ", "")
    if addr and pw:
        return addr, pw
    return None


def _decode(value) -> str:
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return str(value or "")


def _body_snippet(msg, limit: int = 240) -> str:
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and \
                        "attachment" not in str(part.get("Content-Disposition", "")):
                    payload = part.get_payload(decode=True) or b""
                    text = payload.decode(part.get_content_charset() or "utf-8",
                                          errors="replace")
                    return " ".join(text.split())[:limit]
        else:
            payload = msg.get_payload(decode=True) or b""
            text = payload.decode(msg.get_content_charset() or "utf-8",
                                  errors="replace")
            return " ".join(text.split())[:limit]
    except Exception:
        pass
    return ""


def read_recent_emails(count: int = 5) -> str:
    """Gelen kutusundaki en son e-postalari okur (gonderen, konu, kisa ozet)."""
    creds = _creds()
    if not creds:
        return ("Gmail ayarli degil. config/api_keys.json icine 'gmail_address' ve "
                "'gmail_app_password' (Google uygulama sifresi) ekle.")
    try:
        count = max(1, min(int(count or 5), 15))
    except (TypeError, ValueError):
        count = 5

    addr, pw = creds
    try:
        with imaplib.IMAP4_SSL(IMAP_HOST) as imap:
            imap.login(addr, pw)
            imap.select("INBOX")
            status, data = imap.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                return "Gelen kutusu bos gorunuyor."
            ids = data[0].split()
            latest = ids[-count:][::-1]
            out = []
            for i, mid in enumerate(latest, 1):
                status, msg_data = imap.fetch(mid, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                sender = _decode(msg.get("From"))
                subject = _decode(msg.get("Subject")) or "(konu yok)"
                snippet = _body_snippet(msg)
                block = f"{i}. {subject}\n   Gonderen: {sender}"
                if snippet:
                    block += f"\n   Ozet: {snippet}"
                out.append(block)
            if not out:
                return "E-posta okunamadi."
            return f"Son {len(out)} e-posta:\n\n" + "\n\n".join(out)
    except imaplib.IMAP4.error:
        return ("Gmail girisi basarisiz. Uygulama sifresinin dogru oldugundan ve "
                "2 Adimli Dogrulamanin acik oldugundan emin ol.")
    except Exception as exc:
        return f"E-posta okunamadi: {exc}"


def send_email(to: str, subject: str, body: str) -> str:
    """Verilen alici(lar)a e-posta gonderir. to virgulle ayrilmis olabilir."""
    creds = _creds()
    if not creds:
        return ("Gmail ayarli degil. config/api_keys.json icine 'gmail_address' ve "
                "'gmail_app_password' ekle.")
    to = (to or "").strip()
    if not to:
        return "Alici e-posta adresini ver."
    addr, pw = creds

    message = EmailMessage()
    # Gönderen adı "EXON" görünsün (adres yine hesabın kendisi).
    message["From"] = f"EXON <{addr}>"
    message["To"] = to
    message["Subject"] = (subject or "(konu yok)").strip()
    message.set_content(body or "")

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(addr, pw)
            smtp.send_message(message)
        return f"E-posta gonderildi: {to} -> '{message['Subject']}'."
    except smtplib.SMTPAuthenticationError:
        return ("Gmail girisi basarisiz. Uygulama sifresini kontrol et "
                "(normal sifre degil, 16 haneli uygulama sifresi gerekir).")
    except Exception as exc:
        return f"E-posta gonderilemedi: {exc}"
