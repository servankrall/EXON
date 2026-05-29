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

## 5. ✋ Barge-in — "Sözünü kesebilme"
EXON konuşurken sen konuşmaya başlarsan **otomatik susar ve seni dinler**. Ekstra
paket gerekmez, varsayılan **açık**tır.

- Kapatmak için `config/api_keys.json`: `"barge_in": false`
- Çok hassas/az hassas ise eşiği ayarla: `"barge_in_threshold": 900`
  (düşürürsen daha kolay tetiklenir, yükseltirsen daha zor).

## 6. 🧠 Yeni Araçlar (ek paket YOK, anahtarsız)
EXON'a doğal dille söyle:
- **Wikipedia hızlı-cevap:** "Atatürk kimdir", "kuantum bilgisayar nedir" → anında özet.
- **Döviz/Kripto:** "dolar kaç TL", "1 bitcoin kaç dolar", "100 euro kaç TL".
- **Çeviri:** "şunu İngilizceye çevir: ...".
- **Dosya arama:** "masaüstünde rapor.pdf var mı", "indirilenlerde sunum bul".

## 7. 📧 E-posta (Gmail) — okuma & gönderme
OAuth gerekmez; Google **uygulama şifresi** kullanılır.

1. Google Hesabı → Güvenlik → **2 Adımlı Doğrulama**'yı aç.
2. **Uygulama şifreleri**'nden 16 haneli bir şifre oluştur.
3. `config/api_keys.json`:
   ```json
   "gmail_address": "ornek@gmail.com",
   "gmail_app_password": "16haneliuygulamasifresi"
   ```
4. EXON'a "maillerimi oku" veya "şu kişiye mail gönder" de.

## 8. 🏷 Kimlik — EXON Robotik
EXON artık kendini **EXON Robotik** firmasının ürünü olarak tanıtır. "Seni kim
yaptı?" sorusuna "EXON Robotik firması tarafından geliştirildim" yanıtını verir.
Arayüz de (açılış logosu, başlık, altbilgi) EXON Robotik kimliğine göre yenilendi.

## 9. 🎮 Sistem Kontrolü — oyun modu, kapatma, ses (ek paket YOK)
EXON'a doğal dille söyle:
- **Oyun modu:** "oyun moduna geç" → **Yüksek Performans** güç planı açılır + EXON
  kendi animasyon/kaynak yükünü düşürür. "normal moda dön" ile kapatırsın.
- **Uygulama kapatma:** "Spotify'ı kapat" (belirli) ya da "açtığın uygulamaları kapat"
  (EXON'un o oturumda açtıklarını kapatır). explorer gibi kritik süreçler korunur.
- **Sekme kapatma:** "sekmeyi kapat" → sadece aktif **tarayıcı sekmesi** kapanır
  (tarayıcının kendisi kapanmaz).
- **Ses:** "sesi aç / kıs / sustur".
- **Ekran görüntüsü:** "ekran görüntüsü al" → `screenshots/` klasörüne kaydeder.
- **Güç:** "bilgisayarı kilitle / uyut / yeniden başlat / kapat". Kapatma ve yeniden
  başlatmada EXON önce **onay** ister; kilitle/uyut için istemez.

## 10. 🤖 Robot Yüz, Şarkı, Kod Asistanı (ek paket YOK)
- **Robot yüzü:** Ortadaki tasarım artık **moda göre ifade değiştiren** bir robot
  kafası: dinleme = gülümseme, konuşma = ağız oynar, düşünme = yukarı bakış + noktalar,
  hata = kızgın, duraklatma = uyuyor (zz), oyun modu = vizör + tarama çizgisi.
- **Şarkı:** "rap yap", "pop söyle", "duygusal bir şarkı söyle" → EXON istenen **tür ve
  dilde anlamlı söz** yazıp seslendirir; **arkada o türe uygun bir ritim** otomatik çalar
  ve **tonunu ruh haline göre** ayarlar (mutlu=canlı, hüzünlü=içten, rap=ritmik).
- **Kod asistanı:** "şu dosyamı oku", "projede X'i ara", "şunu düzelt" → kodlarını okur,
  arar, açıklar ve (söyleyince) düzeltme yazar.
- **Haber & borsa:** "gündemi özetle", "Tesla hissesi kaç", "BIST ne durumda".
- **Kişilik:** Sıcak ve enerjik; arada bir hafif espri yapar, açılışta seni **kişisel
  olarak selamlar**.

---

### Hepsini bir arada kurmak
```
pip install pvporcupine opencv-contrib-python discord.py
```
Sonra `config/api_keys.json` içine ilgili anahtarları gir ve `run.bat` ile başlat.
