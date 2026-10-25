# 35 × 28 mm deneme — 0.3 — 2026-10-24

35 × 28 mm kart, yerel bağlantı ve geometri kontrollerini geçti. Bu sonuçla
40 × 30 mm'ye çıkmak için henüz gerekçe yok. Yeni JLCDFM raporu
(2026-10-24 21:45:56) 0 Danger / 67 Warning gösteriyor. SMT montaj analizi
seçili değil; devre/RF/assembly incelemeleri hâlâ açık.

| Kontrol | Sonuç |
|---|---:|
| Gerber dış hat ölçüsü | 35 × 28 mm |
| Katman / footprint | 4 / 53 |
| KiCad hata / açık bağlantı / şema uyuşmazlığı | 0 / 0 / 0 |
| Kütüphane footprint farkı uyarısı | 43 |
| Minimum çizilmiş yol genişliği | 0.20 mm |
| GND dolgusu minimum genişlik ayarı | 0.20 mm |
| Via bakır / delik / nominal halka | 0.60 / 0.20 / 0.20 mm |
| Gerçek Excellon kaplı delik sayısı | 77 |
| Pad dış dikdörtgeni → via bakırı, bütün netler | ≥ 0.20 mm |
| Pad dış dikdörtgeni → farklı net yolu | ≥ 0.20 mm |
| Via → via, bütün netler | ≥ 0.2026 mm |
| Maskede 0.10 mm altı ayrı açıklık arası köprü | 0 |
| Baskı → pad/maske / delik minimumu | 0.229 / 0.316 mm |
| Gerber katmanı / ZIP dosyası | 11 / 19 |
| Yeni JLCDFM PCB analizi | 0 Danger / 67 Warning |
| SMT montaj analizi / fiziksel test | Yapılmadı / yapılmadı |

30 × 22 mm referansın alanı 660 mm², denemenin alanı 980 mm² (+%48.5).
Önceki minimum çizilmiş yol 0.10 mm, via halkası 0.125 mm idi. Üretici
raporundaki iki pad-spacing Danger, yeni üretici raporunda sıfıra indi.
Pad köşelerini de kapsayan yerel kontrol üreticinin özel algoritmasının
kopyası değildir; bu kapanışın kanıtı kullanıcının yeni JLCDFM raporudur.
Kalan beş uyarı kategorisi ve bağımsız Gerber incelemesi
`docs/jlc-dfm-review.md` içinde. 0.3 ZIP'in içindeki NOT RUN notu paketleme
anına aittir; teslim edilmiş ZIP değiştirilmedi.

İki iç katmanı da GND'ye ayıran ilk deneme tüm bağlantıları kapatamadı.
Geçen adayda In1.Cu üzerinde sinyal yolu yok; In2.Cu üzerinde 116 sinyal/güç
segmenti ve GND dolgusu var. Toplam 792 yol segmenti. RF yollarının 50 Ω,
anten/geri dönüş yolu veya elektromanyetik performans doğrulaması yapılmadı.

Yerleşim ve bütün yollar yeniden çalışıldı. Şarj bölgesindeki bazı GND
yolları açılarak dolgu ve ek GND vialarıyla bağlantı yeniden kuruldu. Son
kontrol bütün netlerin bağlı olduğunu doğruluyor. Yeni pad bakır şekilleri,
pad/net eşleşmeleri ve maskeler, konum değişiklikleri dışında 0.2.1 ile aynı.
Router'a yalnız geçici, daha muhafazakâr dikdörtgen pad engelleri verildi;
native kartta fiziksel padler bu amaçla değiştirilmedi.

Sabit paketlerin kendi pad aralıklarında 12 çift 0.15–0.18 mm aralığında.
`collar-tracker.kicad_dru` yalnız **aynı footprint'in iki padine** 0.15 mm
kuralını uygular; yollar/vialar 0.20 mm kontrolüne tabi. Genel DRC exclusion
veya severity düşürme yok. 43 uyarı, 0.2.1'den gelen yerel footprint baskı/maske
düzenlemeleridir. U.FL ortak maske açıklıkları ve nRF footprint/pin-1/stencil
konuları hâlâ assembly incelemesi ister; bütün JLC uyarılarının biteceği iddia edilmez.

Kaynak: [`experiments/35x28-in2/hardware/`](../experiments/35x28-in2/hardware/).
Son [DRC](../experiments/35x28-in2/evidence/final-drc.json),
[bağımsız geometri ölçümleri](../experiments/35x28-in2/evidence/geometry-checks.json),
[ZIP/hash manifesti](../experiments/35x28-in2/evidence/delivery.json),
[üst](../experiments/35x28-in2/previews/final-top.png) ve
[alt](../experiments/35x28-in2/previews/final-bottom.png) bakır/baskı görüntüleri.
İki görünüm de incelendi. ZIP CRC'si, tüm iç dosya hashleri, PCB kaynak hash'i,
Gerber dış hat koordinatları ve Excellon delik sayısı doğrulandı.

Yeni paket: [`collar-tracker-0.3-35x28-dfm.zip`](../release/collar-tracker-0.3-35x28-dfm.zip).
Tekrar paketleme: `python3 scripts/export_size_trial.py`. Script güncel native
DRC'yi çalıştırır, geometri raporunun kaynak hash'ini denetler; hata/açık/parity
veya geometri başarısızlığında durur. PCB değiştiyse önce `dfm_geometry.py` ve
`check_size_trial.py experiments/35x28-in2` yeniden çalıştırılmalıdır.
`build_size_trial.py --inner2-signal` yalnız başlangıç yerleşimini üretir;
tamamlanmış aday üzerinde tekrar çalıştırmak yerel rota tamamlamalarını siler.

Bu paket fiziksel veya enerjili prototip testi değildir. Güç/UVLO/VDD_GPIO,
pil/NTC/ESD, gerçek eSIM/operatör, nabız donanımı, anten/stackup ve assembly
açıkları sürüyor. J6 harici SIM arayüzü, J5 dijital genişleme arayüzüdür.
Önceki 38 × 30 mm kutu maketi bu PCB için tekrar doğrulanmadı. Sipariş veya
asistan tarafından üretici yüklemesi yapılmadı; önceki 0.2/0.2.1 ZIP'ler ve
`hardware/` altındaki 30 × 22 mm kaynak korundu.
