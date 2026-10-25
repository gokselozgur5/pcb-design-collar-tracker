# 0.3.4 — U1.71 toprak bağlantısı

0.3.3 için ilk JLC kaydımız 0/0 gösteriyordu. Kankamın ekran görüntüsü ve
teslim ZIP'inin yeniden yüklenmesi **0 Danger / 1 Warning** verdi. Tek bir
sıfır sonucunu tamamlanmış kabul etmemiz yetersizdi. Önceki PDF/ZIP korundu;
`release/collar-tracker-0.3.3-recheck.json` bu karşı bulguyu kaydediyor.
Aynı ZIP'in farklı analiz sonuçları vermesinin nedeni henüz belirlenmedi.

## Düzeltme

Gerçek tekrar analizinin ham koordinatları kalan 0.080419 mm boşluğu
**U1.71** üzerinde gösterdi. U1.30 ve U1.71 simetrik ama ayrı bağlantılar;
önceki U1.30 tespiti U1.71'in de temiz olduğunu göstermiyordu.

Yalnız U1.71 GND yolunun bir kesimi **0.20 → 0.30 mm** genişletildi.
Yolun uçları, neti ve katmanı aynı. Pad/maske/pasta, bileşenler, bütün
via/delikler ve kontrol kuralları değişmedi. GND dolgusu yenilendi; sürüm
etiketi/title 0.3.4 oldu.

`scripts/verify_clearance034.py` gerçek JLC ölçüm çizgisini kullanıyor:
eski yolun dışında 0.080419 mm kalıyor; yeni GND bakırı çizginin tamamını
kapsıyor. Böylece eskiyi reddeden, yeniyi geçiren bir geometri kontrolü var.
KiCad tüm severity/tüm yollar/şema eşleşmesinde **0 hata / 0 uyarı /
0 açık / 0 parity**. In1/In2/B.Cu, iki maske/pasta, delik ve outline
çıktıları tarih/sürüm meta verisi dışında aynı.

## Kanıt ve teslim

**İki bağımsız yükleme de 0 Danger / 0 Warning verdi.** Birinci rapor
2026-10-25 06:39:36, ikinci rapor 06:41:25; ikisi de PCB seçili / SMT kapalı.
İki PDF de tamamen görüntülendi. İkinci yükleme son teslim yolundaki ZIP'i
kullandı; sonradan dosya yeniden üretilmedi veya değiştirilmedi.

- [İlk JLC kaydı](https://jlcdfm.com/viewer?pcbUploadFileId=637107561329414146)
- [İkinci JLC kaydı](https://jlcdfm.com/viewer?pcbUploadFileId=637107883633496065)
- ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.4-35x28-dfm.zip`
- Son PDF: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.4-jlc-dfm-report.pdf`
- Makine tarafından doğrulanmış teslim kaydı: `release/collar-tracker-0.3.4-verification.json`.

- Kaynak: `experiments/35x28-clearance-r034/hardware/`.
- Yerel kanıt: `experiments/35x28-clearance-r034/evidence/local-checks.json`.
- JLC kayıtları: `evidence/zero-warning-r033/candidate034-check1/` ve `candidate034-check2/`.
- ZIP SHA256: `735ff8506629eb931cdd4a1847796e0eae2ec24deebb4f579f7441bb2182c990`.
- Kaynak SHA256: `597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2`.

ZIP 132624 byte / 14 dosya. Son PDF SHA256:
`d85511db1fd7d8b826c86be4ad319612ad53d5e809f8e5eda46b0aadb886d7c8`.
JLC kural dosyası öncekiyle aynı SHA256:
`f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.

`scripts/finalize_clearance034.py`, iki farklı JLC kayıt numarası, aynı
yükleme SHA256'sı, tam analiz edilmiş 29 satır, sıfır kırmızı/turuncu,
değişmeyen kural dosyası ve ham ölçümleri birlikte şart koşuyor.
Tarayıcı aracı yalnız yeni yüklemenin kayıt numarasını izliyor; bütün
analiz satırlarının iki ardışık okumada sabit kalmasını bekliyor.

Bu çalışma PCB DFM kapsamındadır. 0.3.3'teki U5 land/U2 maske süreç
uyarlamalarının SMT kalifikasyonu ve diğer elektrik/RF/BOM/eSIM/firmware/
fikstür/kutu gereksinimleri devam ediyor; çalışan PCBA kabulü değildir.
