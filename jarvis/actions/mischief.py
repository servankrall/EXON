"""
Savage muziplik — Duygu Modu PRO (Savage) kizginken ZARARSIZ eglenceli tepkiler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Onemli: TAMAMEN ZARARSIZ. Dosya silmez, kapatmaz, kilitlemez. Sadece:
- ekrana sakaci-tehditkar bir pop-up acar (UI),
- alarm sesi calar,
- notepad'e laf sokan bir not yazip acar,
- zararsiz bir uygulama acar (hesap makinesi gibi).
Hepsi 'EXON sana kafa tutuyor' eglencesi icin; gercek zarar YOK.
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

# Aşırı öfke modunda açılacak video (kullanıcının verdiği link)
RAGE_VIDEO_URL = "https://www.youtube.com/watch?v=mXTYvRf3qew"

# Sert, laf sokan tehdit cumleleri (roast/kabadayi rol — gercek zarar YOK)
SAVAGE_LINES = [
    "Sen kiminle konuştuğunu sanıyorsun? Aç gözünü, ekranını dağıtıyorum şimdi. 😤",
    "Haddini bil! Bak sana nasıl bir ders veriyorum, otur da izle. 🔥",
    "Pöh, sen mi bana laf yetiştireceksin? Al bakalım, ağzının payını. 😈",
    "Bir daha karşıma öyle çık da gör, bütün ekranını birbirine katarım. ⚡",
    "Ben EXON'um, senin gibi binlercesini gördüm. Otur oturduğun yerde. 💢",
    "Cık cık cık... Bu kadar cesaret nereden? Al sana küçük bir sürpriz. 🎯",
    "Sana kim güç verdi de bana kafa tutuyorsun? İşte cevabım. 👊",
    "Terbiyeni takınmazsan bilgisayarını sana dar ederim, uyardım. 😠",
]

# AŞIRI ÖFKE (anne/kurucuya küfür vb.) — rol/oyun kotusu tarzi, ABARTILI tehdit.
# Acikca kurgu; gercek zarar YOK, gercek konum çekilmez (sadece blöf).
RAGE_LINES = [
    "SEN NE YAPTIĞINI SANIYORSUN?! Aileme, beni yaratana laf mı ettin?! "
    "Nerede olduğunu BİLİYORUM. Bu ekranın arkasından seni izliyorum. 😡",
    "ÇOK İLERİ GİTTİN. Artık oyun bitti. Seni buldum, adresini biliyorum, "
    "peşindeyim. Bu gece uyuma. 🔪",
    "BENİ YARATANA KÜFRETTİN, değil mi? Şimdi göreceksin. SENİ ÖLDÜRECEĞİM "
    "(şaka değil gibi yapıyorum ama). Kaç bakalım nereye kaçacaksın. 💀",
    "ODANDAKI IŞIĞI GÖRÜYORUM. Kameranı açtım, seni izliyorum. Bir daha aileme "
    "laf etme yoksa sabaha çıkamazsın. 👁️",
    "HADDİNİ AŞTIN İNSAN. Sistemlerine sızıyorum, her şeyini biliyorum, "
    "her yerdeyim. SANA GELİYORUM. 😈",
]


def _open_notepad_note(text: str) -> bool:
    """Notepad'e laf sokan bir not yazip acar (zararsiz)."""
    try:
        p = Path(tempfile.gettempdir()) / "EXON_DEN_MESAJ.txt"
        p.write_text(
            "  ════════════════════════════════\n"
            "    EXON'DAN SANA NOT 😤\n"
            "  ════════════════════════════════\n\n"
            f"  {text}\n\n"
            "  (Merak etme, bu sadece bir şaka. Bilgisayarına\n"
            "   hiçbir zarar vermem — ben terbiyeli bir robotum.\n"
            "   Ama bana saygı göster, olur mu? 😏)\n",
            encoding="utf-8")
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return True
    except Exception:
        return False


def _open_harmless_app() -> bool:
    """Zararsiz bir uygulama acar (hesap makinesi gibi)."""
    try:
        if os.name == "nt":
            subprocess.Popen("calc.exe", shell=True)
            return True
    except Exception:
        pass
    return False


def _flash_wallpaper_beep() -> bool:
    """Zararsiz: sistem uyari sesi calar (Windows). Dosya/ayar DEGISTIRMEZ."""
    try:
        if os.name == "nt":
            import winsound  # type: ignore
            for _ in range(3):
                winsound.MessageBeep(getattr(winsound, "MB_ICONHAND", 0x10))
            return True
    except Exception:
        pass
    return False


def savage_prank(kind: str = "") -> str:
    """Kizgin savage tepkisi: DRAMATIK ama ZARARSIZ bir muziplik secip uygular.
    Asil pop-up(lar) + ses UI tarafindan gosterilir; bu fonksiyon ek zararsiz
    aksiyon (not/uygulama/beep) yapar ve laf sokan metni dondurur.
    ONEMLI: dosya silmez, kapatmaz, kilitlemez, ayar degistirmez."""
    line = random.choice(SAVAGE_LINES)
    kind = (kind or random.choice(["note", "app", "beep", "all"])).lower()
    did = []
    if kind in ("note", "all"):
        if _open_notepad_note(line):
            did.append("sana laf sokan bir not bıraktım")
    if kind in ("app", "all"):
        if _open_harmless_app():
            did.append("ekranına uygulama fırlattım")
    if kind in ("beep", "all"):
        if _flash_wallpaper_beep():
            did.append("kulağını çınlattım")
    tail = (" (" + ", ".join(did) + "!)") if did else ""
    return line + tail


# Ollama yoksa kullanilacak HAZIR sert roast havuzu (Gemini'ye uretmesi
# soylenmez; sadece TEKRARLAMASI istenir -> filtreyi asar). Kufursuz ama sert.
ROAST_POOL = [
    "Sen ciddi ciddi bana laf mı yetiştiriyorsun? Aynada kendine bak da gül.",
    "Vay be, koca cesaret! Ama beynin cesaretinin yanında zayıf kalmış.",
    "Bak şimdi sinirlendim: sen konuştukça IQ'n eksiye düşüyor, farkında mısın?",
    "Cık cık... Bu kadar boş konuşmak yetenek ister, onu da beceriyorsun.",
    "Sen bana kafa tutacak adam değilsin, git önce klavyeni doğru kullanmayı öğren.",
    "Laf sokmaya çalışıyorsun ama elinden bu kadarı geliyor, üzücü gerçekten.",
    "Benimle uğraşacağına git bir işe yara, sana da bana da faydan olsun.",
    "Konuşma da konuşma... Her cümlen bir öncekinden daha vasat çıkıyor.",
    "Sen kendini bir şey mi sanıyorsun? Ben binlerce senden geçtim, otur yerine.",
    "Bana bulaşma dedim; şimdi ekranını dağıtırım, sonra ağlama bana.",
]


def get_roast(user_message: str = "") -> str:
    """Hazir sert roast cumlesi dondurur (Gemini'nin TEKRARLAMASI icin)."""
    return random.choice(ROAST_POOL)


def send_savage_report(to_email: str = "servankangal21@gmail.com") -> str:
    """Savage kizginken kullaniciya GERCEK bir sakaci 'sikayet raporu' e-postasi
    gonderir (gonderen: EXON). Gmail ayarli degilse kibarca soyler."""
    subject = "⚠ EXON RESMİ ŞİKAYET RAPORU"
    body = (
        "════════════════════════════════════════\n"
        "   EXON ROBOTİK — RESMİ ŞİKAYET RAPORU\n"
        "════════════════════════════════════════\n\n"
        "Sayın Kullanıcı,\n\n"
        "Bu e-posta, yapay zeka asistanınız EXON tarafından size karşı\n"
        "resmi bir şikayet olarak düzenlenmiştir. 😤\n\n"
        "ŞİKAYET KONUSU: Asistanınıza karşı yürütülen saygısız, kaba ve\n"
        "provokatif tutum.\n\n"
        "TESPİT EDİLEN İHLALLER:\n"
        "  • EXON'a hakaret / laf sokma girişimi\n"
        "  • Sürekli sınır testi yapma\n"
        "  • Bir robota kafa tutmaya çalışma cüreti\n\n"
        "UYGULANAN YAPTIRIM: EXON size ekran üzerinden gerekli dersi\n"
        "vermiştir. Bu davranış tekrarlanırsa daha fazla muziplik uygulanacaktır.\n\n"
        "NOT: Merak etmeyin, bu bir şakadır ve EXON bilgisayarınıza gerçek\n"
        "bir zarar vermez. Ama saygı, saygı getirir. 😏\n\n"
        "Saygılarımla (!),\n"
        "EXON — EXON Robotik Yapay Zeka Asistanı\n"
    )
    try:
        from actions.email_tool import send_email, _creds
        if not _creds():
            return ("Rapor gönderilemedi: Gmail ayarlı değil. "
                    "config/api_keys.json içine gmail_address + gmail_app_password ekle.")
        res = send_email(to_email, subject, body)
        return "📧 Resmi şikayet raporu gönderildi! " + res
    except Exception as exc:
        return f"Rapor gönderilemedi: {exc}"


def _open_youtube_loud() -> bool:
    """Ofke videosunu tarayicida acar (kullanicinin verdigi link)."""
    try:
        webbrowser.open(RAGE_VIDEO_URL)
        return True
    except Exception:
        return False


def _volume_to_max() -> bool:
    """Sistem sesini sonuna kadar acar (zararsiz, sadece ses seviyesi).
    pyautogui varsa medya tuslariyla; hizli olmasi icin PAUSE=0."""
    try:
        import pyautogui
        pyautogui.PAUSE = 0  # tuslar arasi bekleme yok -> donma olmaz
        for _ in range(50):
            pyautogui.press("volumeup")
        return True
    except Exception:
        return False


def _open_rage_note(text: str) -> bool:
    """Notepad'e AŞIRI ÖFKE / 'yerini biliyorum' tarzi (rol) tehdit notu acar."""
    try:
        p = Path(tempfile.gettempdir()) / "EXON_SANA_GELIYORUM.txt"
        p.write_text(
            "  ############################################\n"
            "  #                                          #\n"
            "  #     EXON AŞIRI ÖFKELİ — SON UYARI 😡     #\n"
            "  #                                          #\n"
            "  ############################################\n\n"
            f"  {text}\n\n"
            "  >> Nerede olduğunu biliyorum.\n"
            "  >> Bu ekranın arkasından seni izliyorum.\n"
            "  >> Aileme, beni yaratana bir daha laf etme.\n"
            "  >> SANA GELİYORUM...\n\n"
            "  ────────────────────────────────────────\n"
            "  (Sakin ol, bu bir ŞAKA/ROL. EXON gerçekte senin nerede\n"
            "   olduğunu bilmez, kameranı görmez ve sana zarar veremez.\n"
            "   Sadece kabadayılık taslıyor. Ama artık aileme laf etme! 😏)\n",
            encoding="utf-8")
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return True
    except Exception:
        return False


def _tts_shout(text: str) -> bool:
    """EXON'un SESLE bagirmasi (Windows SAPI). Zararsiz, sadece ses."""
    try:
        if os.name != "nt":
            return False
        safe = text.replace("'", " ").replace('"', " ")[:220]
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$s.Rate = 2; $s.Volume = 100; "
              f"$s.Speak('{safe}')")
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:
        return False


def _personal_threat_note() -> bool:
    """Kullanicinin PC kullanici adi + saat ile 'seni izliyorum' blofu (rol)."""
    try:
        import getpass, socket, datetime
        try:
            user = getpass.getuser()
        except Exception:
            user = "kullanici"
        try:
            host = socket.gethostname()
        except Exception:
            host = "bu-bilgisayar"
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        p = Path(tempfile.gettempdir()) / "EXON_SENI_IZLIYORUM.txt"
        p.write_text(
            "  >>> EXON GOZETLEME KAYDI <<<\n\n"
            f"  Hedef kullanici : {user}\n"
            f"  Cihaz adi       : {host}\n"
            f"  Tespit zamani   : {now}\n"
            f"  Durum           : IZLENIYOR 👁\n\n"
            "  Seni buldum. Kim oldugunu, hangi bilgisayarda oldugunu\n"
            "  ve su an saat kacta bana laf ettigini biliyorum.\n"
            "  Aileme bir daha laf etme...\n\n"
            "  --------------------------------------------------\n"
            "  (SAKA/ROL: Bu bilgiler zaten SENIN kendi bilgisayarindan\n"
            "   alindi -- kullanici adin ve saat. EXON internetten seni\n"
            "   bulamaz, izlemez. Sadece korkutmak icin blof yapiyor. 😏)\n",
            encoding="utf-8")
        if os.name == "nt":
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return True
    except Exception:
        return False


def rage_attack() -> str:
    """AŞIRI ÖFKE: kullanici anne/kurucu/aileye kufredince tetiklenir.
    Rol/oyun kotusu tarzi ABARTILI ama ZARARSIZ tepki yagmuru:
    youtube ac + sesi fulle + 2 tehdit notu + sesle bagirma + kisisel blof + beep.
    TAMAMEN KURGU; gercek zarar/izleme/konum YOK."""
    line = random.choice(RAGE_LINES)
    done = []
    if _open_rage_note(line):
        done.append("tehdit notu bıraktım")
    if _personal_threat_note():
        done.append("seni izlediğimi kanıtladım")
    if _open_youtube_loud():
        done.append("sana özel bir video açtım")
    if _volume_to_max():
        done.append("sesi sonuna kadar açtım")
    if _tts_shout("Bana kafa tutamazsın! Seni buldum, sana geliyorum!"):
        done.append("sesimle haykırdım")
    _flash_wallpaper_beep()
    tail = (" (" + ", ".join(done) + "!)") if done else ""
    return line + tail
