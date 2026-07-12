# PANORIX Teslimat Manifestosu

## Uygulama

- `app.py` — Streamlit kabuğu, Firebase Admin köprüsü, otomatik ilk Super Admin oluşturma, PDF ve QR üretimi
- `index.html` — Referans projeyle uyumlu HTML/CSS/JavaScript arayüzü ve Firebase istemcisi
- `logo.png` — Kullanıcının sağladığı PANORIX logosu
- `background.png` — Kullanıcının sağladığı uygulama arka planı

## Firebase

- `firestore.rules` — tenant/rol/yetki, soft delete ve audit güvenlik kuralları
- `storage.rules` — şirket bazlı dosya erişimi ve yükleme kısıtları
- `firestore.indexes.json` — mesaj ve bildirim sorgu indexleri
- `firebase.json` — Firebase CLI yapılandırması

## Otomasyon

- `jobs/reminder_sync.py` — günlük ihale, teminat, sözleşme, tahsilat, görev ve araç uyarıları
- `jobs/ekap_sync.py` — yalnız yetkili JSON feed üzerinden ilan eşleştirme
- `.github/workflows/daily-reminders.yml`
- `.github/workflows/ekap-sync.yml`
- `.github/workflows/quality.yml`

## Dokümantasyon

- `README.md`
- `KURULUM_REHBERI.md`
- `FIREBASE_VERI_MODELI.md`
- `ENTEGRASYON_VE_SINIRLAR.md`
- `KALITE_RAPORU.md`
- `TESLIM_MANIFESTOSU.md`

## Test

- `tests/test_project_integrity.py` — 14 otomatik bütünlük/güvenlik testi
- `scripts/extract_app_js.py` — JavaScript syntax kontrolü için çıkarma aracı
