# PANORIX Otomatik EKAP Takibi

## Sistem ne yapar?

GitHub Actions her gün Türkiye saatiyle yaklaşık 08.30'da çalışır. EKAP'ın kamuya açık genel ihale arama sayfasını yalnız tanımlı reklam anahtar kelimeleriyle sorgular, bulunan İKN'leri resmî EKAP detay sayfalarından okur ve eşleşen kayıtları Firestore `ekapTenders` koleksiyonuna kaydeder.

Varsayılan anahtar kelimeler:

- billboard
- açık hava reklam
- reklam alanı
- reklam panosu
- durak reklamı
- kent mobilyaları
- LED ekran
- CLP
- raket reklam
- megalight
- tanıtım alanı

Yeni ilan bulunduğunda PANORIX Bildirimler bölümüne özet bildirim eklenir. EKAP Takip sayfasının üstünde son tarama zamanı, yeni/güncellenen kayıt sayısı ve hata durumu görünür.

## Güvenli çalışma ilkeleri

- EKAP hesabına giriş yapmaz.
- E-Devlet, e-imza, CAPTCHA veya oturum korumasını aşmaz.
- Yalnız kamuya açık arama ve ihale detay sayfalarını kullanır.
- İstekler arasında en az 2 saniye bekler.
- 401, 403 veya 429 yanıtında taramayı durdurur.
- Her kayıt İKN ile tekilleştirilir; aynı ihale tekrar eklenmez.
- Mevcut kullanıcının verdiği durum, sorumlu ve not alanları otomatik güncellemede ezilmez.

## GitHub'da yapılacaklar

### 1. Service Account secret

Repository'nizi açın:

1. `Settings`
2. `Secrets and variables`
3. `Actions`
4. `New repository secret`

Ad:

```text
FIREBASE_SERVICE_ACCOUNT_JSON
```

Değer: Firebase'den indirdiğiniz yeni Service Account JSON dosyasının tamamı.

### 2. Şirket kimliği

Yeni secret oluşturun.

Ad:

```text
ORGANIZATION_ID
```

Değer:

```text
panorix
```

### 3. İletişim e-postası — isteğe bağlı

Yeni secret oluşturabilirsiniz.

Ad:

```text
EKAP_CONTACT_EMAIL
```

Değer: Kurumsal teknik iletişim e-postanız.

Bu değer yalnız HTTP User-Agent bilgisinde kullanılır; EKAP hesabına giriş amacı taşımaz.

### 4. Manuel test

1. GitHub repository'de `Actions` sekmesine girin.
2. Sol tarafta `PANORIX Otomatik EKAP Takibi` seçeneğini açın.
3. `Run workflow` butonuna basın.
4. Branch olarak `main` seçili kalsın.
5. Yeşil `Run workflow` butonuna basın.
6. Oluşan çalışma satırını açın.
7. Yeşil tik göründüğünde işlem tamamlanmıştır.

## Sonuç kontrolü

Firebase Console'da:

```text
Firestore Database → ekapTenders
```

koleksiyonunu açın.

PANORIX'te:

```text
EKAP Takip
```

sayfasını açın. Son tarama paneli ve bulunan ilanlar görünmelidir.

## Zamanlama

Workflow:

```yaml
cron: "30 5 * * 1-6"
```

şeklindedir. GitHub Actions UTC kullandığı için bu saat Türkiye'de yaklaşık 08.30'dur. Pazartesi-Cumartesi çalışır.

## Önemli sınır

Bu entegrasyon EKAP'ın belgelenmiş resmî API'si değildir; kamuya açık arama ekranını düşük yoğunlukta izleyen bir takip yardımcı aracıdır. EKAP sayfa yapısı değişirse parser güncellenmesi gerekebilir. İhale bilgileri arasında uyuşmazlık bulunursa resmî Kamu İhale Bülteni ve EKAP ihale detay sayfası esas alınmalıdır.
