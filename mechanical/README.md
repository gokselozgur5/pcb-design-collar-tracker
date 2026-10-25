# İlk mekanik hacim çalışması

Bu model PCB, pil, kutu ve anten alanlarını birlikte değerlendirmek için hazırlandı.
Yerleştirilmiş/routing yapılmış gerçek PCB veya üretime hazır kutu değildir.

| Senaryo | Ana gövde | Temas çıkıntısıyla yükseklik | Pil ölçü örneği |
|---|---|---|---|
| `compact_250` | 38 × 30 × 14 mm | 14.6 mm | 250 mAh; 32 × 20.5 × 5.3 mm |
| `reference_500` | 44 × 36 × 14 mm | 14.6 mm | 500 mAh; 36 × 29 × 4.75 mm |

Tasma bağlantısı dahil değil. 250 mAh seçilmiş kapasite değildir; pil ömrü
hesaplanmadı/ölçülmedi. Kullanıcının şarj aralığı tercihi henüz açık.

## Modelde ne var?

- Sarı: üretici/satıcı ölçülerinden pil örneği. Koruma, NTC, kablo çıkışı,
  şişme ve montaj payları onaylı bir paket çizimine göre doğrulanmadı.
- Yeşil: 30 × 22 × 0.8 mm PCB hacmi; gerçek parça yerleşimi yok.
- Koyu gri: nRF9151 paket ölçüsü 12.1 × 11.1 × 1.2 mm.
- Diğer gri bloklar: güç, eSIM, sensör, pasif ve bağlantılar için toplu hacim
  bütçesi; gerçek footprint'ler tek tek yerleştirilmedi.
- Turuncu: LTE/GNSS için istenen hacimler. Anten seçimi, ground plane,
  RF boşlukları, eşleme ve beden etkisi doğrulanmadı. Gerçek antenler daha
  fazla yer veya farklı yerleşim gerektirebilir.
- Pembe: varsayımsal nabız başlığı ve 0.6 mm temas çıkıntısı. Sensör,
  optik/elektrot düzeni ve hayvanla temas yöntemi seçilmedi.
- Açık gri: 1.2 mm duvar/kapak hacmi. Vida, klips, conta, şarj temasları ve
  sızdırmazlık tasarımı henüz yok; su dayanımı iddiası yok.

## Açma ve boyut denemesi

`packing-study.scad` OpenSCAD ile açılır. `variant` iki senaryo arasında;
`view_mode` ise `exploded`, `section`, `assembled`, `mockup` arasında değiştirilir.

`compact-250-sizing-dummy.stl` ve `reference-500-sizing-dummy.stl` **içi dolu
boyut maketleridir**. Ölçek 1:1, birim mm; dilimleyicide otomatik ölçekleme
kullanma. Bu dosyalar elektronik yerleştirilecek kutu değildir. CAD hacmi pil
ve devre ağırlığını temsil etmediğinden maket ağırlığı ürün ağırlığı değildir.

`../previews/compact-250-review.svg` bağımsız, ölçülü inceleme sayfasıdır;
PNG/PDF sürümleri de vardır. Görsel ekranda veya kağıtta 1:1 değildir.

## Kontroller

`../scripts/check_packing.py`, modelde belirtilen dikdörtgen hacimleri
yuvarlatılmış iç duvara, taban/kapak sınırlarına ve birbirine karşı kontrol eder.
500 mAh örnek pilin küçük gövdeden reddedildiği kontrol de var. Sonuç
`packing-checks.json` içinde. Script OpenSCAD katılarını okumaz; iki dosyadaki
ölçüler birlikte güncellenmeli. Hacim kontrolü RF veya üretilebilirlik kanıtı değil.

STL dış sınırları ayrıca gerçek dışa aktarılan üçgenlerden ölçüldü:
`stl-bounds.json`. Her iki katı maket dış ölçüleriyle uyumlu.

Proje kökünden yeniden üretim (OpenSCAD 2021.01):

```sh
python3 scripts/check_packing.py
openscad -o mechanical/compact-250-sizing-dummy.stl --export-format binstl -D 'view_mode="mockup"' mechanical/packing-study.scad
openscad -o mechanical/reference-500-sizing-dummy.stl --export-format binstl -D 'view_mode="mockup"' -D 'variant="reference_500"' mechanical/packing-study.scad
openscad -o previews/compact-250-exploded.png --imgsize 1400,1100 --projection o --viewall --autocenter --camera 0,0,0,65,0,35,140 --colorscheme Tomorrow -D 'view_mode="exploded"' mechanical/packing-study.scad
python3 scripts/make_packing_sheet.py
rsvg-convert -o previews/compact-250-review.png previews/compact-250-review.svg
rsvg-convert -f pdf -o previews/compact-250-review.pdf previews/compact-250-review.svg
```

Kaynaklar: [EEMB hücre](https://www.eemb.com/product-130),
[EEMB paket örneği](https://eemb.store/products/lp502030),
[Adafruit 500 mAh örneği](https://www.adafruit.com/product/1578),
[Nordic paket ölçüsü](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/physical_characteristics.html).
