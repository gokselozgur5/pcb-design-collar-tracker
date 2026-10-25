# Collar tracker

Türkiye için küçük, hafif, hücresel bağlantılı GPS takip cihazı.
Tek elektronik gövdeyi farklı tasmalara takabilmek hedefleniyor. Farklı boy ve
tüy yapısındaki köpeklerde mekanik uyumluluk henüz test edilmedi.

**Aktif iş:** Paul'ün yerleşim notlarını uygulamak, gerçek nano-SIM yuvası eklemek
ve yeni revizyonu JLC DFM'de sıfır hata/uyarıya getirmek. eSIM şimdilik ertelendi.

Yeni revizyon henüz yönlendirilmedi. **0.3.4'ün yeşil sonucu yeni karta ait değil.**
Kesin durum ve ilk yapılacak iş: [STATUS](docs/STATUS.md).

## Yeni oturumda devam

Bu klasörü Claude Code'da açıp **“kaldığım yerden devam et”** yaz.
`CLAUDE.md`, proje talimatlarını ve güncel durumu yükler.

Mevcut Mac'te doğrudan başlatmak için:

```sh
cd /Users/gok/codex/projects/collar-tracker
claude
```

Bağlamı ve kayıtlı kanıtları elle kontrol etmek için:

```sh
python3 scripts/resume.py
```

[Devam komutları](docs/RESUME.md) · [Paul / nano-SIM notları](docs/paul-nanosim.md)
· [Çalışma kaydı](docs/WORKLOG.md)

Private repo: [gokselozgur5/collar-tracker](https://github.com/gokselozgur5/collar-tracker).

## Kullanıcının belirlediği kapsam

- İlk ülke Türkiye; operatör henüz seçilmedi.
- Küçük PCB, mümkün olduğunca yazılımla eklenen özellikler; cihazda AI hesabı yok.
- Küçük ve büyük köpekler için ortak donanım hedefi.
- Nabız ölçümü isteniyor; ölçüm yöntemi henüz doğrulanmadı.

## Bu taslağın sınırı

`hardware/` altında nRF9151 adayına dayanan, incelenebilir ilk KiCad şeması hazır.
Operatörün LTE-M/NB-IoT hizmeti doğrulanmadan modem seçimi kesinleşmiş sayılmaz.
Şema taslağı, bileşenlerin elektriksel ilişkilerini gözden geçirmek içindir.
Üretime hazır PCB, doğrulanmış RF tasarımı veya nabız ölçebilen prototip değildir.
Güncel **0.3.4 / 35 × 28 mm / dört katman** denemesi, JLC'nin iki bağımsız
2026-10-25 06:39:36 ve 06:41:25 raporunda **0 Danger / 0 Warning** aldı. KiCad'de de
0 hata, 0 uyarı, 0 açık bağlantı ve 0 şema uyuşmazlığı var. Kurallar değişmedi.
[Gerber/Excellon ZIP](release/collar-tracker-0.3.4-35x28-dfm.zip),
[JLC raporu](release/collar-tracker-0.3.4-jlc-dfm-report.pdf) ve
[değişiklikler / montaj sınırları](docs/clearance-revision-0.3.4.md).
53 footprint, 792 yol kesimi, 77 adet 0.60/0.20 mm via. In1.Cu GND
referansı; In2.Cu üzerinde sinyal/güç yolları var. **SMT doğrulanmadı.**

[Sipariş öncesi inceleme](docs/order-readiness-0.3.4.md): 78 GND padinde açık
bağlantı yok; ancak eski GIMP'in 2 mm dönüş-via taramasında 61 GND dışı via'nın
52'si eşiğin dışında. İkinci iç katman sinyal de taşıyor. Güç/RF, eSIM, BOM ve
çalışır teslim eksikleri nedeniyle **henüz siparişe hazır değil**.

Son doğrulanmış denemenin native kaynağı `experiments/35x28-clearance-r034/hardware/` içinde.
Yeni çalışma `experiments/paul-nanosim-r04/hardware/` altında; şema/footprint taslağı var,
PCB üretimindeki hata henüz çözülmedi.
`hardware/` altındaki 30 × 22 mm 0.2.1 kaynak ve önceki ZIP'ler referans olarak
korundu. O sürümün gerçek ikinci JLCDFM raporunda 2 Danger / 306 Warning var;
bu sayılar yeni karta ait değil. Önceki rapor/düzeltme ayrıntıları
`docs/jlc-dfm-review.md`, devre/RF sınırları `docs/pcb-dfm.md` içinde.

İlk parametrik 3D hacim çalışması 30 × 22 mm PCB'yi kullanıyor; yeni 35 × 28 mm
kartla tekrar doğrulanmadı. 250 mAh örnek pille 38 × 30 × 14 mm
gövde hedefi; varsayımsal temas çıkıntısıyla toplam yükseklik 14.6 mm. Antenler,
nabız başlığı ve diğer devrelerin büyük bölümü ayrılmış hacimlerdir; gerçek
parçaların ve RF tasarımının bu gövdeye sığdığı henüz doğrulanmadı.

Pil kapasitesi, şarj aralığı, konum güncelleme sıklığı, kutu ve antenler henüz
seçilmedi. Kart ölçüsü bu bilgilerden sonra sabitlenecek. Önceki maliyet
aralıkları üretim teklifi değildi; nabız donanımını içermiyordu.

## Dosyalar

- `experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pro`: güncel 35 × 28 mm deneme projesi.
- `experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pcb`: yerel ve JLC PCB DFM kontrolleri geçen kaynak.
- `scripts/finalize_clearance034.py`: kaynak/yerel test/JLC raporu/ZIP bağlarını doğrular; test edilen baytları teslim eder.
- `hardware/collar-tracker.kicad_pro`: KiCad projesi.
- `hardware/collar-tracker.kicad_pcb`: native KiCad PCB.
- `scripts/build_pcb.py`: gerçek XML netlistten PCB üretimi.
- `scripts/import_route.py`: yerel Freerouting SES içe aktarımı ve dolgu.
- `scripts/export_dfm.py`: DRC kontrolüyle Gerber/Excellon ZIP üretimi.
- `previews/collar-tracker-schematic.pdf`: açıp yakınlaştırılabilen şema önizlemesi.
- `hardware/collar-tracker.kicad_sch`: beş bölümlü tek A2 şema.
- `hardware/bom.csv`: taslak parça listesi; açık seçimler ayrıca belirtilir.
- `docs/decisions.md`: mevcut varsayımlar ve açık tasarım kararları.
- `docs/heart-rate.md`: köpeklerde nabız ölçümü için araştırma ve doğrulama kapsamı.
- `previews/compact-250-review.png`: ölçülü 3D yerleşim özeti.
- `mechanical/packing-study.scad`: düzenlenebilir OpenSCAD hacim çalışması.
- `mechanical/compact-250-sizing-dummy.stl`: yalnız boyut denemesi için katı maket.
- `mechanical/README.md`: mekanik varsayımlar, kontroller ve dosyaların kullanımı.
- `references/manifest.json`: indirilen üretici belgelerinin kaynakları ve SHA-256 değerleri.
- `evidence/`: CAD kontrolleri ve pin bağlantısı incelemesi.

## Kontrol sonucu

KiCad 10.0.7 varsayılan ERC profilinde sıfır ihlal; dışarı aktarılan gerçek netlist
üzerinde 18 bağlantı/bütünlük kontrolü geçti. ERC'nin varsayılan olarak kapalı
dört kontrolü raporda açıkça listeleniyor. Bu sonuç RF, güç sıralaması, pil veya
nabız ölçümünün doğrulandığı anlamına gelmez. Ayrıntı: `docs/verification.md`.

## Araçlar

KiCad 10.0.7 çalışma alanında, GOKSSD üzerinde tutuluyor. Sistem uygulama klasörü
değiştirilmedi. `scripts/kicad-cli` proje için yerel komut satırı girişidir.

Şemayı yeniden üretmek için `scripts/build_draft.py`, doğrulamak için
`scripts/verify_draft.py` kullanılır. Yeniden üretim mevcut şema dosyasının üzerine
yazar; elle KiCad düzenlemesi yaptıktan sonra bu komutu çalıştırma. Üretici
footprint kopyasının kaynağı, commit'i ve lisansı `hardware/NORDIC_LIBRARY_NOTICE.txt`
içindedir. Scriptin tekrar üretimi için bu kaynağın `references/nordic-lib-kicad`
altında bulunması gerekir; hazır KiCad şeması bağımsız açılabilir.
