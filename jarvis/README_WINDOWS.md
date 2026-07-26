# JARVIS Windows Edition

**Servan Kanğal** tarafından geliştirilen JARVIS projesinin Windows portu.

---

## Yapılan Değişiklikler (macOS → Windows)

| Bileşen | macOS | Windows |
|---|---|---|
| **Ses çalma** | `afplay` (subprocess) | `pygame.mixer` |
| **TTS** | `say` komutu | `pyttsx3` + PowerShell SAPI |
| **Uygulama açma** | `open -a AppName` | `os.startfile` / `winreg` / `start` |
| **URL açma** | `subprocess open url` | `webbrowser.open()` |
| **Pano kopyalama** | `pbcopy` | `pyperclip` / `clip.exe` |
| **Klavye otomasyonu** | `osascript` (AppleScript) | `pyautogui` |
| **Ekran görüntüsü** | Swift helper + CoreGraphics | `PIL.ImageGrab` + `win32gui` |
| **Apple Calendar** | Swift EventKit helper | Yerel JSON (`memory/calendar.json`) |
| **Apple Reminders** | Swift EventKit helper | Yerel JSON (`memory/reminders.json`) |
| **Apple Health** | iCloud / HealthKit | Manuel JSON (`memory/health/health_data.json`) |
| **WiFi bilgisi** | `airport` komutu | `netsh wlan show interfaces` |
| **Pil bilgisi** | `pmset -g batt` | `psutil.sensors_battery()` |
| **Klavye kısayolları** | `⌘+M`, `⌘+F` | `Ctrl+M`, `Ctrl+F` |
| **Tam ekran** | `⌘+F` | `F11` / `Ctrl+F` |
| **Kurulum** | `setup.sh` (bash) | `setup.bat` (Windows) |

---

## Kurulum

### Gereksinimler
- Windows 10/11 (64-bit)
- Python 3.11 veya üzeri
- Mikrofon (ses girişi için)

### Hızlı Kurulum

```
setup.bat çift tıkla
```

### Manuel Kurulum

```cmd
pip install -r requirements.txt
```

PyAudio kurulumunda sorun çıkarsa:
```cmd
pip install pipwin
pipwin install pyaudio
```

---

## Başlatma

```
run.bat çift tıkla
```
veya
```cmd
python main.py
```

---

## Klavye Kısayolları

| Kısayol | Fonksiyon |
|---|---|
| `F4` / `Ctrl+M` | Mikrofon aç/kapat |
| `F5` | Duraklat / Devam et |
| `F11` / `Ctrl+F` | Tam ekran |
| `ESC` | Kapat |

---

## Yeni Özellikler (Windows'a Özgü)

### Yerel Takvim (`actions/calendar.py`)
Apple Calendar yerine JSON tabanlı yerel takvim sistemi.
- Dosya: `memory/calendar.json`
- Etkinlik ekleme, listeleme, silme desteklenir.

### Yerel Hatırlatıcı (`actions/reminders.py`)
Apple Reminders yerine JSON tabanlı yerel hatırlatıcı sistemi.
- Dosya: `memory/reminders.json`
- Bugün / yaklaşan / geciken filtreleme desteklenir.

### Sağlık Verisi (`actions/health.py`)
Apple HealthKit Windows'ta mevcut değil. Manuel JSON ile kullanılabilir:

1. iPhone'da **Health Auto Export** uygulamasını kullan
2. Dışa aktarılan JSON verisini şu konuma kaydet:
   ```
   memory/health/health_data.json
   ```
3. Format:
   ```json
   {
     "heart_rate": 72,
     "resting_hr": 60,
     "hrv": 45,
     "blood_oxygen": 98.5,
     "steps": 8000,
     "calories": 450,
     "exercise_min": 35,
     "sleep_hours": 7.5
   }
   ```

---

## Uygulama Desteği

| Uygulama | macOS | Windows |
|---|---|---|
| Spotify | ✅ | ✅ (URI scheme) |
| Chrome / Firefox / Edge | ✅ | ✅ |
| VS Code | ✅ | ✅ |
| WhatsApp | ✅ | ✅ (Desktop URL scheme) |
| Discord / Slack / Telegram | ✅ | ✅ |
| Zoom / Teams | ✅ | ✅ |
| Hesap Makinesi | ✅ | ✅ (`calc`) |
| Görev Yöneticisi | Activity Monitor | ✅ (`taskmgr`) |
| Ayarlar | System Preferences | ✅ (`ms-settings:`) |
| Apple Music | ✅ | ❌ → WMP/Groove |
| iCal / Reminders | ✅ | Yerel JSON |
| Safari | ✅ | ❌ |
| Xcode | ✅ | ❌ |

---

## Sorun Giderme

**`No module named 'tkinter'` hatası:**
tkinter **pip ile kurulmaz**; Python ile birlikte gelir. Python kurulumunda "tcl/tk and
IDLE" bileşeni seçilmemiş demektir. Çözüm:
- **Ayarlar > Uygulamalar > Yüklü uygulamalar > Python 3.x > ... > Değiştir (Modify)**
- **"tcl/tk and IDLE"** kutusunu işaretle > **Modify**
- Ya da [python.org](https://www.python.org/downloads/)'dan Python'u tekrar kurarken bu
  kutuyu işaretle. (Microsoft Store sürümünde sorun çıkarsa python.org sürümünü kullan.)

**PyAudio kurulmuyor:**
```cmd
pip install pipwin
pipwin install pyaudio
```
Hâlâ sorun varsa: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

**win32gui / pywin32 hatası:**
```cmd
pip install pywin32
python Scripts/pywin32_postinstall.py -install
```

**Ekran görüntüsü siyah geliyor:**
- Windows Gizlilik Ayarları > Ekran yakalama'yı kontrol et
- pywin32 veya pygetwindow kurulu olduğundan emin ol

**TTS (ses okuma) çalışmıyor:**
```cmd
pip install pyttsx3
```
pyttsx3 çalışmazsa PowerShell SAPI otomatik devreye girer.

---

## Lisans

Orijinal proje: Servan Kanğal  
Windows portu, aynı lisans kapsamında dağıtılır.
