# 0.3.1 — ölçülmüş maske/pad düzeltmesi — 2026-10-25

Sonradan gelen doğrulama: 2026-10-25 01:28:03 JLCDFM raporu bu revizyonda
**0 Danger / 45 Warning** verdi. Negatif maske 22 → 2, çok parçalı maske
2 → 0; diğer üç kategori 10/30/3 olarak kaldı. SMT seçili değil.
Kanıt `evidence/jlc-dfm-20261025-r5`; sonraki aday `docs/mask-revision-0.3.2.md`.
Aşağıdaki bölüm ilk teslim anındaki durumu kaydeder; eski ZIP değişmedi.

Son kullanıcı raporu `collar-tracker-0.3-35x28-dfm.zip` dosyasına ait;
2026-10-25 00:42:22 tarihinde yine **0 Danger / 67 Warning** veriyor.
Önceki turda 0.3 değiştirilmemişti. Bu tur ayrı 0.3.1 kaynak ve ZIP üretildi.
**0.3.1 için üretici DFM sonucu henüz yok; sıfır turuncu iddiası yok.**

| Değişiklik | Önce | 0.3.1'de ölçülen |
|---|---:|---:|
| C1/C2/C5/C8 bakır pad aralığı | 0.18 mm | 0.25 mm |
| Aynı parçaların maske köprüsü | 0.18 mm | 0.20 mm |
| J3–J7 temas padlerinin maske payı | 0 | 0.05 mm |
| J1/J2 ortak maske açıklığını oluşturan şekil sayısı | 4'er | 1'er |
| U2.1 maskesi → GNSS_LNA_EN kontrol yolu | 0.1517 mm | 0.2100 mm |
| GND bölgesi clearance ayarı | 0.20 mm | 0.25 mm |

Dört 0201 kondansatör için 0.30 × 0.35 mm pad ve 0.55 mm pitch kullanıldı;
padler merkez yönüne 0.045 mm taşındı. Ayrı paste-only padler de aynı şekil
ve merkeze getirildi. Maske payı +0.025 mm. Seçim, [Murata'nın GRM ailesi
referansındaki](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM0115C1C100GE01-01A-EN_PDF_CERAMICCAPACITORSMD?lastModifiedDatetime=20250813132738)
GRM03 / 0.6 × 0.3 mm tablolarının ortak aralığında: a=0.25, b=0.30, c=0.35 mm.
Bu genel aile kılavuzuyla uyumlu bir reflow adayıdır; kesin sipariş kodu,
parça toleransı ve gerçek montaj değerlendirmesi henüz tamamlanmadı.

U.FL açıklıkları eski teslimin gerçek Gerberinden birleştirildi; pad bakırı,
pasta ve fiziksel bakır keepout'u korundu. Tek poligon üretmek, JLC'nin
compound-mask uyarısını kapattığının kanıtı değildir. Arkların poligona
yaklaştırılma hatası da hesaba katıldığında sınır farkı 0.00002 mm altındadır.
Yerel eski KiCad pad poligonları bu köşelerde yaklaşık 0.0074 mm kaba fark
verdiğinden karşılaştırma gerçek Gerber açıklıkları üzerinden yapıldı.

Yalnız üç GNSS_LNA_EN kontrol yolunun uçları değişti. Bütün RF yolları,
diğer yollar, net eşleşmeleri ve 77 via korundu. GND dolguları 0.25 mm
clearance ile yeniden dolduruldu; bağlantılar tekrar doğrulandı. İki alt
yüz etiketi 0.10 mm taşındı; kart üzerinde `COLLAR 0.3.1 TEST` yazıyor.

## Doğrulama

- Native KiCad: 0 hata, 0 açık bağlantı, 0 şema uyuşmazlığı; 47 kütüphane
  footprint farkı uyarısı açıkça tutuldu. DRC severity/exclusion değiştirilmedi.
- 53 footprint / 792 yol / 77 via, 35 × 28 × 0.8 mm aday, dört bakır katmanı.
- Pad dış kutusu–via ve farklı net yolu ≥0.20 mm; via–via ≥0.2026 mm.
- Native ve gerçek Gerber karşılaştırmasında 0.10 mm altı ayrı maske köprüsü yok.
- Gerberde dört kondansatörün bakır/maske aralıkları ve yeni pasta eşleşmeleri
  bağımsız ölçüldü; belirtilmeyen bütün pad bakırları öncekiyle aynı.
- 214 üst + 54 alt bakır padin 267'si maske içinde tamamen açık; yalnız U2.11'in
  DK kaynaklı merkez padindeki kısmi örtü aynı kaldı. Bu, JLC'nin 22 negatif
  maske uyarısının kapanış kanıtı değildir.
- Gerber dış hattı, 77 adet 0.20 mm delik, ZIP CRC'si ve bütün iç dosya hashleri
  doğrulandı. Eski 0.3 PCB/ZIP ve 0.2.1/30 × 22 mm kaynak değişmedi.
- Üst/alt native bakır ve baskı görselleri incelendi. Fiziksel/enerjili test yok.

## Açık kalanlar

U5'in sabit 0.15 mm pad aralıkları, U2'nin 0.125–0.1485 mm maske komşulukları,
U2 merkez maskesi ve nRF land/mask incelemesi sürüyor. [JLC kapasite tablosu](https://jlcpcb.com/capabilities/pcb-capabilities)
farklı-net SMD padlerinde 0.15 mm, 1 oz renkli maskede 0.10 mm köprü bildiriyor;
bazı genel turuncu uyarılar bu sınırların içinde olabilir. Proses/renk/bakır
ve montajcı kabulü yerine geçmez.

U1'in 1:1 pasta çıktısı değiştirilmedi. Önceki incelemedeki yorumun sınırı:
[Nordic](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html)
1:1 pasta verisinin montajcıya gönderilip montajcı tarafından ayarlanmasını
olağan iş akışı olarak tarif ediyor. Dolayısıyla 1:1 dosya tek başına kesin
tasarım hatası değildir; final stencil'in montajcıyla belirlenmesi açık iştir.
Montajcı girdisi olmadan hazırlanacak stencil için ayrıca alan azaltma
önerileri var; bu revizyon stencil üretim onayı vermiyor.

Tam çalışan, kullanıcı lehimi gerektirmeyen teslim hedefi korunuyor. BOM,
gerçek eSIM/pil/anten, güç sıralaması/UVLO/ESD, RF/stackup, firmware,
fikstür ve fonksiyon testleri açık. Bu dosya bir DFM inceleme paketi.

## Dosyalar

Yeni ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.1-35x28-dfm.zip`

Kaynak: `/Users/gok/codex/projects/collar-tracker/experiments/35x28-mask-r031/hardware/collar-tracker.kicad_pcb`

Kanıtlar aynı deneyin `evidence` dizininde: `final-drc.json`,
`geometry-checks.json`, `gerber-mask-audit.json`, `gerber-revision-checks.json`,
`changes.json`, `delivery.json`. Tekrar üretim sırası: `revise_mask_031.py plan`
(.venv-dfm), `apply` (KiCad Python), `dfm_geometry.py`, `size_trial_labels.py`
plan/apply, tekrar geometri ve `check_size_trial.py --mask-revision-031`,
`export_mask_revision.py`, Gerber denetimleri. Apply önceki 0.3'ten başlar;
sonraki elle düzenlemeler varsa üzerine çalıştırma. Export mevcut 0.3.1 ZIP'in
üzerine yazmayı reddeder; yeni değişiklikler yeni revizyon gerektirir.
