# PCB / DFM incelemesi

Güncel deneme **0.3 / 35 × 28 mm**: [test raporu](size-trial-35x28.md),
[Gerber ZIP](../release/collar-tracker-0.3-35x28-dfm.zip). Yerel kontroller geçti;
yeni JLCDFM sonucu henüz yok. Aşağıdaki 30 × 22 mm / 0.2.1 bölümü, korunmuş
önceki kartın raporu ve devre/RF açıklarıdır.

Göksel önceki GIMP kartındaki gibi Python/KiCad API ile native PCB ve üretici
sitesine yüklenebilen Gerber ZIP istedi. Çalışma `pcbnew` 10.0.7 ve yerel
Freerouting 2.4.1 ile yapıldı. Kaynak: gerçek KiCad XML netlisti.

Paket: `release/collar-tracker-0.2.1-dfm.zip`. Son KiCad DRC: 0 hata,
0 açık bağlantı, 0 şema eşleşme sorunu; yerel baskı/maske düzenlemelerine ait
43 kütüphane footprint farkı uyarısı var. Gerber dış hattı 30 × 22 mm,
Excellon 75 adet 0.20 mm kaplı delik içeriyor. Eski 0.2 ZIP korunuyor.
İkinci JLCDFM raporu da incelendi: 0.2.1'de 2 Danger ve 306 Warning kaldı.
Maske köprüsü ve baskı mesafesindeki kırmızı bulgular kapandı; iki pad-aralığı
kırmızısı sürüyor. Üretici analizi temiz değil.
Yerel DRC üretim onayı değildir; bulgular/düzeltmeler `jlc-dfm-review.md` içinde.

Kart 30 × 22 mm, dört bakır katman, hedef kalınlık 0.8 mm; 53 footprint içeriyor.
J3/J4 şarj/pil lehim padleri, J5 dijital nabız genişletme padleri, J6 harici SIM
padleri, J7 1.8 V debug temasları. Kart üzerinde gerçek eSIM veya nabız sensörü
yok. Bazı küçük parçalar alt yüzde; önceki mekanik hacim çalışması bu gerçek
PCB ile henüz yeniden birleştirilmedi.

Sinyaller 0.15 mm nominal, dar pad çıkışlarında en az 0.10 mm; güç sınıfı
0.30 mm nominal. Clearance 0.10 mm, via 0.45/0.20 mm, delik-bakır 0.20 mm,
kenar-bakır 0.30 mm. İlk 0.15 mm minimum hedefi, dar pad çıkışları için
0.10 mm olarak belirlendi. Bu, [JLCPCB'nin çok katmanlı 1 oz kapasitesi](https://jlcpcb.com/capabilities/pcb-capabilities)
içinde; akım taşıma, gerilim düşümü veya RF doğrulaması değil.
Yerel tamamlamada bazı güç bağlantıları 0.15 mm; güç sınıfı ayarı bütün yolun
0.30 mm olduğu anlamına gelmez. Dört katmanda da sinyal yolları ve GND dolgusu
var; iç katmanlar kesintisiz RF referans düzlemi değil. Güç/RF incelemesi açık.

Sipariş öncesi açıklar: donanımsal düşük voltaj kesme, VDD_GPIO sıralaması,
giriş koruması, pil/NTC, gerçek eSIM ve operatör profili, nabız ölçüm yöntemi,
antenler, RF/laminat dizilimi, stencil/assembly ve fiziksel test.

Nordic DK paketi 1.0.0 içindeki PCA10171 board 1.0.1 / `400797.PcbDoc`
KiCad Altium okuyucusuyla incelendi. Kaynak paketin SHA256 değeri:
`535974f95549ea418a6004861a7b2c3daa47606082e5b5d106d35012283f1af3`.
SKY65943 footprint'i buradan alındı; Skyworks 204404H sayfa 9 da görüntülendi.
Merkez pad maskesi ve üç pasta penceresi ayrı çizimlerdir. 0.2.1'de merkez
pad yalnız bakır katmanında bırakıldı; ayrı maske/pasta çizimleri korunarak
geçersiz negatif margin gösterimi kaldırıldı. Assembly incelemesi açık.

BQ25185: KiCad Texas DLH0010A footprint'i. LIS2DW12: LGA-12 2×2 mm.
nRF community footprint'inin 112 pin konum/boyutu DK karşılaştırmasına uydu;
pin 1 pad/ek özel şekil temsilindeki fark güncel üretici çizimiyle uzlaştırılacak.
Ham veri `evidence/nordic-reference-footprints.json` içinde.

`build_draft.py` şemayı, `build_pcb.py` PCB yerleşimini üzerine yazar.
Başlangıç şeması `snapshots/pre-pcb-20261024` altında korundu.
`scripts/import_route.py` seçilmiş SES dosyasını içe aktarır ve pad yerleşimini
kaynakla karşılaştırır. `scripts/export_dfm.py` normal pakette DRC hatası veya
açık bağlantı varsa dışa aktarımı engeller. Son DRC ve paket manifesti birlikte
okunmalı; bu belge tek başına test sonucu değildir.

Son rota `build/pcb/collar-r6.ses` dosyasından geldi; `scripts/finish_pcb.py`
kalan beş bağlantıyı ve BAT çıkışını çevreleyen CHG_FAULT yolunu tamamladı.
Ardından aynı netin mevcut via bakırı içinde kalan iki yeni via kaldırıldı;
bağlantı sürekliliği son DRC ile doğrulandı. Ara durumlar ve değişiklik kanıtı
`evidence/local-routing-fixes.json`, `evidence/pcb-finished-drc.json` ve
`build/pcb/pre-via-cleanup.kicad_pcb` altında. Bu üretim scriptlerini tekrar
çalıştırmak elle tamamlanmış PCB'nin üzerine yazar; mevcut paketi tekrar üretmek
için yalnız `python3 scripts/export_dfm.py` yeterli.

0.2.1 için `fix_jlc_dfm.py`, `place_dfm_labels.py`, `apply_dfm_labels.py`
eski PCB kopyasına deterministik düzeltmeyi uygular; Shapely 2.1.2 yalnız
geometri kontrollerinde `.venv-dfm` altında kullanılır. `export_dfm.py`
yerel öncesi/sonrası geometri kontrolünü ve KiCad DRC'yi paketlemeden çalıştırır.

İlk paketi kullanıcı JLCDFM'ye yükledi. Asistan dış yükleme, sipariş veya
fiziksel test yapmadı.
