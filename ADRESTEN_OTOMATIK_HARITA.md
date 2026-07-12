# Adresten Otomatik Harita

## Kullanıcı işlemi

1. **Billboardlar** menüsüne girin.
2. **Yeni Kayıt** butonuna basın.
3. İl, ilçe, mahalle ve açık adresi doldurun.
4. **Kaydet** butonuna basın.
5. PANORIX adresi otomatik bulur ve koordinatları Firestore kaydına ekler.
6. **Harita** menüsünü açtığınızda billboard işaretli görünür.

Enlem ve boylam kullanıcı tarafından girilmez. Adres değişmediği sürece harita servisine tekrar istek gönderilmez. Adres değiştirilip kayıt yeniden kaydedildiğinde konum yeniden hesaplanır.

## Adres bulunamazsa

Açık adresi şu sırayla daha ayrıntılı yazın:

```text
Cadde veya sokak, bina numarası, mahalle, ilçe, il
```

Örnek:

```text
Atatürk Bulvarı No: 25, Kızılay Mahallesi, Çankaya, Ankara
```
