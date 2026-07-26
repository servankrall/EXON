# 🚀 EXON'u Uygulama (.exe) Yapma — Adım Adım

Çökme sorunu çözüldü! Artık EXON'u herkesin kullanabileceği bir uygulamaya çevirelim.

> ⚠️ **ÖN KOŞUL:** Klasör **OneDrive DIŞINDA** ve **boşluksuz/parantezsiz** bir yolda
> olmalı. Doğru: `C:\EXON\jarvis`  ·  Yanlış: `...\OneDrive\Desktop\jarvis (3)\...`

---

## Yöntem 1: Tek tıkla .exe (önerilen)

1. `C:\EXON\jarvis` klasöründe **`build_exe.bat`**'a çift tıkla.
2. İlk sefer birkaç dakika sürer (paketleri + PyInstaller'ı kurup derler).
3. Bitince **`dist\EXON\`** klasörü otomatik açılır. İçinde **`EXON.exe`** vardır.
4. Test et: `EXON.exe`'ye çift tıkla → uygulama açılmalı.

### Paylaşmak için
- **`dist\EXON`** klasörünün **tamamını** sağ tık → "Sıkıştırılmış (zip) klasör".
- Bu zip'i gönder. Karşı taraf açıp içindeki **`EXON.exe`**'ye çift tıklar.
  **Python'a, kuruluma gerek YOK** — her şey içinde gömülü.

---

## Yöntem 2: Klasör + Başlatıcı (exe istemezsen)

`jarvis` klasörünü zip'le, gönder. Karşı taraf **`EXON_Baslat.bat`**'a çift tıklar.
Python yoksa otomatik indirip kurar, paketleri yükler, açar.

---

## Sık sorulanlar

**exe açılınca SmartScreen "bilinmeyen yayıncı" diyor.**
Normaldir (imzasız exe). "Daha fazla bilgi → Yine de çalıştır" denir. İmzalama
sertifikası ücretlidir; başlangıç için gerekmez.

**Antivirüs exe'yi siliyor.**
PyInstaller exe'leri bazen yanlış alarm verir. Derlerken antivirüsü geçici kapat,
ya da `dist` klasörünü istisnalara ekle.

**exe çok büyük (~300 MB).**
İçinde Python + tüm kütüphaneler gömülü olduğu için normaldir.

**Kullanıcı verisi nerede?**
exe'nin yanındaki **`EXON_data`** klasöründe (ayarlar, hafıza, üretilen görseller).

---

## Profesyonel görünüm (opsiyonel)

- **İkon:** `jarvis` klasörüne **`EXON.ico`** koy → exe o ikonu kullanır.
- **Pro satışı:** `PRO_KURULUM.md`'ye bak (Gumroad ile aylık $2 / yıllık $10).
