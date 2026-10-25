# Tasarım kararları — 2026-10-24

## Mevcut yön

| Konu | Durum |
|---|---|
| Türkiye | Kullanıcı kararı |
| Ortak küçük/hafif gövde | Kullanıcı hedefi; en küçük köpekte ağırlık ve bağlantı doğrulaması gerekli |
| eSIM | Kullanıcı gereksinimi; sağlayıcı/profil ve fiziksel parça açık |
| nRF9151 | Taslak aday; LTE-M aboneliği ve kullanım bölgeleri doğrulanacak |
| Nabız | Kullanıcı talebi; fiziksel ölçüm yöntemi ve sensör henüz seçilmedi |
| Pil, kutu ve kart ölçüsü | Açık; bir şarjla kullanım süresi belirlenmedi |

Kullanıcı 500 mAh'ın gerekli olup olmadığını ve kutuyu da tasarlayıp
tasarlayamayacağımızı sordu; Apple Watch Ultra örneğiyle daha küçük gövde
hedefini vurguladı. 500 mAh sabit gereksinim değil. Önceki boyut tahmini alt
sınır olarak kullanılmayacak. PCB dış hattı, pil, anten, nabız teması ve kutu
birlikte ele alınıyor. İlk OpenSCAD hacim çalışması üretildi; fiziksel kutu yok.
Şarj aralığı sorusu açık; kullanıcı bir kapasite veya gün hedefi seçmedi.

## İlk 3D hacim çalışması

`mechanical/packing-study.scad` iki parametrik senaryo içeriyor:

| Senaryo | Gövde | Örnek pil | PCB için ayrılan hacim |
|---|---|---|---|
| Küçük gövde | 38 × 30 × 14 mm | 250 mAh; 32 × 20.5 × 5.3 mm | 30 × 22 × 0.8 mm |
| 500 mAh karşılaştırması | 44 × 36 × 14 mm | 36 × 29 × 4.75 mm | 30 × 22 × 0.8 mm |

İkisinde de varsayımsal temas çıkıntısı 0.6 mm; tasma bağlantısı dahil değil.
Bu ölçüler asistanın araştırma hedefi, kullanıcıca seçilmiş ürün ölçüsü değil.
[EEMB üretici sayfası](https://www.eemb.com/product-130) 250 mAh hücreyi 31 mm,
[satış sayfası](https://eemb.store/products/lp502030) paketi 32 mm uzunlukta
listeliyor; modelde büyük değer kullanıldı. Her iki pil de yalnız ölçü örneği;
deşarj darbesi, koruma, NTC, kablo çıkışı ve şişme payı ayrıca doğrulanacak.

Belirtilen hacimler yuvarlatılmış iç duvar, taban ve kapak sınırları içinde;
birbirleriyle hacimsel çakışma yok. Bu kontrol gerçek BOM yerleşimi/routing
veya çalışan ürün kanıtı değildir. Özellikle turuncu LTE/GNSS blokları seçilmiş
anten değildir; yer ve boşluk gereksinimleri gövdeyi büyütebilir. Nabız başlığı
varsayım, ölçüm yöntemi açık. Conta, bağlantı, şarj temasları, montaj ve dayanım
henüz tasarlanmadı. Kanıt ve yeniden üretim: `mechanical/README.md`.

## Apple Watch Ultra'dan incelenebilenler

İlk nesil Ultra'nın [iFixit söküm yazısı](https://www.ifixit.com/News/65598/apple-watch-ultra-is-beautiful-rugged-and-repairability-is-just-within-reach)
ve iki iç yerleşim fotoğrafı incelendi. Fotoğraflarda cihaza göre biçimlenmiş pil,
SiP ve esnek şerit bağlantılar görülüyor. iFixit antenlerin ekran/gövde ile
bütünleştirildiğini bildiriyor. [Söküm videosunda](https://www.youtube.com/watch?v=b4-lT12eSQs)
Creative Electron röntgenleri bulunuyor; video/röntgen üzerinden kapsamlı PCB
analizi henüz yapılmadı. Fotoğraf kaynakları/hash'leri
`references/apple-watch-ultra/manifest.json` içinde; görseller iFixit'e ait.

[Apple mekanik çizimi](https://developer.apple.com/download/files/accessories/dimensional-drawings/apple-watch-ultra.pdf)
dış ölçü ve sensör/şarj çevresindeki boş bırakılacak alanları gösterir. Bu araştırmada
Apple tarafından yayımlanmış tam Ultra devre şeması, Gerber veya düzenlenebilir
PCB kaynak paketi bulunmadı; bu, internette hiçbir dosya olmadığı iddiası değil.

Bizim tasarım için çıkarım: pil, kart dış hattı, anten ve kutu aynı yerleşim
çalışmasında ele alınmalı. Fotoğraflar bağlantı şemasını, katmanları veya RF
tasarımını yeniden üretmek için yeterli değil. Elektriksel/RF dayanağı olarak
[Nordic nRF9151 DK donanım paketi](https://docs.nordicsemi.com/r/bundle/ug_nrf9151_dk/page/ug/nrf91_dk/intro/kit_content.html)
şema, PCB, BOM ve Gerber içeriyor; bu tur paketin kendisi indirilip incelenmedi.
Geliştirme kartının dış boyutu ürünümüzün küçüklük sınırı değildir.

## Ön boyut tahmini — yerleşim doğrulaması değil

Kullanıcının boyut sorusu için asistanın çalışma tahmini:

- Elektronik PCB: yaklaşık 30–35 × 25–30 mm. Antenler için ayrı gövde alanı
  bulunabildiği varsayımı; yerleşim yapılmadığından sığma doğrulanmadı.
- 500 mAh sınıfı pil, anten alanı ve kutuyla ana GPS/eSIM gövdesi:
  yaklaşık 45–50 × 35–40 × 14–18 mm (uzunluk × genişlik × kalınlık).
- Nabız sensörünün temas başlığı/elektrotları ve tasma bağlantı aparatı bu
  zarfa dahil değil. Seçilecek antenin RF gereksinimi tahmini büyütebilir.
- Bu ölçüler kullanıcı kararı, sabit tasarım sınırı veya üretim çizimi değildir.
  500 mAh pil seçimi yapılmadı; pil ömrü sonucu çıkarılmadı.

Boyut dayanakları: [Nordic nRF9151](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/physical_characteristics.html)
12.1 × 11.1 × 1.2 mm; [Adafruit 500 mAh örnek pil](https://www.adafruit.com/product/1578)
36 × 29 × 4.75 mm. Bu pil yalnız mekanik örnektir; darbe akımı, NTC ve
diğer elektriksel gereksinimler için seçilmiş/onaylanmış parça değildir.
PCB/pil üst üste yerleşimi, izolasyon, kablo, montaj ve kutu payları varsayıldı;
RF performansı veya gerçek mekanik montaj bu hesapla doğrulanmış olmaz.

## Şemada kullanılan çalışma varsayımları

- nRF9151 uygulama işlemcisi, GPS ve LTE-M/NB-IoT işlevlerini taşır.
- GPIO ve dijital sensörler için 1.8 V alanı; eSIM için modem tarafından üretilen
  ayrı SIM_1V8 alanı. Bu iki besleme birbirine bağlanmaz.
- Tek hücreli 4.2 V Li-ion/LiPo adaydır. Hücre koruması ve hücreye temas eden NTC
  gerekir. Kapasite ve izin verilen akımlar henüz seçilmedi.
- BQ25185 şarj/power-path ve TPS7A02 1.8 V regülatör ilk şema adaylarıdır.
  Şarj akımı 100 mA çalışma varsayımıdır; hücre seçimine göre yeniden hesaplanır.
- GPS girişinde SKY65943-11 filtre/LNA adayı. 1.8 V ile çalıştırılarak LNA enable
  seviyesinin GPIO alanıyla uyumu korunur.
- LIS2DW12 hareket sensörü adayı. İvmeden doğrudan nabız üretildiği iddia edilmez.
- Harici nabız sensörü denemeleri için dijital bağlantı ayrılır; hayvanla temas eden
  elektrot/optik başlık ana karttan ayrı değerlendirilir.

## Yerleşimden önce kapanacak konular

1. Türkiye'de operatör, LTE-M kapsaması/aktivasyonu, eSIM profil teslimi.
2. Hücre kapasitesi, deşarj darbesi, şarj akımı, NTC ve koruma özellikleri.
3. VDD her koşulda en az 3.0 V; düşük pilde donanımsal kapatma ve tekrar açılma
   eşikleri. Hücrenin kendi koruma eşiği tek başına bu koşulu garanti etmez.
4. VDD/ENABLE/VDD_GPIO sıralaması. Nordic en az 6 ms gecikme önerir; erken GPIO
   darbelerine tolerans ancak açık inceleme ve ölçümle kabul edilebilir.
5. eSIM parça kodu, 1.8 V uyumu, footprint ve profil sağlayıcısı. Şemadaki genel
   bağlantı somut bir eSIM sipariş kodu değildir.
6. GNSS ve LTE antenleri, kutu/beden etkisi, RF matching ve üretici stack-up'ı.
   Sadece 50 ohm net sınıfı yazmak fiziksel empedansı doğrulamaz.
7. Nabız sensörünün temas şekli, mekanik rahatlığı ve referans ölçüm karşılaştırması.
8. OTA güncelleme bölümlendirmesi; gerekirse harici flash footprint'i.

## Ana üretici kaynakları

- [nRF9151 pinout](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/pinout.html)
- [Önerilen devre ve pasifler](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/schematic_design.html)
- [VDD](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/vdd.html)
- [VDD_GPIO](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/vdd_gpio.html)
- [GNSS](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gps_if.html)
- [UICC](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/uicc_if.html)
- [BQ25185](https://www.ti.com/product/BQ25185)
- [TPS7A02](https://www.ti.com/product/TPS7A02)
- [LIS2DW12](https://www.st.com/en/mems-and-sensors/lis2dw12.html)

Nordic web belgeleri tarayıcı kaynağından okundu; doğrudan indirmeleri 403 verdi.
İndirilemeyen belgeler manifestte başarılı gibi işaretlenmedi.
