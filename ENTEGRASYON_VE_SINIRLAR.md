# Entegrasyonlar ve Sınırlar

## Çalışan entegrasyonlar

### Firebase Authentication

- E-posta/şifre ile giriş
- Oturum kalıcılığı
- Şifremi unuttum e-postası
- Çıkış
- Admin tarafından kullanıcı oluşturma
- Kullanıcı aktifleştirme/pasifleştirme
- Refresh token iptali
- Rol/custom claim güncelleme

### Cloud Firestore

- PANORIX modüllerinde gerçek CRUD
- Şirket/tenant ayrımı
- Soft delete
- Audit log
- Otomatik sıra numarası
- Rol/yetki kontrolü
- Gerçek zamanlı mesaj görünümü

### Firebase Storage

- Billboard fotoğrafları
- Sözleşme/evrak/fatura dosyaları
- Operasyon görselleri
- Şirket ve kayıt bazlı klasör ayrımı

### Google Maps

- Billboard markerları
- Duruma göre renk
- İl/ilçe/durum filtresi
- Marker cluster
- Detay modalı
- Street View panorama

### Raporlama

- Excel dışa aktarma ve içe aktarma
- CSV dışa aktarma
- ReportLab PDF
- Billboard QR kodu

### Otomasyon

- Günlük tarih uyarıları
- Yetkili JSON veri akışından EKAP benzeri ilan eşleştirme
- GitHub Actions zamanlaması

## Sağlayıcı gerektiren, otomatik etkin olmayan alanlar

### EKAP

Uygulama EKAP web sitesini otomatik kazımaz. `jobs/ekap_sync.py` yalnız aşağıdakilerden biri sağlanırsa çalışır:

- Kurumunuzun kullanma yetkisine sahip olduğu API
- Lisanslı veri sağlayıcı JSON servisi
- Kurum içi oluşturulan JSON feed

Gerekli GitHub Secrets:

- `EKAP_FEED_URL`
- `EKAP_FEED_TOKEN` (servis gerektiriyorsa)
- `ORGANIZATION_ID`

### SMS / WhatsApp / Push

Kod tabanında bildirim collection'ı ve uygulama içi bildirim ekranı vardır. SMS, WhatsApp Business ve push gönderimi için sağlayıcı seçimi, sözleşme, şablon onayı ve API bilgileri gerekir. Bu bilgiler verilmeden gerçek gönderim yapılmaz.

### Ekonomi ve hava durumu

Dashboard değerleri şirket ayarlarından girilebilir. Canlı kur, altın, BIST ve hava durumu için lisanslı/veri kullanım koşullarına uygun servis seçilmelidir.

### MFA / 2FA

Bu sürüm Firebase E-posta/Şifre girişini kullanır. SMS veya TOTP tabanlı MFA için Firebase Authentication with Identity Platform yapılandırması ve ayrı akış gerekir.

### E-fatura / muhasebe

E-fatura, e-arşiv veya muhasebe programı entegrasyonu sağlayıcının API sözleşmesine göre ayrıca geliştirilmelidir.

## Mimari sınır

Referans proje korunmak amacıyla frontend ayrı React/TypeScript paketine dönüştürülmemiştir. Tüm ekranlar mevcut `index.html` modül/CRUD deseninde kalır. Bu karar görsel ve davranışsal uyumu sağlar; çok büyük ekiplerde uzun vadeli frontend parçalama ihtiyacı ayrıca değerlendirilmelidir.
