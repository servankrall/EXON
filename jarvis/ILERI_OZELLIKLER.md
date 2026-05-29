# EXON — İleri Seviye Özellikler Kurulumu

Tüm özellikler **opsiyoneldir**. İlgili paket/anahtar yoksa o özellik sessizce
devre dışı kalır; EXON yine normal çalışır. Anahtarları `config/api_keys.json`
dosyasına yaz.

---

## 1. 🔔 Uyandırma Sözcüğü — "Hey EXON"
EXON arka planda **standby** (mikrofon kapalı) başlar; sözcüğü duyunca uyanır ve
"Efendim?" der.

1. `pip install pvporcupine`
2. [console.picovoice.ai](https://console.picovoice.ai) → ücretsiz **AccessKey** al →
   `config/api_keys.json` içine: `"picovoice_access_key": "BURAYA"`
3. **"Hey EXON"** için: aynı konsolda *Porcupine → Wake Word* ile özel sözcük eğit,
   **Windows (.ppn)** indir, `wake/Hey-EXON_windows.ppn` olarak koy.
   - Özel dosya yoksa hazır **"Jarvis"** sözcüğüne düşer (yine de çalışır).
4. Başlat: EXON "standby" açılır. *Hey EXON* (veya Jarvis) de → uyanır.
   Tekrar uyutmak için **F4** (mute).

## 2. 📸 Yüz Tanıma — kameradan kişi tanıma
1. `pip install opencv-contrib-python`
2. `faces/<isim>/` klasörü aç, o kişinin birkaç net yüz fotoğrafını koy.
   Örn: `faces/Servan/1.jpg`, `faces/Servan/2.jpg`, `faces/Felat/1.jpg` ...
3. EXON'a "beni tanı" / "kameradan kim olduğumu bul" de → `recognize_face` çalışır.

## 3. ⏰ Görev Otomasyonu (Planlayıcı) — HAZIR, ek paket yok
EXON'a doğal dille söyle:
- "Her sabah 8'de bana hava durumunu söyle"
- "Her gün 22:00'de su içmeyi hatırlat"

Görevler `memory/scheduled_tasks.json`'a kaydedilir, vakti gelince EXON otomatik
sesli yapar. "Zamanlanmış görevlerimi say" / "şu görevi sil" de.

## 4. 📲 Telegram / Discord — telefondan komut
Bilgisayar **açıkken** telefondan komut gönderirsin; EXON yazı/görsel döner.

### Telegram (ek paket gerekmez)
1. Telegram'da [@BotFather](https://t.me/BotFather) → `/newbot` → token al
2. `config/api_keys.json`: `"telegram_bot_token": "BURAYA"`
3. Botuna yaz: `/hava`, `/ara Felat Kanğal`, `/gorsel neon mavi robot`, veya
   doğrudan soru.

### Discord (opsiyonel)
1. `pip install discord.py`
2. [Developer Portal](https://discord.com/developers) → Bot oluştur → **Message
   Content Intent**'i aç → token al → `"discord_bot_token": "BURAYA"`
3. Botu sunucuna ekle, mesaj yaz.

---

### Hepsini bir arada kurmak
```
pip install pvporcupine opencv-contrib-python discord.py
```
Sonra `config/api_keys.json` içine ilgili anahtarları gir ve `run.bat` ile başlat.
