# PANORIX Firebase Veri Modeli

Cloud Firestore şemasız bir veri tabanıdır; PANORIX uygulaması aşağıdaki ortak alanları ve collection sözleşmelerini uygular.

## Bütün iş collection'larında ortak alanlar

| Alan | Tür | Açıklama |
|---|---|---|
| `organizationId` | string | Şirket/tenant ayrımı |
| `no` | string | Modüle özel otomatik kayıt numarası |
| `createdAt` | timestamp | Oluşturulma zamanı |
| `createdBy` | string | Oluşturan Firebase UID |
| `createdByName` | string | Oluşturan kullanıcı adı |
| `updatedAt` | timestamp | Son güncelleme zamanı |
| `updatedBy` | string | Güncelleyen Firebase UID |
| `updatedByName` | string | Güncelleyen kullanıcı adı |
| `isDeleted` | boolean | Soft delete durumu |
| `deletedAt` | timestamp | Arşivlenme zamanı |
| `deletedBy` | string | Arşivleyen Firebase UID |

## Collection listesi

### `users`

Firebase Authentication kullanıcısına karşılık gelen profil belgesidir. Belge kimliği Firebase UID ile aynıdır.

Başlıca alanlar:

- `email`, `fullName`, `phone`
- `role`
- `department`, `title`
- `organizationId`, `organizationName`
- `active`, `isDeleted`, `isSuperAdmin`
- `permissions`: modül/aksiyon bazlı özel yetki haritası

Roller:

- `super_admin`
- `admin`
- `manager`
- `sales_manager`
- `sales_rep`
- `accounting`
- `operations_manager`
- `operations_staff`
- `field_staff`
- `guest`

Aksiyonlar:

- `view`
- `create`
- `update`
- `delete`
- `approve`
- `export`

### `municipalities`

Belediye kimliği, iletişim, ihale birimi, banka/cari bilgiler ve borç takibi.

### `tenders`

Belediye bağlantısı, ihale numarası, tarih, süre, geçici/kesin teminat, sözleşme ve uyarı tarihleri.

### `ekapTenders`

Yetkili veri akışından bulunan ihale ilanları, eşleşen anahtar kelime, kaynak bağlantı, yayın/son başvuru tarihleri ve takip durumu.

### `billboards`

Kod, reklam alanı türü, adres, il/ilçe/mahalle, enlem/boylam, durum, ölçüler, yön, aydınlatma, fiyat, belediye/ihale bağlantısı ve fotoğraf.

Durumlar:

- Boş
- Kirada
- Rezerve
- Bakımda
- Pasif

### `customers`

Firma, vergi bilgileri, yetkili, telefon/e-posta, adres, cari bakiye, müşteri skoru ve notlar.

### `leads`

CRM fırsatları, müşteri, satış temsilcisi, tahmini değer, olasılık, son aktivite ve funnel aşaması.

### `offers`

Teklif numarası, müşteri, billboard kalemleri, kampanya tarihleri, iskonto, KDV, toplamlar, para birimi ve onay durumu.

### `reservations`

Müşteri, teklif, seçili billboard kimlikleri, başlangıç/bitiş tarihleri ve rezervasyon durumu. Uygulama aynı billboard için tarih çakışmasını kontrol eder.

### `contracts`

Rezervasyon/müşteri bağlantısı, sözleşme numarası, tarih aralığı, tutar, ödeme planı, imza durumu ve dosya.

### `documents`

Şartname, sözleşme, teminat, teslim tutanağı, fatura, belediye yazışması ve görsel onay dosyaları. İlişkili modül ve kayıt kimliğiyle etiketlenir.

### `invoices`

Müşteri/sözleşme, fatura numarası, tarih, vade, matrah, KDV, toplam, tahsil edilen, bakiye ve durum.

### `payments`

Müşteri, fatura, tarih, tutar, para birimi, ödeme yöntemi, dekont/referans ve durum. Onaylı tahsilatlar fatura bakiyesini otomatik günceller.

### `expenses`

Belediye ödemesi, teminat, vergi, bakım, montaj, vinil, yakıt, personel, sigorta ve diğer giderler.

### `operations`

Montaj, söküm, vinil, temizlik, bakım, arıza, keşif ve fotoğraf kontrol iş emirleri; billboard, müşteri, sözleşme, araç, sorumlu ve malzeme bağlantıları.

### `tasks`

Görev, modül bağlantısı, sorumlu kullanıcı, başlangıç/hedef tarih, öncelik ve durum.

### `vehicles`

Plaka, tür, marka/model, yakıt, durum, sigorta, muayene, kasko ve bakım tarihleri.

### `competitors`

Rakip firma, bölge, belediye/ihale bağlantısı, ihale bedeli ve sözleşme süresi.

### `messages`

- `senderId`, `receiverId`
- `participants`: iki kullanıcı UID'si
- `body`
- `readBy`
- `organizationId`

Mesajlar yalnız katılımcılar tarafından okunabilir.

### `notifications`

- `recipientIds`
- `readBy`
- `type`, `title`, `message`
- `recordId`, `targetDate`, `daysLeft`

Günlük job; ihale, teminat, sözleşme, fatura, görev ve araç tarihleri için 365/180/90/30/7/1/0 gün uyarıları oluşturur.

### `auditLogs`

- `userId`, `userName`
- `module`, `action`, `recordId`
- `oldData`, `newData`
- `createdAt`

Audit log güncellenemez ve silinemez.

### `settings`

Belge kimliği `organizationId` değeridir. Şirket adı, para birimi ve dashboard ekonomi göstergeleri saklanır.

### `counters`

Modül/yıl bazlı kayıt numarası üretir. Belge kimliği:

```text
organizationId_module_yıl
```

## Storage yolu

Bütün yüklemeler şu biçimde saklanır:

```text
organizations/{organizationId}/{module}/{recordId}/{timestamp}_{filename}
```

İzin verilen başlıca türler:

- Görseller
- PDF
- Word
- Excel
- Metin dosyaları

Tek dosya üst sınırı 20 MB'dir.

## Firestore güvenlik yaklaşımı

- Kullanıcının `users/{uid}` profili aktif olmalıdır.
- Belge `organizationId` değeri kullanıcının şirketiyle eşleşmelidir.
- İstenen işlem rol varsayılanı veya özel yetkiyle izinli olmalıdır.
- Oluşturmada `createdBy` mevcut UID olmalıdır.
- Güncellemede `createdAt`, `createdBy` ve `organizationId` değiştirilemez.
- Güncellemede `updatedBy` mevcut UID olmalıdır.
- Hard delete yasaktır.
- Soft delete için `delete` yetkisi gerekir.
