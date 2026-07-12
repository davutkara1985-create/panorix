# PANORIX İlk Yönetici Hesabı

Bu sürümde demo hesap ve ekrandan kurulum kodu yoktur.

İlk Super Admin hesabı, Streamlit Cloud **Secrets** alanındaki bilgilerle otomatik oluşturulur. Yönetici parolası GitHub repository dosyalarına yazılmaz ve tarayıcıya gönderilmez.

## Streamlit Secrets alanına eklenecek bölüm

```toml
INITIAL_ADMIN_EMAIL = "davutkara1985@gmail.com"
INITIAL_ADMIN_PASSWORD = "BU-SOHBETTE-BELIRTTIGINIZ-YONETICI-SIFRESI"
INITIAL_ADMIN_NAME = "Davut Kara"
INITIAL_ORGANIZATION_NAME = "PANORIX"
INITIAL_ORGANIZATION_ID = "panorix"
```

`INITIAL_ADMIN_PASSWORD` alanına bu sohbette belirttiğiniz yönetici şifresini yalnız Streamlit Secrets ekranında yazın.

## Otomatik oluşturulan kayıtlar

Uygulama ilk açıldığında:

1. Firebase Authentication içinde yönetici kullanıcısı aranır.
2. Kullanıcı yoksa Secrets alanındaki parola ile oluşturulur.
3. Kullanıcıya `super_admin` ve şirket custom claim bilgileri atanır.
4. Firestore `users/{uid}` profili oluşturulur.
5. Firestore `settings/panorix` şirket ayarı oluşturulur.
6. İşlem `auditLogs` collection'ına kaydedilir.

## İlk girişten sonra

1. Yönetici e-postası giriş ekranında otomatik yazılı gelir.
2. Yönetici şifresiyle giriş yapın.
3. Giriş başarılı olduktan sonra Streamlit Secrets ekranına dönün.
4. `INITIAL_ADMIN_PASSWORD` satırını silin veya değerini boş bırakın.
5. Uygulamayı **Reboot app** ile yeniden başlatın.

Mevcut Firebase Authentication hesabı ve Firestore profili korunur. PANORIX mevcut hesabın şifresini yeniden yazmaz.

## Güvenlik notu

Yönetici şifresi sohbet içinde açıkça paylaşıldığı için ilk girişten sonra **Şifremi Unuttum** akışıyla yeni ve yalnız sizin bildiğiniz bir şifre belirlemeniz önerilir.
