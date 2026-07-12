# PANORIX Kurulum Rehberi

Bu rehber kod uzmanı olmayan kullanıcı için, mümkün olduğunca ekran üzerinden yapılacak işlemlerle hazırlanmıştır.

---

# A. GitHub'a yükleme

## 1. ZIP dosyasını açın

1. PANORIX ZIP dosyasına sağ tıklayın.
2. **Tümünü Ayıkla** seçeneğini seçin.
3. Açılan klasörde `app.py`, `index.html`, `logo.png` ve `background.png` dosyalarını gördüğünüzü doğrulayın.

## 2. Gizli klasörleri görünür yapın

Windows'ta:

1. Dosya Gezgini üst menüsünden **Görünüm** seçeneğini açın.
2. **Göster → Gizli öğeler** seçeneğini işaretleyin.
3. `.streamlit` ve `.github` klasörlerinin göründüğünü kontrol edin.

## 3. Yeni GitHub repository oluşturun

1. GitHub hesabınıza giriş yapın.
2. **New repository** seçeneğine basın.
3. Repository adı olarak `PANORIX` yazın.
4. İlk aşamada **Private** seçmenizi öneririm.
5. README veya `.gitignore` eklemeyin; projede zaten vardır.
6. **Create repository** seçeneğine basın.

## 4. Dosyaları yükleyin

1. Repository içinde **Add file → Upload files** seçeneğine basın.
2. Ayıkladığınız PANORIX klasörünün **içindeki bütün dosya ve klasörleri** yükleme alanına sürükleyin.
3. Şu yolların ana dizinde göründüğünü kontrol edin:

```text
app.py
index.html
.streamlit/config.toml
.github/workflows/daily-reminders.yml
firestore.rules
storage.rules
```

4. `PANORIX/app.py` şeklinde ikinci bir iç klasör oluşmamalıdır.
5. Commit mesajına `PANORIX Firebase initial release` yazın.
6. **Commit changes** seçeneğine basın.

## 5. Kesinlikle yüklemeyeceğiniz dosyalar

Şunları GitHub'a yüklemeyin:

```text
.streamlit/secrets.toml
Firebase Service Account JSON dosyası
.env
```

`.streamlit/secrets.toml.example` güvenli örnek dosyadır ve yüklenebilir.

---

# B. Firebase projesi oluşturma

## 1. Firebase projesi

1. Firebase Console'a giriş yapın.
2. **Create a project / Proje oluştur** seçeneğine basın.
3. Proje adını `PANORIX` yazın.
4. Proje kimliğini not edin. Daha sonra değiştirilemez.
5. Google Analytics zorunlu değildir; tercihinize göre kapatabilirsiniz.
6. Projeyi oluşturun.

## 2. Firebase Web App ekleme

1. Firebase proje ana ekranında Web simgesine (`</>`) basın.
2. Uygulama takma adına `PANORIX Web` yazın.
3. Firebase Hosting seçeneğini işaretlemek zorunda değilsiniz.
4. **Register app / Uygulamayı kaydet** seçeneğine basın.
5. Ekranda şu alanları içeren `firebaseConfig` nesnesi gösterilir:

```text
apiKey
authDomain
projectId
storageBucket
messagingSenderId
appId
measurementId
```

6. Bu ekranı kapatmadan değerleri güvenli bir yere geçici olarak not edin.

---

# C. Firebase Authentication

## 1. E-posta/Şifre girişini açın

1. Sol menüden **Build → Authentication** bölümüne girin.
2. **Get started** seçeneğine basın.
3. **Sign-in method** sekmesini açın.
4. **Email/Password** satırına basın.
5. Birinci **Email/Password** seçeneğini etkinleştirin.
6. **Save** seçeneğine basın.

## 2. Güçlü parola politikasını ayarlayın

1. Authentication içinde **Settings** sekmesine girin.
2. **Password policy** bölümünü açın.
3. Önerilen ayarlar:
   - Minimum uzunluk: 12
   - Büyük harf zorunlu
   - Küçük harf zorunlu
   - Rakam zorunlu
   - Özel karakter zorunlu
4. Enforcement seçeneğini **Require** yapın.

Not: PANORIX kullanıcı ekleme ekranında minimum 8 karakter kontrolü vardır; Firebase tarafındaki daha güçlü politika her zaman önceliklidir.

## 3. Streamlit alan adını yetkilendirin

Streamlit uygulamasını yayımladıktan sonra uygulama adresiniz örneğin şöyle olur:

```text
panorix-firma.streamlit.app
```

Firebase Authentication içinde:

1. **Settings → Authorized domains** bölümüne girin.
2. **Add domain** seçeneğine basın.
3. Yalnız alan adını girin; `https://` yazmayın:

```text
panorix-firma.streamlit.app
```

4. Kaydedin.

## 4. İlk kullanıcıyı manuel oluşturmayın

Bu sürümde Firebase Console içinden ayrıca **Add user** işlemi yapmanız gerekmez. İlk Super Admin hesabı, Streamlit Secrets içindeki `INITIAL_ADMIN_*` değerleri kullanılarak uygulama açıldığında Firebase Admin SDK tarafından otomatik oluşturulur.

Authentication içinde önceden aynı e-posta ile bir kullanıcı varsa PANORIX bu kullanıcıyı tekrar oluşturmaz; eksik Super Admin profilini ve yetkilerini tamamlar.

---

# D. Cloud Firestore kurulumu

## 1. Veritabanını oluşturun

1. Sol menüden **Build → Firestore Database** bölümüne girin.
2. **Create database** seçeneğine basın.
3. **Production mode** seçeneğini seçin.
4. Kullanıcılarınıza en yakın uygun Avrupa bölgesini seçin.
5. Bölge seçimini dikkatli yapın; sonradan değiştirmek kolay değildir.
6. Veritabanını oluşturun.

## 2. Firestore güvenlik kurallarını yayınlayın

1. Firestore Database içinde **Rules** sekmesine girin.
2. Editördeki mevcut kuralların tamamını silin.
3. GitHub projenizdeki `firestore.rules` dosyasını açın.
4. Dosyanın tamamını kopyalayın.
5. Firebase Rules editörüne yapıştırın.
6. **Publish** seçeneğine basın.

`allow read, write: if true` biçiminde herkese açık test kuralı kullanmayın.

## 3. Firestore indexlerini oluşturun

Firebase Console'da **Firestore Database → Indexes** bölümüne girin.

### Index 1 — Mesajlar

- Collection ID: `messages`
- Query scope: `Collection`
- Alan 1: `organizationId` — Ascending
- Alan 2: `participants` — Arrays / Array contains

### Index 2 — Bildirimler

- Collection ID: `notifications`
- Query scope: `Collection`
- Alan 1: `organizationId` — Ascending
- Alan 2: `recipientIds` — Arrays / Array contains

Her iki indexi oluşturduktan sonra durumları **Enabled** olana kadar bekleyin.

Alternatif olarak Firebase CLI kullanan geliştiriciler `firebase.json` ve `firestore.indexes.json` dosyalarını kullanabilir.

---

# E. Firebase Storage kurulumu

## 1. Storage alanını oluşturun

1. Firebase sol menüsünden **Build → Storage** bölümüne girin.
2. **Get started** seçeneğine basın.
3. Mümkünse Firestore ile uyumlu bölgeyi seçin.
4. Storage alanını oluşturun.

## 2. Storage kurallarını yayınlayın

1. Storage içinde **Rules** sekmesini açın.
2. Mevcut kuralları silin.
3. Projedeki `storage.rules` dosyasının tamamını kopyalayın.
4. Rules editörüne yapıştırın.
5. **Publish** seçeneğine basın.

Kurallar dosyaları şirket, modül ve kayıt bazında ayırır; izin verilen dosya türlerini ve 20 MB sınırını uygular.

---

# F. Firebase Service Account

Bu anahtar yalnız Streamlit'in güvenli sunucu tarafı için kullanılır. Tarayıcıya gönderilmez.

## 1. JSON anahtarını oluşturun

1. Firebase Console'da dişli simgesine basın.
2. **Project settings** bölümüne girin.
3. **Service accounts** sekmesini açın.
4. **Firebase Admin SDK** bölümünde **Generate new private key** seçeneğine basın.
5. Uyarıyı onaylayın.
6. Bilgisayarınıza bir JSON dosyası iner.

## 2. Güvenlik

- JSON dosyasını GitHub'a yüklemeyin.
- E-posta veya mesajla paylaşmayın.
- Kullanmadığınız anahtarı Google Cloud IAM üzerinden silin.
- Eski kongre projesindeki anahtar GitHub'a yüklendiyse onu mutlaka iptal edin.

---

# G. Google Maps ve Street View

## 1. Google Cloud projesini seçin

1. Google Cloud Console'a giriş yapın.
2. Firebase ile aynı Google Cloud projesini seçin.
3. Projede faturalandırma hesabının bağlı olduğundan emin olun.

## 2. API'yi etkinleştirin

1. **APIs & Services → Library** bölümüne girin.
2. `Maps JavaScript API` aratın.
3. **Enable** seçeneğine basın.

PANORIX harita markerları ve tarayıcı içi Street View panorama için Maps JavaScript API kullanır.

## 3. API anahtarı oluşturun

1. **APIs & Services → Credentials** bölümüne girin.
2. **Create credentials → API key** seçeneğine basın.
3. Anahtarı kopyalayın.
4. Hemen **Edit API key** seçeneğine girin.

## 4. Anahtarı kısıtlayın

### Application restrictions

- **Websites / HTTP referrers** seçin.
- Streamlit alanınızı ekleyin:

```text
https://panorix-firma.streamlit.app/*
```

Yerel geliştirme yapacaksanız ayrıca:

```text
http://localhost:8501/*
```

### API restrictions

- **Restrict key** seçin.
- Yalnız `Maps JavaScript API` seçin.
- Kaydedin.

Anahtarı GitHub koduna yazmayın.

> Google Maps JavaScript API bir tarayıcı API'sidir. Anahtar harita yüklenirken kullanıcının tarayıcısına gönderilir ve teknik olarak görülebilir. Bu nedenle güvenlik, anahtarı gizlemekten çok **HTTP referrer** ve **API restriction** ayarlarını doğru yapmaya dayanır.

---

# H. Streamlit Community Cloud yayını

## 1. Uygulamayı oluşturun

1. Streamlit Community Cloud hesabınıza giriş yapın.
2. **Create app** seçeneğine basın.
3. GitHub repository olarak `PANORIX` seçin.
4. Branch: `main`
5. Main file path: `app.py`
6. Python sürümü seçilebiliyorsa `3.12` seçin.

## 2. Secrets alanını doldurun

Advanced settings veya uygulama oluşturulduktan sonra:

**Manage app → Settings → Secrets**

alanını açın.

Aşağıdaki yapıyı yapıştırın ve değerleri kendi Firebase/Google bilgilerinizle değiştirin:

```toml
INITIAL_ADMIN_EMAIL = "davutkara1985@gmail.com"
INITIAL_ADMIN_PASSWORD = "BU-SOHBETTE-BELIRTTIGINIZ-YONETICI-SIFRESI"
INITIAL_ADMIN_NAME = "Davut Kara"
INITIAL_ORGANIZATION_NAME = "PANORIX"
INITIAL_ORGANIZATION_ID = "panorix"

SESSION_TIMEOUT_MINUTES = 60
GOOGLE_MAPS_API_KEY = "GOOGLE-MAPS-ANAHTARINIZ"
APP_PUBLIC_URL = "https://panorix-firma.streamlit.app"

[firebase_web]
api_key = "FIREBASE-WEB-API-KEY"
auth_domain = "PROJE-ID.firebaseapp.com"
project_id = "PROJE-ID"
storage_bucket = "PROJE-ID.firebasestorage.app"
messaging_sender_id = "MESAJ-GONDEREN-ID"
app_id = "WEB-APP-ID"
measurement_id = ""

[firebase_service_account]
type = "service_account"
project_id = "PROJE-ID"
private_key_id = "JSON-DOSYASINDAKI-PRIVATE-KEY-ID"
private_key = """-----BEGIN PRIVATE KEY-----
JSON DOSYASINDAKI PRIVATE KEY SATIRLARINI BURAYA AYNEN YAPISTIRIN
-----END PRIVATE KEY-----
"""
client_email = "firebase-adminsdk-xxxxx@PROJE-ID.iam.gserviceaccount.com"
client_id = "JSON-DOSYASINDAKI-CLIENT-ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "JSON-DOSYASINDAKI-CLIENT-CERT-URL"
universe_domain = "googleapis.com"
```

Dikkat:

- Firebase Web yapılandırması tarayıcı istemcisini projeye bağlayan yapılandırmadır; asıl veri güvenliği Authentication ve `firestore.rules` / `storage.rules` ile sağlanır.
- `APP_PUBLIC_URL` sonunda `/` olmaması tercih edilir.
- `private_key` başlama ve bitiş satırlarını da içermelidir.
- Secrets içeriğini GitHub'a koymayın.
- `INITIAL_ADMIN_PASSWORD` yalnız Streamlit Secrets alanında tutulmalı; GitHub dosyalarına yazılmamalıdır.
- İlk hesap başarıyla oluşturulduktan sonra `INITIAL_ADMIN_PASSWORD` satırını Secrets alanından silebilirsiniz. Mevcut hesap ve profil çalışmaya devam eder.

## 3. Deploy

1. Secrets değerlerini kaydedin.
2. **Deploy** veya **Reboot app** seçeneğine basın.
3. Uygulamanın açılmasını bekleyin.

---

# I. İlk Super Admin hesabının otomatik oluşturulması

1. Streamlit Secrets içindeki `INITIAL_ADMIN_EMAIL` alanında yönetici e-posta adresinizin doğru olduğunu kontrol edin.
2. `INITIAL_ADMIN_PASSWORD` alanına yalnız Streamlit Secrets içinde kullanacağınız ilk yönetici şifresini yazın.
3. `INITIAL_ADMIN_NAME`, `INITIAL_ORGANIZATION_NAME` ve `INITIAL_ORGANIZATION_ID` alanlarını kontrol edin.
4. **Deploy** veya **Reboot app** seçeneğine basın.
5. Uygulama açılırken Firebase Admin SDK şu kayıtları otomatik oluşturur veya tamamlar:
   - Firebase Authentication yönetici kullanıcısı
   - `users/{Firebase UID}` Super Admin profili
   - `settings/{organizationId}` şirket ayarları
   - `auditLogs/{otomatik belge}` ilk yönetici oluşturma kaydı
6. Giriş ekranında yönetici e-posta adresi otomatik yazılı gelir. Tanımladığınız şifreyle giriş yapın.
7. İlk başarılı girişten sonra `INITIAL_ADMIN_PASSWORD` satırını Streamlit Secrets alanından silin ve uygulamayı yeniden başlatın. PANORIX mevcut Firebase kullanıcısını korur; şifreyi yeniden oluşturmaz veya değiştirmez.

## Otomatik kurulum hata verirse

- `Firebase Service Account yapılandırılmamış` mesajı: `[firebase_service_account]` bölümünü kontrol edin.
- `INITIAL_ADMIN_PASSWORD alanını tanımlayın` mesajı: Authentication içinde kullanıcı henüz yoktur ve Secrets parola alanı boştur.
- `Başka bir aktif Super Admin hesabı bulundu` mesajı: Veritabanında farklı bir Super Admin vardır; otomatik hesap üzerine yazılmaz.
- Firebase parola politikası hatası: Belirlediğiniz şifrenin Firebase Authentication parola kurallarını karşıladığını kontrol edin.

# J. Yeni kullanıcı ekleme

1. Super Admin hesabıyla giriş yapın.
2. Sol menüden **Kullanıcı Yönetimi** bölümüne girin.
3. Ad Soyad, e-posta, rol, birim ve geçici şifreyi girin.
4. Gerekiyorsa özel yetki kutularını işaretleyin.
5. **Kullanıcı Ekle** seçeneğine basın.
6. Kullanıcı Firebase Authentication ve Firestore profilinde birlikte oluşturulur.
7. Kullanıcı kendi e-posta ve geçici şifresiyle giriş yapabilir.

Rol veya yetki değişikliğinden sonra ilgili kullanıcının çıkış yapıp yeniden giriş yapması önerilir.

---

# K. GitHub Actions — günlük hatırlatmalar

Bu bölüm isteğe bağlıdır; uygulamanın temel kullanımı için zorunlu değildir.

## 1. Service Account JSON secret

1. GitHub repository içinde **Settings** bölümüne girin.
2. **Secrets and variables → Actions** seçeneğini açın.
3. **New repository secret** seçeneğine basın.
4. Name:

```text
FIREBASE_SERVICE_ACCOUNT_JSON
```

5. Secret alanına Firebase'den indirdiğiniz JSON dosyasının **tam içeriğini** yapıştırın.
6. Kaydedin.

`daily-reminders.yml` her gün Türkiye saatiyle yaklaşık 09.00'da çalışır ve yaklaşan tarihleri bildirim collection'ına yazar.

## 2. EKAP/veri feed entegrasyonu

Yalnız yetkili bir JSON feed/API'niz varsa şu secrets değerlerini ekleyin:

```text
EKAP_FEED_URL
EKAP_FEED_TOKEN
ORGANIZATION_ID
```

`ORGANIZATION_ID` değerini Firestore'daki kendi `users/{uid}` belgenizde görebilirsiniz.

Yetkili veri akışı yoksa bu secrets değerlerini eklemeyin. Workflow hata vermeden taramayı atlar.

---

# L. Canlı kullanımdan önce test listesi

## Authentication

- Doğru şifreyle giriş
- Yanlış şifre hatası
- Şifremi unuttum e-postası
- Pasif kullanıcının giriş yapamaması
- Super Admin'in pasife alınamaması

## Yetkilendirme

- Misafir yalnız izin verilen modülleri görüyor mu?
- Satış rolü finans kayıtlarını değiştiremiyor mu?
- Muhasebe rolü fatura ve tahsilat ekleyebiliyor mu?
- Saha rolü operasyon görevlerini güncelleyebiliyor mu?
- Başka şirket kimliğine sahip veri okunamıyor mu?

## Veri

- Belediye ekleme/düzenleme/arşivleme
- İhale ve teminat tarihleri
- Billboard fotoğraf yükleme
- Rezervasyon tarih çakışması
- Tahsilat onaylanınca fatura bakiyesi
- Sözleşme/rezervasyon sonrası billboard durumu
- Audit log kaydı

## Harita

- Markerların görünmesi
- Boş/Kirada/Rezerve renkleri
- İl/ilçe filtresi
- Marker cluster
- Street View
- QR ile billboard detay bağlantısı

## Mobil

- Menü açma/kapatma
- Formların tek sütuna düşmesi
- Checkbox dokunma alanları
- Tabloların yatay kayması
- Takvim görünümü

---

# M. Sorun giderme

## Firebase yapılandırması eksik

Streamlit Secrets içinde `[firebase_web]` alanlarını kontrol edin.

## Firebase Service Account yapılandırılmamış

`[firebase_service_account]` bölümünü ve private key satırlarını kontrol edin.

## Missing or insufficient permissions

1. `firestore.rules` dosyasını yeniden kopyalayın.
2. Rules ekranında **Publish** seçeneğine bastığınızı kontrol edin.
3. Kullanıcının `users/{uid}` profilinde `active=true`, `isDeleted=false` ve doğru `organizationId` olduğunu kontrol edin.
4. Kullanıcının çıkış yapıp tekrar giriş yapmasını sağlayın.

## Firestore index hatası

Hata mesajındaki bağlantıyı açarak indexi oluşturabilir veya rehberdeki iki indexi manuel tanımlayabilirsiniz.

## Google Maps yüklenemedi

- Maps JavaScript API etkin mi?
- Billing bağlı mı?
- API key doğru mu?
- HTTP referrer kısıtında Streamlit URL'si var mı?
- API restriction içinde Maps JavaScript API seçili mi?

## Storage upload reddedildi

- Kullanıcı çıkış yapıp yeniden giriş yaptı mı?
- Custom claim içinde `organizationId` var mı?
- Dosya 20 MB altında mı?
- Dosya türü kurallarda izinli mi?

## Tasarım eski görünüyor

1. Streamlit'te **Reboot app** seçeneğine basın.
2. Tarayıcıda `Ctrl + F5` kullanın.
3. GitHub'da `logo.png`, `background.png` ve güncel `index.html` dosyalarının ana dizinde olduğunu kontrol edin.
