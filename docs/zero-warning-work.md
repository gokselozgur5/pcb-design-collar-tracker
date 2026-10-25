# Sıfır uyarı çalışması — 2026-10-25

Kankam bütün uyarıları sıfırlamamızı istedi. **PCB DFM işi tamamlandı:**
0.3.4 iki bağımsız JLC yüklemesinde **0 Danger / 0 Warning**, KiCad **0/0/0**.
Raporlar 2026-10-25 06:39:36 ve 06:41:25; SMT seçili değil.
Güncel değişiklik/kanıt/teslim kaydı: `docs/clearance-revision-0.3.4.md`.
Aşağıdaki kütüphane temizliği ve eşik araştırması, fiziksel düzeltmeden önceki
aşamanın kaydıdır; teslim edilen kaynak `35x28-clearance-r034` kopyasıdır.

## Tamamlanan yerel düzeltme

0.3.2'nin fiziksel tasarımını koruyan çalışma kopyası:
`/Users/gok/codex/projects/collar-tracker/experiments/35x28-zero-r033/hardware/collar-tracker.kicad_pcb`

Karttaki özelleştirilmiş footprint'ler eski standart kütüphane kimliklerini
taşıyordu. 53 parçanın mevcut tanımı `Collar033.pretty` proje kütüphanesine
kaydedildi; PCB ve şemadaki footprint bağlantıları bu açık tanımlara çevrildi.
`library-provenance.json`, her parçanın önceki kimliğini ve dosya hashini tutuyor.
Bu işlem geometrinin montaj için onaylandığı anlamına gelmez.

- Önce: 0 hata / 47 kütüphane farkı uyarısı / 0 açık / 0 şema uyuşmazlığı.
- Sonra: **0 hata / 0 uyarı / 0 açık / 0 şema uyuşmazlığı**.
- `--severity-all --schematic-parity --all-track-errors` kullanıldı.
- Proje ve özel DRC kural dosyaları bire bir aynı; kontrol kapatılmadı,
  severity değiştirilmedi, exclusion eklenmedi.
- Şemada yalnız footprint kimlikleri değişti. Native pad/maske/yol/via/dolgu/
  baskı geometrileri aynı. **11 Gerber katmanının tamamı**, yalnız üretim
  zaman damgası çıkarıldığında yayımlanmış 0.3.2 ile bire bir aynı.
- Kaynak SHA256: `345544f51eec67767cb7154620392a062bba0ac8ea19051c3e0de5a2beee255b`.

Kanıtlar `experiments/35x28-zero-r033/evidence/library-cleanup-checks.json`,
`library-drc.json`, `geometry.json`, `gerbers/`. Tekrar üretim araçları
`scripts/persist_trial_footprints.py`, `dfm_geometry.py` ve
`verify_library_cleanup033.py`.

Bu kopya henüz 0.3.3 Gerber sürümü olarak yayımlanmadı. Fiziksel çıktı
değişmediğinden mevcut 0.3.2 ZIP, JLC karşılaştırması için doğru girdidir.
Kütüphane temizliğinin JLC uyarılarını değiştirdiği iddia edilmiyor.

## JLC'nin gerçek varsayılan eşikleri

[JLCDFM'nin herkese açık örneği](https://jlcdfm.com/viewer?pcbUploadFileId=637065032774410242&demo=1)
yeni, anonim bir tarayıcı bağlamında incelendi. Kankamın Gerber'i yüklenmedi.
Kural paneli açıldı; Apply/Save/Set as default kullanılmadı.
Örneğin indirdiği sistem yapılandırması ve ekran görüntüleri
`evidence/zero-warning-r033` altında korunuyor.

| Kontrol | Yapılandırmadaki değerler, mil | Uyarı/yeşil sınırı |
|---|---|---|
| Pad aralığı | 4, 6, 8 | 6 mil = 0.1524 mm |
| Maske köprüsü | 4, 6, 8 | 6 mil = 0.1524 mm |
| Maskenin yakındaki yola mesafesi | 3, 6, 8 | 6 mil = 0.1524 mm |
| Negatif maske açıklığı | Sayısal eşik yok, warning-value | Geometri bulgusu |

Arayüzde yuvarlanmış 0.15 mm değerinin hem turuncu hem yeşil görünmesinin
nedeni bu hassasiyettir. Önceki 0.20 mm taraması uyarı eşiğinin doğrudan
kopyası değildi. Bu sistem profili kankamın analizine ait profil ayrıca
okunmadan onun kesin yapılandırması olarak kabul edilmiyor.

Gerçek maskeler bu 0.1524 mm eşiğiyle sayıldığında 0.3.1'de 30, 0.3.2'de
26 ayrı maske komşuluğu eşik altında. Bu, yerel geometrik sayımdır;
**0.3.2 için alınmış JLC sonucu değildir**. Dolayısıyla sıfır JLC uyarısı
beklentisiyle yeni ZIP teslim edilmedi ve rapor kuralları gevşetilmedi.

İki negatif maske ve üç maske/yol bulgusunun tüm gerçek koordinatları PDF'de
yok. Aynı net yollarının pad sınır kutusunda maske dışına taşması aday taraması
sonuç vermedi; iki uyarının sebebi olarak sunulmuyor. ST'nin MKI179V1 resmî
Gerber bağlantısı bulundu, fakat indirme HTTP/2 hatası ve zaman aşımıyla
başarısız; bu referans kartın land ölçülerini inceledik iddiası yok.

## Sonuç ve erişim düzeltmesi

JLC analizi, kullanıcının “sıfırla” isteğinin gerekli adımı olarak yeniden
değerlendirildi; önceki ek onay engeli kaldırıldı. Yalnız Gerber/delik dosyaları
hazırlandı. Anonim yükleme giriş istedi; kullanıcı açılan ayrı tarayıcıda
giriş yapıp “login oldum tekrar dene” dedi. Şifre/cookie/token okunmadı veya
dışarı aktarılmadı; normal tarayıcı oturumu kullanıldı.

0.3.2 ve düzeltilen 0.3.3 yüklenip analiz edildi: **40 → 0 Warning**.
Ham sonuçlar, değişmeyen kural dosyası, tam PDF ve ekran görüntüleri saklandı.
Gerçek koordinatlar önceki U1.71 görsel eşleşmesini düzeltti: U1.30.
Negatif maskeler FB1'in iki padindeydi. Yerel 26 maske köprüsü sayımı
gerçek 0.3.2 sonucuyla aynı çıktı. Sipariş veya üretici mesajı gönderilmedi.
Tam çalışan, kullanıcı lehimi gerektirmeyen PCBA için elektrik/RF/BOM/
firmware/test ve yeni footprint/maske süreç kalifikasyonu işleri açık.

## 0.3.3 tekrar kontrolü ve 0.3.4

Kankam bir turuncu gösterdi; teslim edilen aynı 0.3.3 ZIP'i tekrar yükleyince
0/1 yeniden üretildi. İlk 0/0 raporu tek anlık sonuçtu; yeterli kabul kanıtı
değildi. Raw koordinatlar U1.71'i gösterdi; U1.30 ayrı bir simetrik bağlantı.
0.3.4 bu ikinci GND yolunu da 0.30 mm yapıyor. Yeni ZIP iki farklı JLC
kaydında aynı kurallarla 0/0 verdi; ikinci yükleme son teslim yolundan yapıldı.
Sonuçların önce neden farklılaştığı henüz belirlenmedi.
