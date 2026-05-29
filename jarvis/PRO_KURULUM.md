# 💎 EXON Pro — Kurulum ve Para Kazanma Rehberi

EXON'da bazı güçlü özellikler **Pro**'ya özeldir. Bu rehber, **satışlardan paranın
sana gelmesi** için Pro'yu nasıl kuracağını anlatır. **Sunucu/backend gerekmez.**

---

## 🎯 Mantık
- Sen bir satış platformunda (**Gumroad** önerilir) "EXON Pro" ürünü açarsın, fiyat koyarsın.
- Müşteri satın alınca **para senin hesabına** geçer ve müşteriye otomatik bir
  **lisans anahtarı** verilir.
- Müşteri uygulamadaki **"✦ PRO'YA GEÇ"** butonundan anahtarı girer; EXON, Gumroad'ın
  ücretsiz API'siyle anahtarı doğrular ve Pro özellikleri açılır.

---

## 1) Gumroad ile (önerilen — lisans otomatik)
1. [gumroad.com](https://gumroad.com) → ücretsiz hesap aç (ödeme için PayPal/banka bağla).
2. **New Product → Digital product** oluştur: ad "EXON Pro", fiyat (örn. ₺149 / $4.99).
3. Ürün ayarlarında **"Generate a unique license key per sale"** seçeneğini **AÇ**.
4. Ürünü yayınla. Sana iki şey lazım:
   - **Ürün linki** (örn. `https://senin.gumroad.com/l/exon-pro`)
   - **Product ID** (ürün sayfası → Share/Advanced'de görünür) veya **permalink** (`exon-pro`)
5. `jarvis/config/api_keys.json` dosyasına ekle:
   ```json
   "pro_purchase_url": "https://senin.gumroad.com/l/exon-pro",
   "gumroad_product_id": "BURAYA_URUN_ID"
   ```
   (ID yerine permalink kullanacaksan: `"gumroad_product_permalink": "exon-pro"`)

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
