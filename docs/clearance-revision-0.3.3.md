# 0.3.3 — ilk JLC sonucu ve tekrar kontroldeki eksik

**Düzeltme:** Aşağıdaki 06:29:27 tarihli ilk sonuç gerçekti, ancak aynı
teslim ZIP'i tekrar yüklenince 0/1 verdi. Kankam da 1 turuncuyu gösterdi.
Kalan U1.71 bağlantısı ve yeni doğrulama [0.3.4](clearance-revision-0.3.4.md)
çalışmasında ele alınıyor. İlk 0/0, tekrar edilebilir kabul sonucu değildir.

JLC'nin 2026-10-25 **06:29:27** tarihli gerçek raporu, 35 × 28 mm / dört
katmanlı kart için **0 Danger / 0 Warning** gösteriyor. PCB analizi seçili;
SMT seçili değil. Raporun tamamı iki raster bölümde görüntülendi.

- ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.3-35x28-dfm.zip`
- PDF: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.3-jlc-dfm-report.pdf`
- Kaynak: `experiments/35x28-clearance-r033/hardware/`
- [JLC sonucu](https://jlcdfm.com/viewer?pcbUploadFileId=637105049294819330)
- Kanıt: `evidence/zero-warning-r033/candidate033-1/`
- Doğrulama kaydı: `release/collar-tracker-0.3.3-verification.json`

Teslim ZIP'i, JLC'ye yüklenen `collar-tracker-0.3.3-iteration1.zip` ile **bayt
bayt aynı**; yalnız dosya adı değişti. Raporun eski adı göstermesi bu yüzden.
14 Gerber/delik/katman dosyası, 132683 byte. Özel notlar veya hesap bilgileri
ZIP'e eklenmedi. SHA256:
`6fc0fa2a60f7820cf1ea0a2b06f517fcde13f5683420a5f289cc2b1dabe0f312`.

## Gerçek önce/sonra

Önce aynı oturumda 0.3.2 analiz edildi: 0/40. Önceki kullanıcı raporu
0.3.1'deki 45'ti. İki yeni analiz aynı JLC kural dosyasını ve aynı kategori
eşiklerini kullanıyor; hiçbir kontrol/severity kapatılmadı veya gevşetilmedi.
Kural dosyası SHA256:
`f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.

| Warning kategorisi | 0.3.2 | 0.3.3 |
|---|---:|---:|
| Pad aralığı | 10 | 0 |
| Maske köprüsü | 26 | 0 |
| Maske–yakın bakır mesafesi | 2 | 0 |
| Negatif maske | 2 | 0 |

## Fiziksel değişiklikler

- **U2:** altı küçük terminal maskesinde kenar başına 0.050 → 0.025 mm
  genişleme; merkez maskesi 1.55 → 1.50 mm genişlik, 2.90 mm yükseklik aynı.
  Bakır/pasta aynı. Pozitif maske payı korunuyor. Bu, Skyworks Figure 7'nin
  bire bir maskesi değil; [JLC'nin LDI/1:1 maske kabiliyetine](https://jlcpcb.com/capabilities/pcb-capabilities)
  göre yapılmış süreç uyarlaması. Montaj kalifikasyonu hâlâ gerekli.
- **U5:** padlerin yerel boyutu 0.375 × 0.350 → 0.375 × 0.340 mm. Merkezler,
  açı ve pin aralıkları korunuyor. Maske ve pasta pad ile aynı ölçüde;
  lehim alanı %2.857 azalıyor. Bu, [ST TN0018](https://www.st.com/resource/en/technical_note/cd00134799.pdf)
  genel +0.10 mm genişlik önerisinden 0.010 mm sapma; ST'nin aynen onayladığı
  footprint olarak sunulmuyor. Nominal konumdaki maksimum terminal boyutu
  pad içinde kalıyor; yerleştirme/reflow dayanıklılığını bu test kanıtlamıyor.
- **FB1:** iki maskeye 0.025 mm pozitif pay. Bakır/pasta aynı.
- **U1.30:** GND bağlantısının bir kesimi 0.200 → 0.300 mm genişletildi;
  pad genişliğine eşit bağlantı dar dolgu boşluğunu giderdi. Toprak boşluğu
  eklenmedi. Bu kaydın ham koordinatları U1.30'u gösteriyordu. Daha sonraki
  tekrar analizi U1.71'i de buldu; U1.71 eşleştirmesini kesin olarak yanlış
  ilan etmek hataydı. İki simetrik bağlantı ayrı kontrol edilmeliydi.
- **J7.1:** yakındaki SWDIO yolunun üç kesimi 0.0483 mm sola kaydırıldı;
  45° giriş/çıkış, net ve 0.20 mm yol genişliği korundu.
- GND dolguları yenilendi; sürüm etiketi/title 0.3.3 yapıldı.

## Yerel doğrulama ve sınır

KiCad tüm severity, tüm yollar ve şema eşleşmesi: **0 hata / 0 uyarı /
0 açık / 0 parity**. Proje/DRC kuralları ve elektriksel şema aynı.
53 footprint, 792 yol kesimi, aynı 77 via/delik. Gerçek Gerber'de 268 padin
tamamı maske açıklığında; en dar maske köprüsü 0.155 mm. Önceki kaynak ve
ZIP hashleri korundu. Native PCB SHA256:
`ab78d20c04a6b872dec1dfaad2b50d3995f3112f852905cbfc1ee378c5b992ea`.

Bu sonuç **PCB DFM temizliği**dir. SMT, güç/RF/anten, kesin BOM, eSIM/operatör,
firmware, programlama/test fikstürü ve kutu doğrulamaları tamamlanmadı.
Üretim siparişi verilmedi; tam çalışan PCBA kabulü veya montaj onayı değildir.
