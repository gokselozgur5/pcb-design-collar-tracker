# JLCDFM raporları ve montaj incelemesi

## Son durum — 2026-10-25

**0.3.4: iki bağımsız JLC yüklemesinde 0 Danger / 0 Warning.**
Raporlar 06:39:36 ve 06:41:25; PCB seçili, SMT seçili değil.
KiCad de 0 hata / 0 uyarı / 0 açık / 0 parity. Kurallar aynı.
Son teslim ZIP'i iki rapordaki girdilerle aynı SHA256'ya sahip.
Kaynak ve rapor yolları: `docs/clearance-revision-0.3.4.md`.

0.3.3'ün ilk 06:29:27 raporu 0/0 idi; kullanıcının ekran görüntüsü ve
aynı ZIP'in yeniden yüklenmesi 0/1 verdi. Kalan uyarı U1.71'deydi.
Önceki U1.30 bulgusu ayrı bir simetrik konumdu; U1.71 eşleştirmesini
kesin yanlış ilan etmek ve tek sıfır sonuçla işi kapatmak hataydı.
0.3.4 yalnız U1.71 GND yolunu 0.20 → 0.30 mm genişletiyor; pad/maske/
pasta, diğer yollar, via, bileşen ve kurallar aynı. Yerel regresyon gerçek
JLC ölçüm çizgisinin eski yol dışında kaldığını, yeni GND bakırıyla tamamen
kapandığını doğruluyor. Önceki ZIP/PDF korunuyor; 0.3.3 recheck kaydı mevcut.

## Önceki 0.3.1 / 0.3.2 incelemesi — tarihsel kayıt

Kankamın sonraki “sıfırla” isteğinde, aynı fiziksel 0.3.2 tasarımının ayrı
çalışma kopyasında KiCad uyarıları **47 → 0** yapıldı: özelleşmiş footprint
tanımları proje kütüphanesine kaydedildi; kurallar ve 11 Gerber geometrisi
korundu. Bu aşamada JLC sonucu henüz yoktu; sonraki sonuç yukarıdadır.
Doğrulama ve varsayılan 6 mil / 0.1524 mm eşik bulgusu: `docs/zero-warning-work.md`.

Beşinci rapor (01:28:03) **0.3.1** ZIP'ine ait: **0 Danger / 45 Warning**.
Önceki 67 uyarıdan 22'si kapanmış: negatif maske 22 → 2, çok parçalı maske
2 → 0. Pad aralığı 10, maske köprüsü 30, maske–yol 3 olarak kalmış.
Maske–yol örneği bu kez 0.08 mm; negatif maske örneği 0.04 mm.
PCB analizi seçili, SMT seçili değil. Beş raster bölüm incelendi;
kanıtlar `evidence/jlc-dfm-20261025-r5` altında.

0.08 mm örneği bakır görüntüsü korelasyonu (0.920) ve görsel karşılaştırmayla
U1.71 GND padinin toprak dolgusuna bağlandığı boğaza yerleştirildi. Bu,
iki farklı net arasındaki açıklık hatasının kanıtı değil; JLC kriteri ve diğer
iki örnek açıklığa kavuşmadığı için kategori kapatılmadı. İki negatif maske
örneği kesin koordinatlara yerleştirilemedi. Düşük skorlu eşleşmeler kanıt
sayılmadı; PDF tüm bulgu koordinatlarını vermiyor.

Gerberde U2'nin 18 ve U5'in 12 adet 0.20 mm altı maske komşuluğu var.
Toplam 30, rapor sayısıyla uyuşuyor ama her uyarının kimliği doğrulanmış değil.
U5 padlerini küçültme kararı alınmadı: LIS2DW12 paket ölçüleri ve ST TN0018
LGA yönergesine göre mevcut land ölçüleri gerekçeli; montajcı teyidi gerekiyor.

Yeni **0.3.2**, U2'nin maskelerini güncel Skyworks Figure 7 ölçülerine
getiriyor. Bütün bakır padler, yollar, via'lar ve pasta korunuyor.
Yerel/native/Gerber kontrolleri geçti; 268 padin tamamı maske içinde açık.
Değişiklikler ve sınırlar `docs/mask-revision-0.3.2.md` içinde.
**0.3.2'nin JLCDFM sonucu henüz yok; 45, 0.3.1'in sonucudur.**

## Dördüncü rapor ve 0.3.1

00:42:22 raporu 0.3 ZIP'inde yine 0/67 gösteriyordu; kaynak
`evidence/jlc-dfm-20261025-r4`. Ardından üretilen 0.3.1'in değişiklikleri
`docs/mask-revision-0.3.1.md` içinde. Yukarıdaki beşinci rapor bu değişikliğin
gerçek üretici sonucudur; eski ZIP tekrar teslim edilmedi.

## Üçüncü rapor, 0.3 / 35 × 28 mm

2026-10-24 21:45:56 raporunun tamamı görüntülendi. Kaynak PDF ve görüntüler
`evidence/jlc-dfm-20261024-r3` altında. **0 Danger / 67 Warning** var;
önceki rapordaki iki pad-spacing Danger kapandı. Dört katman ve 35 × 28 mm
ölçü doğru. **PCB analizi seçili, SMT analizi seçili değil.** Bu sonuç çalışan
veya dizgiye onaylanmış kart anlamına gelmiyor.

| Kalan kategori | Warning | Rapordaki tek örnek |
|---|---:|---:|
| Pad aralığı | 10 | 0.15 mm |
| Maske köprüsü | 30 | 0.13 mm |
| Maske açıklığı–yakın yol | 3 | 0.15 mm |
| Birden fazla şekilden oluşan maske açıklığı | 2 | Ölçü verilmemiş |
| Negatif maske genişlemesi | 22 | 0.04 mm |

Raporda her bulgunun koordinatı yok. Sayılar 67 ayrı parça veya 67 kesin
elektriksel arıza anlamına gelmez. Önceki 306 Warning'den kalan 57'si maske,
10'u pad aralığı ile ilgili; hepsinin kapandığı söylenemez.

### Gerçek Gerber ve native kaynak incelemesi

- `audit_release_mask.py`, teslim edilmiş ZIP ile aynı açılmış paketin bakır,
  maske ve pasta Gerberlerini okudu. Katman hashleri kaydedildi. Native KiCad
  ile 214 üst + 54 alt bakır pad sayısı eşleşiyor. 0.1 µm karşılaştırma
  toleransıyla **267 padin bakır şekli maske açıklığının içinde**. Yalnız U2.11
  merkez padinin bir kısmı örtülü: bakır 1.45 × 2.802 mm, ayrı açıklık
  1.55 × 2.487 mm. Bu şekil Nordic DK'dan gelen footprint'te mevcut;
  assembly incelemesi bitmediği için otomatik olarak hatalı/doğru ilan edilmedi.
- Dolayısıyla JLC'nin 22 negatif maske uyarısı, basit pad-bakırı/açıklık
  karşılaştırmasıyla 22 küçültülmüş açıklık olarak tekrar üretilemiyor.
  JLC algoritması, yol–pad birleşimleri ve tüm örnek koordinatları bilinmeden
  bunları yanlış alarm saymıyoruz. Mevcut pad getter'ında negatif margin yok;
  F.Cu ve F.Mask parametreleriyle alınan expansion değerleri aynı çıktı.
- Native geometriden U5'te 0.15 mm ve 0201 kondansatörlerde 0.18 mm sabit
  paket aralıkları ölçüldü. Bunlar kartı büyütmekle değişmiyor. U2 maskelerinde
  0.125 / 0.1485 mm, U5 maskelerinde 0.15 mm komşuluklar var. Her birinin
  rapordaki örnekle bire bir eşleştirildiği iddia edilmiyor.
- U2.1 maske açıklığından GNSS_LNA_EN yoluna 0.1517 mm ölçüldü.
  Bu, rapordaki kategori için bir aday; üç bulgunun tamamı eşleştirilmedi.
  Ayrı native ölçüm yalnız pad maskeleri ile farklı net yollarını kapsıyor;
  dolgu bakırı ve üreticinin bütün kontrollerini kapsamaz.
- J1/J2'de iki kasıtlı ortak U.FL maske açıklığı mevcut. İki compound-mask
  uyarısının aday kaynağı bunlar; stencil/montajcı incelemesi gerekiyor.

Kanıtlar: `report-summary.json`, `native-warning-candidates.json`,
`gerber-mask-audit.json`, `pcba-readiness.json`. Gerber okuyucu bu KiCad
çıktısının R/O/C/RoundRect aperture ve doğrusal mask/paste region biçimleriyle
sınırlıdır; desteklemediği biçimde hata verir. Bakır dolgularını pad saymaz;
bu bir tam Gerber DFM motoru değildir.

[JLCPCB kapasite tablosu](https://jlcpcb.com/capabilities/pcb-capabilities),
farklı net SMD padlerinde en az 0.15 mm, maske–yakın yolda 0.09 mm ve 1 oz
yeşil/kırmızı/sarı/mavi/mor maskede 0.10 mm köprü bildiriyor; siyah/beyazda
0.13 mm, 2 oz'da 0.20 mm. Raporun bazı turuncu örnekleri bu sınırlar içinde.
Bu karşılaştırma, seçilmiş stackup/renk/proses veya montajcı onayı değildir.
Paket padlerini sadece gösterge yeşillensin diye küçültmek doğru bir çözüm
olarak kabul edilmedi.

### Montaj hedefi ve açık iş

Kullanıcı elle lehim istemiyor; hedef üreticide dizilmiş, programlanmış ve
test edilmiş çalışan teslim. Mevcut BOM'da 46 takılacak fiziksel parça var;
30'unun kesin MPN'i yok. İki DNP ve beş PCB temas arayüzü ayrıca mevcut.
J6 gerçek eSIM, J5 gerçek nabız sensörü değil; pil/NTC, anten ve harici
bağlantılar da tamamlanmış ürün parçaları olarak seçilmedi.

U1'in maskesi ve pastası tüm padlerde 1:1. [Nordic tasarım kılavuzu](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html)
NSMD ve +0.05 mm maske açıklığı öneriyor; stencil'in montajcıyla belirlenmesini
istiyor. Montajcı girdisi olmadan yapılan stencil için büyük padlerde yaklaşık
%70–80, küçüklerde %75–85 pasta alanı veriyor. Büyük padde %100 pasta
assembly için otomatik kabul edilmedi. Tüm karta körlemesine maske genişleme
uygulamak dar köprüler oluşturabileceğinden yapılmadı.

Bu tur PCB veya teslim edilmiş ZIP değiştirilmedi; yeni Gerber teslimi ya da
üretim onayı yok. Sonraki çalışma sırası: üreticiyle uyumlu footprint/mask/stencil
tanımları; tamamlanmış BOM ve lehimsiz kullanıcı bağlantıları; elektrik/RF
açıklarının kapatılması; firmware/fikstür/test prosedürü; ardından PCB + SMT
incelemesi. Ayrıntı `docs/pcba-delivery.md`.

## Önceki sonuç — ikinci rapor

0.2.1 raporu (2026-10-24 20:41:35) tamamen görüntülendi; kaynak ve dört
görüntü `evidence/jlc-dfm-20261024-r2` altında. Danger toplamı 139 → 2,
Warning toplamı 325 → 306. Maske köprüsü 6 → 0, baskı–pad 98 → 0,
baskı–delik 33 → 0 Danger. **İki pad-aralığı Danger aynı kaldı.**
Maske açıklığının birden fazla şekilden oluşmasına ilişkin 2 yeni Warning var.
Bu nedenle 0.2.1'in tamamen düzeldiği söylenemez.

Kullanıcı kartın fazla küçük olabileceğini belirtti. İlk prototip için
35 × 28 mm (980 mm², mevcut 660 mm²'ye göre +%48.5) önerildi;
40 × 30 mm ve mevcut ölçü seçenekleriyle tercih soruldu, yanıt henüz yok.
Bu ölçü PCB'ye ait; pil, anten ve kutu dahil değil. Büyütme tek başına
paket içi pad/maske kısıtlarını veya elektrik/RF açıklarını çözmez.
Bu aşamada 30 × 22 mm PCB değiştirilmedi ve yeni ZIP yayımlanmadı.

Koordinatsız pad-aralığı örneği, bakır görüntüsünün otomatik eşleştirmesi ve
görsel karşılaştırmayla C6 / SPI_MOSI via çevresine yerleştirildi. Burada
yuvarlatılmış padin gerçek sınırıyla via arasındaki yerel mesafe yaklaşık
0.1046 mm; padin dikdörtgen sınır kutusuyla via arasındaki mesafe 0.0468 mm.
İkincisi rapordaki 0.05 mm örnekle uyuşuyor, fakat JLC'nin algoritması veya
iki bulgunun da kök nedeni henüz kesin olarak doğrulanmadı. Diğer bölgelerde
de sınır kutusu yaklaşımı farklı sonuç veriyor; bu bir hipotez/aday eşleşme,
üreticinin yanlış ölçtüğü veya iki hatanın kapandığı iddiası değil.
Kanıt: `thumbnail-match.json`, `candidate-0.png`, `pad-bbox-via-circle.json`.

## İlk rapor

Kullanıcının sağladığı `DFM analysis report_JLCDFM_collar-tracker-0.2-dfm.zip.pdf`
gerçekten görüntülendi. Tek uzun raster sayfa; rapor zamanı 2026-10-24 20:24:49.
Kart 4 katman, 3 × 2.2 cm; yalnız PCB DFM seçili, SMT DFM seçili değil.
Asıl PDF ve dört okunabilir görüntü `evidence/jlc-dfm-20261024` altında.

Raporda 139 Danger ve 325 Warning işareti listeleniyor; bunlar farklı
kategoriler/katmanlarda sayılan bulgular, 464 bağımsız devre hatası değil.

| Kategori | Danger | Warning | Rapordaki örnek ölçü |
|---|---:|---:|---:|
| Yol genişliği | 0 | 11 | 0.11 mm |
| Pad aralığı | 2 | 45 | 0.05 mm |
| Kaplı delik–yol | 0 | 9 | 0.23 mm |
| Bakır halka | 0 | 100 | 0.12 mm |
| Via–pad | 0 | 1 | 0.12 mm |
| Maske köprüsü | 6 | 30 | 0.01 mm |
| Maske açıklığı–yakın yol | 0 | 74 | 0.10 mm |
| Negatif maske genişlemesi | 0 | 22 | 0.04 mm |
| Baskı–pad | 98 | 0 | 0.09 mm |
| Baskı–delik | 33 | 13 | 0 mm |
| Baskı çizgi kalınlığı | 0 | 20 | 0.12 mm |

KiCad'in ilk 0 hata sonucu bu üretici analiziyle eşdeğer değildi. Örneğin
aynı netin via–pad aralığı normal elektriksel clearance kontrolünde kaçabiliyor;
baskı–tented delik ve dar maske şeritleri için ayrı geometri kontrolü gerekiyor.

## Yapılan düzeltme ve kanıt

- J1/J2 anten konnektörlerinde üçer 0.01 mm maske şeridi gerçek KiCad
  geometrisinden yeniden üretildi. Pad açıklıklarına 0.05 mm genişleme
  verilerek mevcut ortadaki açıklıkla birleştirildi. Bakır olmayan orta alanın
  footprint keepout'u korunuyor. Bu iki konnektörde ortak maske açıklığı
  **bilinçli ve yerel olarak** `AllowSolderMaskBridges` ile tanımlandı;
  global DRC kuralı, severity veya exclusion değiştirilmedi. Bu açıklık
  kararı assembly/stencil incelemesinde de değerlendirilmeli.
- J4 pil temas sırası 0.20 mm aşağı taşındı. BAT pad–via bakır aralığı
  0.025 → 0.225 mm, kart kenarına mesafe 0.50 mm. Via/yol geometrisi,
  pad boyutları ve netler aynı kaldı. İlk via taşıma denemesi DRC'de
  reddedildi; teslim edilen sürüm bu denemeyi **içermiyor**.
- 109 sıkışan parça çerçevesi/yön işareti silk'ten Fab'a taşındı.
  Bağlantı ve kart etiketleri kaldı: 1 mm yazı, 0.15 mm çizgi; dört etiketin
  gerçek glyph poligonlarıyla pad/maske mesafesi en az 0.249 mm,
  delik mesafesi en az 0.311 mm ve kenar payı en az 0.30 mm doğrulandı.
  Assembly bilgisi Fab katmanında; küçük entegrelerin yönü fiziksel silk'te
  artık gösterilmiyor ve montaj çizimi/CPL ile ele alınmalı.
- U2 merkezi pad'in maskesi/pastası zaten ayrı çizimlerle tanımlanıyordu.
  Negatif margin'ler yerine pad yalnız bakıra alındı; ayrı açıklıklar korundu.

`check_dfm_geometry.py` eski kaynakta altı maske şeridini ve yakın BAT viasını
reddediyor, yeni kaynakta geçiriyor. Tüm net/pad boyutları, tüm 797 yol parçası
ve 75 via geometrisi değişmemiş; sadece J4 konumu farklı. Yerel ölçümde
0.10 mm'den dar ayrı pad/via aralığı ve maske şeridi kalmadı. Bu kontrol
JLC'nin bütün algoritmasını uygulamaz; PDF her bulgunun koordinatını vermiyor.
Özellikle PDF'deki iki 0.05 mm pad-aralığı Danger örneğinin bire bir kapanışı
ve diğer uyarıların durumu ancak yeniden JLCDFM çalıştırılarak doğrulanabilir.

Son KiCad DRC: 0 hata, 0 açık bağlantı, 0 şema eşleşme sorunu. 43 warning
yerel düzenlemelerin standart footprint kütüphanesinden farklı olduğunu
belirtiyor; bastırılmadı. Paket DRC özeti ve yerel geometri kanıtını içeriyor.

## Kalan uyarıları nasıl okuyacağız

[JLCPCB'nin güncel kapasitesi](https://jlcpcb.com/capabilities/pcb-capabilities)
1 oz çok katmanlı kartta 0.09 mm yol/aralık, via deliği–yol için 0.20 mm ve
renkli 1 oz maskede 0.10 mm köprü bildiriyor. 0.45/0.20 mm via, yayımlanan
via çapı/delik koşullarını sağlıyor; PTH pad halkasıyla aynı kategori değil.
Bu nedenle rapordaki 0.11 mm yol ve 0.12 mm halka uyarıları tek başına
üretilemezlik kanıtı değil. Tolerans, seçilen bakır/maske/stackup ve assembly
koşulları üreticiyle teyit edilmeli; sırf göstergeyi yeşile çevirmek için
RF padleri veya bütün vialar büyütülmedi.

Üretim onayı hâlâ yok: güç/UVLO/VDD_GPIO, gerçek eSIM ve operatör,
nabız donanımı, anten/RF/stackup, nRF pin-1 footprint farkı, stencil,
alt parçalarla kutu uyumu ve fiziksel test açık.
