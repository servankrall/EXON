# 💎 EXON Pro — Kurulum ve Para Kazanma Rehberi

EXON'da bazı güçlü özellikler **Pro**'ya özeldir. Bu rehber, **satışlardan paranın
sana gelmesi** için Pro'yu nasıl kuracağını anlatır. **Sunucu/backend gerekmez.**

---

## 🎯 İki yöntem (ikisi de parayı sana getirir)
- **Yöntem A — Kolay (önerilen):** Anahtarı SEN üretirsin; Gumroad'ın "lisans anahtarı" özelliği **gerekmez**.
- **Yöntem B — Gelişmiş:** Gumroad üyelik + otomatik lisans doğrulama (abonelik bitince Pro kapanır).

Her iki yöntemde de satış Gumroad/Shopier üzerinden olur ve **para senin hesabına** geçer.
EXON ödemeye hiç dokunmaz; sadece lisans anahtarını doğrular.

---

## Yöntem A (kolay, önerilen): Kendi anahtarını üret
> Gumroad'da "Generate a unique license key" seçeneğini bulamadıysan **bunu kullan.**

1. (Opsiyonel) Kendi gizli imzanı koy — koymazsan gömülü varsayılan kullanılır.
   `jarvis/config/api_keys.json`:
   ```json
   "license_secret": "kendi-uzun-gizli-metnin"
   ```
2. Gumroad/Shopier'de **normal bir ürün** aç (Aylık $2, Yıllık $10). Lisans özelliği gerekmez.
3. `jarvis` klasöründe anahtar üret:
   ```cmd
   python make_license.py yearly      (yıllık, 365 gün)
   python make_license.py monthly     (aylık, 30 gün)
   python make_license.py lifetime    (ömürlük)
   ```
4. Çıkan anahtarı (örn. `EXON-Y-20967-FDF073EF35`) satın alan kişiye ver (Gumroad satış
   sonrası "content/receipt" alanına yaz ya da e-posta at).
5. Müşteri EXON'da **✦ PRO'YA GEÇ → Etkinleştir**'e anahtarı girer → Pro açılır.
   Aylık/yıllık anahtarlar sürelidir; süre bitince yeni anahtar verirsin (yenileme).

Butonların senin satış sayfanı açması için (opsiyonel):
```json
"pro_purchase_url_monthly": "https://senin.gumroad.com/l/exon-pro",
"pro_purchase_url_yearly":  "https://senin.gumroad.com/l/exon-pro"
```

---

## Yöntem B (gelişmiş): Gumroad otomatik abonelik
1. [gumroad.com](https://gumroad.com) → ücretsiz hesap aç (ödeme için PayPal/banka bağla).
2. **New Product → Membership** oluştur: ad "EXON Pro". İki **tier (kademe)** ekle:
   - **Aylık** → `$2 / month`
   - **Yıllık** → `$10 / year`
3. Ürün ayarlarında **"Generate a unique license key per sale"** seçeneğini **AÇ**.
4. Ürünü yayınla. Sana lazım olanlar:
   - **Product ID** (ürün → Share/Advanced) veya **permalink** (`exon-pro`)
   - Her tier'ın **satın alma linki** (tier seçili ürün linki)
5. `jarvis/config/api_keys.json` dosyasına ekle:
   ```json
   "gumroad_product_id": "BURAYA_URUN_ID",
   "pro_purchase_url_monthly": "https://senin.gumroad.com/l/exon-pro?tier=Ayl%C4%B1k",
   "pro_purchase_url_yearly":  "https://senin.gumroad.com/l/exon-pro?tier=Y%C4%B1ll%C4%B1k"
   ```
   (ID yerine permalink kullanacaksan: `"gumroad_product_permalink": "exon-pro"`)

> Abonelik **iptal edilir veya ödeme alınmazsa** EXON bir sonraki açılışta lisansı
> yeniden doğrular ve Pro'yu otomatik kapatır.

> **İki ayrı alan var, karıştırma:**
> - `gumroad_product_id` / `gumroad_product_permalink` → lisans **doğrulama** için.
> - `pro_purchase_url_monthly` / `pro_purchase_url_yearly` → **butonun açtığı satış sayfası**.
>
> `pro_purchase_url_*` boş olsa bile **permalink** doluysa butonlar otomatik
> `https://gumroad.com/l/<permalink>` ürün sayfanı açar (alıcı orada Aylık/Yıllık seçer).
> Tier'a **doğrudan** gitmek istersen `pro_purchase_url_monthly/yearly` alanlarını doldur.

Artık "SATIN AL" butonu senin satış sayfanı açar, para sana gelir, anahtar doğrulanır. ✅

---

## 2) Shopier ile (Türkiye — banka havalesi kolay)
Shopier'in otomatik lisans API'si yoktur; anahtarı **elle** verirsin:
1. [shopier.com](https://www.shopier.com) → ürün oluştur, fiyat koy.
2. `"pro_purchase_url"` alanına Shopier ürün linkini yaz.
3. Satıştan sonra müşteriye bir anahtar gönder (ör. e-posta ile). Gumroad ayarlı
   olmadığı için EXON girilen anahtarı çevrimdışı kabul eder.

> Not: Gumroad **product_id** ayarlı değilse EXON, girilen herhangi bir anahtarı kabul eder
> (test/elle satış için). **Gerçek koruma** istiyorsan Gumroad'ı yapılandır.

---

## 🔓 Pro'da neler var?
Görsel oluşturma · şarkı söyleme · kod asistanı · borsa/hisse · haber · e-posta ·
oyun modu · ekran analizi · YouTube analizi.

**Free'de** ise: sesli sohbet, web & Wikipedia araması, hava durumu, uygulama açma,
takvim/hatırlatıcı, çeviri, döviz, medya, WhatsApp ve daha fazlası — yani EXON ücretsiz
de güçlü kalır.

## 🧪 Kendin için Pro'yu açmak
Kendi bilgisayarında test için `config/api_keys.json` içine `"pro_active": true` yaz —
ödeme olmadan tüm Pro özellikleri açılır.
