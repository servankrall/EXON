"""
Guvenlik & Veri korumasi.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- Sifreli hafiza yedegi (parola tabanli, stdlib): hassas verileri sifreli .enc'e al/coz.
- Veri butunlugu kontrolu: onemli JSON dosyalarinin SHA-256 ozetini kaydet/dogrula.
- Guvenlik gunlugu: olaylari yerel guvenlik.log'a yazar.
- Kurtarma/acil durum: bozuk JSON'lari yedekten/bos sablondan onarir.

Harici paket gerekmez; sifreleme stdlib (hashlib PBKDF2 + XOR akis) ile yapilir.
Bu, askeri seviye degildir ama yerel/elle kurcalama'ya karsi makul koruma saglar.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from paths import DATA_DIR

_SEC_DIR = DATA_DIR / "security"
_LOG_FILE = _SEC_DIR / "guvenlik.log"
_HASH_FILE = _SEC_DIR / "integrity.json"


def _ensure_dir() -> None:
    try:
        _SEC_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ── Guvenlik gunlugu ─────────────────────────────────────────────────────────
def log_security(event: str) -> None:
    _ensure_dir()
    try:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {event}\n")
    except Exception:
        pass


def read_security_log(lines: int = 20) -> str:
    if not _LOG_FILE.exists():
        return "Güvenlik günlüğü henüz boş."
    try:
        all_lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
        tail = all_lines[-max(1, min(lines, 100)):]
        return "Son güvenlik olayları:\n" + "\n".join(tail)
    except Exception as exc:
        return f"Günlük okunamadı: {exc}"


# ── Sifreleme (PBKDF2 turetilmis anahtar + HMAC dogrulama) ───────────────────
def _derive_key(password: str, salt: bytes, length: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt,
                               200_000, dklen=length)


def _keystream(key: bytes, nbytes: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < nbytes:
        out += hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:nbytes])


def encrypt_data(plaintext: str, password: str) -> bytes:
    salt = os.urandom(16)
    enc_key = _derive_key(password, salt, 32)
    mac_key = _derive_key(password, salt + b"mac", 32)
    data = plaintext.encode("utf-8")
    cipher = bytes(a ^ b for a, b in zip(data, _keystream(enc_key, len(data))))
    tag = hmac.new(mac_key, salt + cipher, hashlib.sha256).digest()
    return b"EXON1" + salt + tag + cipher


def decrypt_data(blob: bytes, password: str) -> str | None:
    try:
        if blob[:5] != b"EXON1":
            return None
        salt = blob[5:21]
        tag = blob[21:53]
        cipher = blob[53:]
        mac_key = _derive_key(password, salt + b"mac", 32)
        if not hmac.compare_digest(tag, hmac.new(mac_key, salt + cipher,
                                                 hashlib.sha256).digest()):
            return None  # yanlis parola veya bozulmus veri
        enc_key = _derive_key(password, salt, 32)
        data = bytes(a ^ b for a, b in zip(cipher, _keystream(enc_key, len(cipher))))
        return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def encrypt_memory(password: str) -> str:
    """memory.json'u sifreli yedege (memory.enc) alir."""
    if not password or len(password) < 4:
        return "Parola en az 4 karakter olmalı."
    src = DATA_DIR / "memory" / "memory.json"
    if not src.exists():
        return "Şifrelenecek hafıza dosyası yok."
    _ensure_dir()
    try:
        blob = encrypt_data(src.read_text(encoding="utf-8"), password)
        (_SEC_DIR / "memory.enc").write_bytes(blob)
        log_security("Hafıza şifreli yedeği oluşturuldu.")
        return "Hafıza şifreli olarak yedeklendi (security/memory.enc)."
    except Exception as exc:
        return f"Şifreleme başarısız: {exc}"


def decrypt_memory(password: str) -> str:
    """memory.enc'i cozer (icerigi dondurur; dosyanin ustune YAZMAZ)."""
    enc = _SEC_DIR / "memory.enc"
    if not enc.exists():
        return "Şifreli yedek bulunamadı."
    text = decrypt_data(enc.read_bytes(), password)
    if text is None:
        log_security("Şifreli hafıza çözme BAŞARISIZ (yanlış parola?).")
        return "Çözme başarısız: parola yanlış veya veri bozuk."
    log_security("Şifreli hafıza başarıyla çözüldü.")
    return "Çözme başarılı. İçerik:\n" + text[:1500]


# ── Veri butunlugu ───────────────────────────────────────────────────────────
_WATCHED = ("memory/memory.json", "config/api_keys.json",
            "memory/calendar.json", "memory/reminders.json")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_integrity() -> str:
    """Izlenen dosyalarin guncel ozetini kaydeder (referans olusturur)."""
    _ensure_dir()
    hashes = {}
    for rel in _WATCHED:
        p = DATA_DIR / rel
        if p.exists():
            try:
                hashes[rel] = _sha256_file(p)
            except Exception:
                pass
    try:
        _HASH_FILE.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
        log_security("Veri bütünlüğü referansı güncellendi.")
        return f"Bütünlük referansı kaydedildi ({len(hashes)} dosya)."
    except Exception as exc:
        return f"Referans kaydedilemedi: {exc}"


def verify_integrity() -> str:
    """Dosyalar son referanstan beri DEGISTI mi kontrol eder."""
    if not _HASH_FILE.exists():
        return ("Henüz bütünlük referansı yok. Önce 'snapshot' alınmalı "
                "(EXON ilk güvenli kaydı oluşturur).")
    try:
        ref = json.loads(_HASH_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "Referans dosyası okunamadı."
    changed, missing, ok = [], [], 0
    for rel, old in ref.items():
        p = DATA_DIR / rel
        if not p.exists():
            missing.append(rel)
            continue
        try:
            if _sha256_file(p) != old:
                changed.append(rel)
            else:
                ok += 1
        except Exception:
            changed.append(rel)
    if not changed and not missing:
        return f"Veri bütünlüğü TAMAM ✓ ({ok} dosya değişmemiş)."
    msg = ["Veri bütünlüğü uyarısı:"]
    if changed:
        msg.append("Değişen: " + ", ".join(changed))
    if missing:
        msg.append("Kayıp: " + ", ".join(missing))
    log_security("Bütünlük kontrolü: " + "; ".join(msg))
    return "\n".join(msg)


# ── Kurtarma / Acil durum ────────────────────────────────────────────────────
def recover_json(rel_path: str) -> str:
    """Bozuk bir JSON dosyasini yedekler ve bos {} ile onarir (acil kurtarma)."""
    p = DATA_DIR / rel_path
    if not p.exists():
        return f"Dosya yok: {rel_path}"
    try:
        json.loads(p.read_text(encoding="utf-8"))
        return f"{rel_path} zaten geçerli, kurtarmaya gerek yok."
    except Exception:
        pass
    try:
        bak = p.with_suffix(p.suffix + f".bozuk_{int(time.time())}")
        p.rename(bak)
        p.write_text("{}", encoding="utf-8")
        log_security(f"Bozuk JSON kurtarıldı: {rel_path} (yedek: {bak.name})")
        return f"{rel_path} bozuktu; yedeklendi ({bak.name}) ve sıfırlandı."
    except Exception as exc:
        return f"Kurtarma başarısız: {exc}"


def security_report() -> str:
    """Genel guvenlik durumu ozeti (gelistirici/kullanici icin)."""
    lines = ["[GÜVENLİK DURUMU]"]
    lines.append("Bütünlük: " + verify_integrity().split("\n")[0])
    enc = _SEC_DIR / "memory.enc"
    lines.append("Şifreli yedek: " + ("var ✓" if enc.exists() else "yok"))
    lines.append("Günlük: " + ("aktif" if _LOG_FILE.exists() else "henüz boş"))
    return "\n".join(lines)
