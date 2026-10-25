# 0.3.4 sipariş öncesi inceleme — 2026-10-25

**Mevcut kart, fabrikadan dizilmiş ve çalışır cihaz olarak siparişe hazır değil.**
İki JLC PCB DFM raporu 0 Danger / 0 Warning; SMT, elektriksel çalışma ve RF
kabulü yapılmış değil. Paul'ün GIMP incelemesinden çıkan GND düzeni bu karta
tam olarak taşınmamış.

İncelenen kaynak:
`/Users/gok/codex/projects/collar-tracker/experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pcb`

- PCB SHA256: `597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2`
- Gerber ZIP SHA256: `735ff8506629eb931cdd4a1847796e0eae2ec24deebb4f579f7441bb2182c990`
- Kart ve teslim ZIP'i bu incelemede değiştirilmedi.
- Tekrarlanabilir ölçümler: [audit.py](../evidence/order-readiness-20261025-r034/audit.py)
  ve [audit.json](../evidence/order-readiness-20261025-r034/audit.json).

## Katmanlar ve bağlantılar

35 × 28 × 0.8 mm kartın dört bakır katmanı var.

| Katman | Mevcut bakır |
|---|---|
| F.Cu | 446 yol segmenti + GND dolgusu |
| In1.Cu | GND düzlemi; çizilmiş sinyal/güç yolu yok |
| In2.Cu | 116 sinyal/güç segmenti + GND dolgusu |
| B.Cu | 230 yol segmenti + GND dolgusu |

Dolayısıyla üst/alt iletkenler var; iki iç katmanı tamamen GND olan
`sinyal / GND / GND / sinyal` düzeni henüz yok.

Şemada GND tanımlı 78 pad var. Yeni DRC'de açık bağlantı ve şema uyuşmazlığı
yok. U1 nRF9151'in 30 GND pin numarası, [Nordic'in GND listesiyle](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gnd.html)
eşleşiyor. Diğer bütün bileşenlerin pin işlevleri bu tur üretici belgeleriyle
baştan karşılaştırılmadı. Bütün netler GND olmamalı; sinyal ve besleme netleri
şemadaki ayrı bağlantılarını koruyor.

77 via'nın 16'sı GND. Bu 16 via'nın merkezi, dört katmanın da kaydedilmiş
GND dolgusunun içinde. Bu ölçüm ve açık bağlantı kontrolü bağlantının varlığını
destekler; dönüş akımının kısa/düşük empedanslı olduğu veya termal/RF yeterliliği
sonucunu vermez.

## Paul'ün önceki notlarına göre durum

Kaynaklar: GIMP arşivindeki `CHANGES_v0.1.4.md` (ikinci Paul incelemesi),
`CHANGES_v0.1.2.md` (iki iç GND katmanı), mevcut GIMP `tools/return_vias.py`
ve `docs/REVIEW_v0.1.6.md`. Bunlar önceki projede saklanmış inceleme ve uygulama
kayıtlarıdır; Paul'ün bu tasma kartını incelediği iddia edilmiyor.

| Önceki inceleme noktası | Bu kartta doğrulanan durum |
|---|---|
| GND padlerinden kısa bağlantıyla düzleme geç; gereksiz GND yollarını kaldır | 206 GND yol segmenti, toplam 151.485 mm ve 16 GND via var. Tümü gereksiz diye sınıflandırılmadı; yerel pad dönüşleri ve uzun bağlantılar ayrıca ele alınmalı. GIMP'teki düzenin tamamlandığı söylenemez. |
| Sinyal katman geçişlerinin yakınına GND dönüş via'sı | Eski GIMP uygulamasının 2 mm taramasında 61 GND dışı via'nın 9'u içeride, **52'si dışarıda**; en uzak 7.0902 mm (`I2C_SDA`, x127.0031/y105.2826). |
| İki iç GND referansı | In1 ayrılmış; In2'de 116 sinyal/güç segmenti var. İkinci kesintisiz GND düzlemi sağlanmamış. |
| İki padli parçaların lehim/ısıl dengesi | Dört GND dolgusunun bağlantı modu solid. 77 GND pad bunu devralıyor, bir pad ayrıca solid seçilmiş. Bu otomatik bir kusur değildir; pad başına bakır dengesi ve dizgi prosesi incelenmedi. |
| Güç yolları yeterince geniş/kısa olsun | VDD_NRF 0.25 mm; VIN_5V/VBAT/VSYS 0.20–0.25 mm; VIO_1V8 0.20 mm. Akım/gerilim düşümü/ısınma yeterliliği ölçülmedi. GIMP'in 0.4 mm değerini bu karta gerekçesiz aktarmak da doğrulama olmaz. |

2 mm, GIMP'te kullandığımız geometrik tarama eşiğidir; Paul'ün evrensel bir
sayısal şartı veya RF/EMC standardı olarak sunulmaz. 52 uzak via, 52 kanıtlanmış
işlevsel arıza demek değildir. Ancak önceki dönüş-via kontrolünün bu kartta
tamamlanmadığını somut olarak gösterir. Mesafeler merkezler arası düz çizgidir;
gerçek dönüş akımının güzergâhı çözülmedi.

[Nordic stack-up yönergesi](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/pcb_stack_up.html?contentId=hAMpO_HZkUUtvaGq7NCRUw)
sinyal katmanının yanında dönüş akımı için ayrılmış GND referansı, RF yollarında
empedans kontrolü ve sürekli referans ister. Mevcut alt katmanın In2 üzerindeki
yollardan nasıl etkilendiği ayrıca incelenmeli. Bu bir kaynak temelli inceleme
gereksinimidir; ölçülmüş RF kaybı iddiası değil.

## Siparişten önce açık işler

- **Güç ve RF:** GND dönüşleri/katman düzeni, gerçek üretici stack-up'ıyla 50 Ω
  yollar, antenler ve beden/kutu etkisi; güç yolu düşümleri, hücre/NTC/koruma,
  düşük gerilimde kapatma ve VDD_GPIO sıralaması. Nordic'in önerdiği 6 ms
  gecikme veya erken GPIO durumlarına tolerans gösterildiği doğrulanmadı;
  [üretici açıklaması](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/vdd_gpio.html).
- **İşlev:** J6 yalnız SIM temasları; gerçek eSIM, profil ve Türkiye operatörü
  seçilmedi. J5 dijital genişleme portu; nabız sensörü yok.
- **Dizgi:** BOM'da 53 kayıt; 46 takılacak fiziksel parça, iki DNP ve beş temas
  arayüzü var. 30 fiziksel parçanın kesin MPN'si eksik. 32 parça üstte, 14 altta;
  çift taraflı dizgi gerekiyor. CPL/orientasyon, U1 stencil ve özelleştirilmiş
  U2/U5 land/maske prosesi onaylanmadı.
- **Çalışır teslim:** Pil/anten bağlantıları, lehimsiz SWD fikstürü, firmware,
  fabrika test yöntemi ve 35 × 28 mm karta uygun kutu henüz tamamlanmadı.

Önce bu seçimler ve şema/güç açıkları tamamlanmalı; ardından ground/RF odaklı
yerleşim ve rota revizyonu, yeni DRC/ERC/DFM/SMT ve dizgili prototip doğrulaması
gelmeli. Yeni katman/yerleşim gereksinimleri görülmeden 35 × 28 mm'nin son ölçü
olduğu veya büyütülmesi gerektiği söylenemez.

## Kontrol kapsamı

Yeni KiCad 10.0.7 DRC: 0 ihlal / 0 açık / 0 parity; ERC: 0 ihlal.
Varsayılan devre dışı kontroller raporlarda açıkça duruyor (DRC beş, ERC dört);
kural, severity ve exclusion değiştirilmedi. [DRC](../evidence/order-readiness-20261025-r034/drc.json),
[ERC](../evidence/order-readiness-20261025-r034/erc.json).
Bu tur yeniden JLC yüklemesi, sipariş, ödeme, üretici mesajı veya enerjili test
yapılmadı. İki JLC sonucu önceki aynı ZIP'e bağlı raporlardır.
