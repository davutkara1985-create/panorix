# PANORIX

**Şehir Reklamlarının Tüm Gücü Tek Merkezde**

PANORIX; belediyelerden ihale ile kiralanan billboard, CLP, raket, megalight, totem, LED ekran ve durak reklam alanlarının satış, rezervasyon, sözleşme, finans ve saha operasyonlarını tek merkezden yönetmek için hazırlanmış Streamlit + Firebase uygulamasıdır.

## Referans mimari

Bu sürüm, yüklenen `kongre-yonetimi-sistemi-main(16)` projesinin doğal devamı olarak hazırlanmıştır. Aşağıdaki yapılar korunmuştur:

- Tek Streamlit custom component yaklaşımı (`app.py` + `index.html`)
- Giriş ekranı, sol menü, üst menü ve sayfa yerleşimi
- Kart, form, tablo, modal, checkbox ve takvim bileşenleri
- Mobil çekmece menüsü ve responsive davranışlar
- Mevcut JavaScript modül/CRUD deseni

Yeni bir tasarım dili veya farklı bir frontend framework eklenmemiştir. Yüklenen `logo.png` logo, `background.png` ise giriş ve ana uygulama arka planı olarak kullanılır.

## Teknoloji yapısı

- Frontend: HTML, CSS ve JavaScript; Streamlit custom component içinde
- Uygulama kabuğu / güvenli sunucu işlemleri: Streamlit + Python
- Authentication: Firebase Authentication (E-posta/Şifre)
- Database: Cloud Firestore
- Files: Firebase Storage
- Maps: Google Maps JavaScript API + Street View
- PDF: ReportLab
- QR: Python qrcode
- Excel: SheetJS
- Otomasyon: GitHub Actions + Firebase Admin SDK

## PANORIX modülleri

- Dashboard
- Belediyeler
- İhaleler
- EKAP Takip
- Billboardlar
- Harita ve Street View
- Müşteriler
- CRM / Satış Funnel
- Teklifler
- Rezervasyonlar
- Sözleşmeler
- Evrak Merkezi
- Faturalar
- Tahsilatlar
- Finans / Giderler
- Operasyon / İş Emirleri
- Görevler
- Takvim
- Araç Yönetimi
- Raporlar
- Analizler
- Rakip Takip
- Mesaj Merkezi
- Bildirimler ve işlem geçmişi
- Kullanıcı Yönetimi
- Ayarlar
- Profil / Şifre

## Dosyalar

```text
PANORIX/
├── .github/workflows/
│   ├── daily-reminders.yml
│   ├── ekap-sync.yml
│   └── quality.yml
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── jobs/
│   ├── common.py
│   ├── reminder_sync.py
│   ├── ekap_sync.py
│   └── requirements.txt
├── tests/
│   └── test_project_integrity.py
├── app.py
├── index.html
├── logo.png
├── background.png
├── firestore.rules
├── storage.rules
├── firestore.indexes.json
├── firebase.json
├── requirements.txt
├── requirements-dev.txt
├── KURULUM_REHBERI.md
├── YONETICI_HESABI_KURULUMU.md
├── FIREBASE_VERI_MODELI.md
└── ENTEGRASYON_VE_SINIRLAR.md
```

## Güvenlik özeti

- Gerçek Firebase Service Account yalnız Streamlit Secrets ve GitHub Actions Secrets içinde tutulur.
- Service Account bilgisi tarayıcıya gönderilmez.
- Custom component statik klasörü çalışma anında izole edilir; `.streamlit` ve sunucu dosyaları web bileşeni tarafından servis edilmez.
- Her iş kaydında `organizationId` zorunludur.
- Firestore Rules, kullanıcı profilini ve rol/yetki matrisini kontrol eder.
- Hard delete kapalıdır; iş kayıtları soft delete ile arşivlenir.
- Audit log kayıtları sonradan değiştirilemez veya silinemez.
- Super Admin pasife alınamaz ve silinemez.
- Kullanıcı oluşturma ve rol değişiklikleri yalnız doğrulanmış Admin SDK köprüsünden yapılır.


## İlk yönetici hesabı

Bu sürümde demo hesap ve ekrandan kurulum kodu kullanılmaz. İlk yönetici yalnız Streamlit Secrets içindeki güvenli ayarlardan otomatik hazırlanır. Yönetici parolası hiçbir GitHub dosyasına yazılmaz.

## İlk çalışma sırası

1. Kodları GitHub'a yükleyin.
2. Firebase projesi ve Web App oluşturun.
3. E-posta/Şifre Authentication yöntemini açın.
4. Firestore ve Storage oluşturun.
5. `firestore.rules` ve `storage.rules` içeriklerini yayınlayın.
6. Gerekli Firestore indexlerini oluşturun.
7. Google Maps JavaScript API anahtarı oluşturun.
8. Streamlit Cloud uygulamasını `app.py` ile yayınlayın.
9. Streamlit Secrets alanına Firebase bilgileriyle birlikte `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`, `INITIAL_ADMIN_NAME` ve şirket bilgilerini girin.
10. Uygulamayı Deploy/Reboot edin. PANORIX ilk Super Admin hesabını Firebase Authentication ve Firestore içinde otomatik oluşturur.
11. Giriş ekranında tanımlanan yönetici e-posta adresiyle giriş yapın.
12. İlk başarılı girişten sonra güvenlik için `INITIAL_ADMIN_PASSWORD` satırını Streamlit Secrets alanından silebilirsiniz.

Tüm ekran adımları için `KURULUM_REHBERI.md`; yalnız yönetici hesabı için `YONETICI_HESABI_KURULUMU.md` dosyasını kullanın.

## Önemli sınırlar

Bu teslimatta Firebase, temel PANORIX CRUD akışları, harita, dosya, rapor, QR, kullanıcı/yetki, hatırlatma ve mesajlaşma çekirdeği çalışır durumdadır. Aşağıdaki hizmetler sağlayıcı hesabı ve ek sözleşme gerektirdiği için doğrudan etkin değildir:

- WhatsApp Business mesaj gönderimi
- SMS sağlayıcısı
- Push notification
- E-fatura/e-arşiv
- Yetkili/resmî EKAP API veya veri akışı
- Canlı ekonomi, altın ve hava durumu sağlayıcıları
- Firebase Identity Platform tabanlı MFA/2FA

`jobs/ekap_sync.py`, yalnız kullanma yetkiniz bulunan bir JSON API/veri akışına bağlanır; EKAP sitesini kazımaz.
