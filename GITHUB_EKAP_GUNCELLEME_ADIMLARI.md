# GitHub EKAP Güncelleme Adımları

## Zorunlu güncellenecek dosyalar

```text
.github/workflows/ekap-sync.yml
jobs/ekap_sync.py
jobs/requirements.txt
index.html
```

## Test için güncellenecek dosyalar

```text
tests/test_project_integrity.py
tests/test_ekap_sync.py
```

## Açıklama dosyaları

```text
EKAP_OTOMATIK_ENTEGRASYON.md
KURULUM_REHBERI.md
ENTEGRASYON_VE_SINIRLAR.md
README.md
KALITE_RAPORU.md
TESLIM_MANIFESTOSU.md
```

## Yükleme

1. GitHub PANORIX repository'nizi açın.
2. `Add file → Upload files` seçeneğine basın.
3. Güncelleme paketinin içindeki dosya ve klasörleri repository ana dizinine sürükleyin.
4. Dosya yollarının `.github/workflows/ekap-sync.yml` ve `jobs/ekap_sync.py` şeklinde olduğundan emin olun.
5. Commit mesajı olarak `Add automatic public EKAP monitoring` yazın.
6. `Commit changes` butonuna basın.
7. GitHub `Actions` sekmesinden `PANORIX Otomatik EKAP Takibi` işini manuel çalıştırın.
