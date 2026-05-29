<div align="center">

# 🤖 EXON · EXON Robotik

**Gerçek zamanlı, sesli, çok yetenekli kişisel yapay zekâ asistanı.**

Windows için • Türkçe öncelikli • Google Gemini Live tabanlı

</div>

---

## ✨ EXON Nedir?

EXON, **EXON Robotik** tarafından geliştirilen; sesinizle konuşan, internette
derinlemesine araştırma yapan, bilgisayarınızı yöneten, kod yazarken size yardım
eden ve hatta şarkı söyleyebilen bir kişisel yapay zekâ asistanıdır. Ortadaki
**robot yüzü**, EXON'un o anki ruh hâline göre ifade değiştirir (dinleme, konuşma,
düşünme, oyun modu...).

> "Seni kim üretti?" → **EXON Robotik firması.**

---

## 🚀 Öne Çıkan Özellikler

| Alan | Yetenekler |
|---|---|
| 🔎 **Araştırma & Bilgi** | Paralel çok-motorlu web araması, Wikipedia hızlı özet, haber brifingi, YouTube kanal analizi |
| 💱 **Finans** | Döviz & kripto çevirme, hisse/endeks fiyatları (BIST, ABD, kripto) |
| 🗓️ **Üretkenlik** | Takvim, hatırlatıcılar, zamanlanmış/tekrarlayan görevler |
| 💬 **İletişim** | WhatsApp mesajı, Gmail okuma & gönderme |
| 🖥️ **Sistem & Kontrol** | Uygulama aç/kapat, sekme kapat, **oyun modu** (performans), güç (kilitle/uyut/kapat), ses, ekran görüntüsü, dosya arama |
| 🎨 **Yaratıcılık & Medya** | Görsel üretme, müzik/video oynatma, **şarkı yazma & söyleme** (rap/pop/duygusal, her dilde) |
| 👨‍💻 **Kod Asistanı** | Kodlarınızı okur, arar, açıklar ve düzeltme yazar |
| 👁️ **Görü & Hafıza** | Ekran analizi, yüz tanıma, kalıcı hafıza |
| 🗣️ **Etkileşim** | Doğal sesli sohbet, **söz kesme (barge-in)**, "Hey EXON" ile uyanma, kişisel karşılama, arada bir espri |

**Toplam 40+ araç** — hepsi doğal dille, konuşarak.

---

## ⚡ Hızlı Kurulum (Windows)

```cmd
git clone https://github.com/servankrall/EXON.git
cd EXON\jarvis
pip install -r requirements.txt
python main.py
```
veya `jarvis\setup.bat` → `jarvis\run.bat` çift tıkla.

İlk açılışta **Gemini API anahtarınızı** girin (ekran sizi yönlendirir).
Anahtarı [Google AI Studio](https://aistudio.google.com/apikey)'dan ücretsiz alabilirsiniz.

---

## 🔑 Yapılandırma

Ayarlar `jarvis/config/api_keys.json` dosyasında tutulur (örnek: `api_keys.example.json`).

| Anahtar | Açıklama | Zorunlu mu? |
|---|---|---|
| `gemini_api_key` | Gemini API anahtarı | ✅ Evet |
| `voice` | EXON'un sesi (Charon, Puck, Kore...) | Hayır |
| `youtube_api_key` / `youtube_channel_handle` | YouTube analizi | Opsiyonel |
| `gmail_address` / `gmail_app_password` | E-posta (Google uygulama şifresi) | Opsiyonel |
| `picovoice_access_key` | "Hey EXON" uyandırma sözcüğü | Opsiyonel |
| `telegram_bot_token` / `discord_bot_token` | Uzaktan komut köprüleri | Opsiyonel |
| `barge_in` / `barge_in_threshold` | Söz kesme davranışı | Varsayılan açık |

Ayrıntılı ileri özellik kurulumu: [`jarvis/ILERI_OZELLIKLER.md`](jarvis/ILERI_OZELLIKLER.md)

---

## 🎙️ Örnek Komutlar

- *"Bitcoin kaç dolar? Bir de Aselsan hissesi ne durumda?"*
- *"Bugünün gündemini özetle."*
- *"Oyun moduna geç."* → yüksek performans + EXON kendi yükünü düşürür
- *"Açtığın uygulamaları kapat."* / *"Sekmeyi kapat."*
- *"Bana motive edici bir rap yaz ve söyle."*
- *"Masaüstündeki main.py dosyamı oku, hatayı bul."*
- *"Şunu İngilizceye çevir."* / *"Ekran görüntüsü al."*

---

## ⌨️ Kısayollar

| Kısayol | İşlev |
|---|---|
| `F4` / `Ctrl+M` | Mikrofon aç/kapat |
| `F5` | Duraklat / Devam |
| `F11` / `Ctrl+F` | Tam ekran |
| `ESC` | Çıkış |

---

## 🏗️ Mimari

```
jarvis/
├── main.py            # Çekirdek: Gemini Live oturumu, araç yönlendirme, ses akışı
├── ui.py              # HUD arayüz + moda göre değişen robot yüzü
├── app_config.py      # Yapılandırma yönetimi
├── bot_bridge.py      # Telegram / Discord köprüleri
├── core/prompt.txt    # (eski) sistem istemi referansı
├── memory/            # Kalıcı hafıza, takvim, hatırlatıcılar (JSON)
└── actions/           # Her yetenek ayrı bir modül (araştırma, finans, kod, şarkı...)
```

EXON, Google **Gemini Live** (native ses) modelini kullanır; araçları
gerçek zamanlı olarak çağırarak hem konuşur hem iş yapar.

---

## 📄 Lisans & Geliştirici

Geliştiren: **EXON Robotik** — yapay zekâ ve robotik çözümler.
Proje sahibi: Servan Kanğal.

<div align="center">

*EXON Robotik · Gelişmiş Yapay Zekâ Asistanı*

</div>
