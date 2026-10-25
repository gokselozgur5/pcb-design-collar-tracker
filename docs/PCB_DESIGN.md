# PCB Design

PCB işlerini de yazılım gibi gereksinim, kaynak, küçük değişiklikler, test ve
doğrulanmış teslim üzerinden yürüteceğiz. Bu rehber sonraki kartlarda da kullanılacak.

Bu dosya çalışma yöntemidir. Güncel kartın durumu [STATUS](STATUS.md), kararları
[decisions](decisions.md), Paul'ün bu karta uygulanması [paul-nanosim](paul-nanosim.md)
içindedir. Bir projedeki ölçü veya test sonucu başka karta otomatik taşınmaz.

## Yazılımdaki karşılığı

| Yazılım | PCB tarafındaki karşılığı |
|---|---|
| Gereksinimler ve kabul kriterleri | Kullanım, ölçü, güç, arayüz, çevre, üretim ve test hedefleri |
| Mimari ve API sözleşmeleri | Blok şema, güç ağacı, pinler, voltajlar, zamanlama ve konektörler |
| Kaynak kod | Şema, native PCB, proje kuralları, footprint/symbol kütüphaneleri |
| Bağımlılık kilidi | CAD sürümü, kesin MPN, datasheet revizyonu, kütüphane commit'i, stackup |
| Build | Netlist, Gerber, delik, BOM, CPL, stencil ve mekanik çıktılar |
| Statik analiz | ERC, DRC, şema–PCB parity ve geometri kontrolleri |
| Birim/regresyon testi | Pin eşleşmesi, footprint ölçüsü, ağ bağlantısı ve önce/sonra hata örnekleri |
| Entegrasyon testi | Gerçek üretici DFM, montaj incelemesi ve fiziksel kart ölçümleri |
| Release | Kaynağa hash ile bağlı, kontrol edilmiş üretim paketi |
| Production smoke test | İlk açılış, programlama, güç/radyo/sensör ve uçtan uca fonksiyon testi |

**ERC/DRC temizliği, kartın çalıştığını kanıtlamaz. PCB DFM temizliği de montajın
ve fonksiyonların doğrulandığı anlamına gelmez.** Her sonucu kendi kapsamıyla yaz.

## 1. Önce ne yapacağımızı sabitle

Başlangıçta aşağıdakileri gereksinim tablosuna yaz. Bilinmeyeni varsayım olarak
işaretle; sessizce kesin karara çevirme.

- Kullanım: hangi işi, hangi koşullarda, hangi sıklıkla yapacak?
- Ülke/operatör/servis: bağlantı teknolojisi ve kullanılacak hizmet gerçekten uyumlu mu?
- Mekanik: kart, pil, anten, kutu, bağlantı aparatı, kablo ve erişim alanları.
- Güç: besleme aralığı, tepe/ortalama akım, çalışma modları, şarj ve hedef süre.
- Arayüzler: voltaj seviyesi, pin eşleşmesi, zamanlama, boot/reset/debug.
- Üretim: adet, bütçe, katman/kalınlık, dizgi yöntemi, elde lehim gereksinimi.
- Teslim: boş PCB mi, dizilmiş kart mı, programlanmış ve test edilmiş cihaz mı?
- Ölçülebilir kabul: neyi hangi ölçüm veya testle tamam sayacağız?

Pil kapasitesi ve kart ölçüsünü tahminle kilitleme. Gerçek bileşen, anten ve
mekanik hacmi birlikte yerleştir; sığma ve çalışma süresini ayrı doğrula.

## 2. Mimari ve parça seçimi

Blok şema ve güç ağacı çiz. Her blok için giriş/çıkış, güç alanı ve hata durumunu yaz.
Besleme düşmesi, reset, takıp çıkarma ve kapalı cihazın bir arayüzden beslenmesi
gibi durumları devre incelemesine dahil et.

Her fiziksel parçada kesin MPN, üretici, paket, pinout ve üretici belgesi bulunmalı.
Dağıtıcı stok kodu MPN'nin yerine geçmez; uygunluk ve bulunabilirlik tarihli kanıttır.
Benzer isimli parçaların marka, paket veya pinlerinin aynı olduğunu varsayma.

Üreticinin datasheet/reference design belgelerini önce oku. Kaynak URL, revizyon,
indirme tarihi ve SHA-256 kaydet. Kütüphane sembolü veya bir AI açıklaması tek başına
üretici pinout'una kanıt değildir.

## 3. Şema ve footprint

- Şemada güç alanlarını, net adlarını, NC pinlerini, pull-up/down ve debug yollarını açık tut.
- Pin numarası → üretici işlevi → şemadaki net → PCB pad'i zincirini kontrol et.
- ERC çalıştır; kapalı kontrolleri ve gerekçeli istisnaları ayrıca kaydet.
- Netlist üzerinden kritik bağlantıları bağımsız kontrol et. Üretim scriptinin aynı
  yanlış tabloyu tekrar okuması bağımsız doğrulama değildir.
- Footprint'i gerçek paket çizimiyle karşılaştır: pin 1, üst/alt görünüm, pad aralığı,
  boyutlar, exposed pad, peg/delik, mask, paste, courtyard ve mekanik keepout.
- Kartın altına çevrilen parçanın pinleri ve CPL yönü için ayrıca kontrol yap.
- Tek pad numarası birden fazla fiziksel pad'de bulunabilir; UUID veya pad indeksi kullan.
- Projeye özel footprint'i yerel kütüphanede sürümle. Native kart ile kütüphane
  arasındaki farkları çöz; uyarıyı gizleyerek geçme.

Konektörün lehim padleri sığıyor diye kullanılabilir sayma. Kart takma/çıkarma,
kablo bükülme, kilit açma ve alet erişimi için de yer bırak.

## 4. Üretim kısıtları ve katman yapısı

Gerçek üreticinin seçilen süreç/katman/kalınlık için geçerli sınırlarını al.
Minimum yol, bakır açıklığı, delik, annular ring, mask köprüsü, kart kenarı ve
silkscreen değerlerini proje kurallarına işle. Kapasite tablosunu tarihli sakla.

Üretici minimumu hedef tasarım marjı olmak zorunda değil. Mümkün olduğunda pay bırak.
Sabit paket pad aralığı için istisna gerekiyorsa yalnız ilgili geometriye uygula;
aynı istisna bütün yol/via açıklıklarını düşürmemeli.

Katman sayısı ve stackup sinyallerin, akımların ve RF ihtiyacının sonucudur.
Bu projedeki dört katman/iki iç GND seçimi bütün kartlar için kural değildir.
Kontrollü empedans gerekiyorsa gerçek dielektrik kalınlığı/malzeme/bakır ve üretici
stackup'ı üzerinden hesapla; yalnız yol genişliğine bakıp “50 ohm” deme.

## 5. Yerleşim ve yönlendirme

Önce mekanik sınırlar, konektör/anten erişimi ve kritik güç/RF blokları; sonra diğer
parçalar. Decoupling ve hassas geri besleme döngülerini üretici yerleşimine göre çöz.
Kritik bağlantıları gözle incelemeden otomatik yönlendiriciye bırakma.

### GND ve dönüş yolları

- GND olması gereken pinleri GND'ye bağla. Bütün pinleri GND'ye bağlamak diye bir hedef yok.
- “GND net adı var”, “açık bağlantı yok” ve “iyi dönüş yolu var” farklı sonuçlardır.
- Referans düzlemini gereksiz yarıklarla bölme. Sinyalin dönüş yolunu katman geçişinde
  ve düzlem kesintilerinde takip et.
- GND pad'lerini mümkün olduğunca kısa yerel bağlantılarla düzleme indir.
  Ayrı küçük pasifleri uzun bir GND hattı üzerinde zincirleme.
- Komşu IC GND pinleri uygun kısa bağlantıyı paylaşabilir; bunun gerçek geometrisini kaydet.
- Dönüş via'sını ilgili sinyal/güç geçişinin yakınına yerleştir. Mesafe hedefini
  sinyal ve stackup'a göre değerlendir; eski bir sayıyı evrensel standart yapma.
- Sadece via sayısını değil, gerçekten doğru dolguya bağlanıp bağlanmadığını ölç.
  Yetim bakır adalarını ve doldurulmuş katmanları kontrol et.

### Güç, termal ve RF

- Tepe akım, izin verilen düşüm, bakır kalınlığı ve sıcaklık üzerinden güç yolu seç.
- Kısa pad çıkışı ile uzun güç hattını ayrı ölç. Netclass genişliği verilmiş olması,
  bütün gerçek yolların o genişlikte olduğunu göstermez.
- Güç sıralaması, UVLO, şarj sınırları, NTC/koruma ve transient durumlarını incele.
- Küçük pasifin iki pad'ine bağlanan bakırı karşılaştır. Bir tarafta büyük düzlem,
  diğer tarafta ince boyun varsa lehim/termal dengesini değerlendir.
- RF geometrisini üretici referansı ve gerçek stackup ile kontrol et. Anten keepout'u,
  kutu, pil ve kullanıcı/beden yakınlığı ayrıca ölçüm gerektirebilir.
- ESD parçası eklemek tek başına yeterli değildir; konektör–koruma–IC sırası ve
  korumanın GND yolu yerleşim incelemesinin parçasıdır.

### Otomatik yönlendirici

Kullanılan CAD/router sürümünü ve ayarlarını sabitle. Native kaynak yerine kopyayı
dışa aktar; router için kullanılan genişletilmiş pad veya keepout üretim geometrisi değildir.
GND düzlemle bağlanacaksa router'ın uzun GND yolları üretmesini önle.

İçe aktardıktan sonra parça konumları, pad/net eşleşmesi, katmanlar, kilitli kritik
yollar, GND bağlantıları, via çap/delikleri ve minimum genişlikleri tekrar kontrol et.
Router'ın “tamamlandı” mesajı native DRC'nin yerine geçmez.

## 6. Doğrulama: tam olarak ne geçti?

| Kontrol | Gerekli kanıt | Kanıtlamadığı şey |
|---|---|---|
| ERC | Doğru şema/revizyon için rapor, varsayılan kapalı kontroller | Fiziksel çalışma |
| DRC + parity | Doğru PCB/proje için ihlaller, açıklar, şema eşleşmesi | RF/EMC, güç kararlılığı |
| GND incelemesi | Pin/net, gerçek dolgu, kısa bağlantı ve dönüş yolu ölçümü | Laboratuvar EMC sonucu |
| Geometri regresyonu | Eski sorunlu örnekte başarısız, düzeltilmiş örnekte başarılı kontrol | Üreticinin tüm algoritmaları |
| Gerber incelemesi | Dışa aktarılan gerçek katman/pad/delik/ölçü karşılaştırması | Montaj doğruluğu |
| Üretici PCB DFM | Yüklenen ZIP hash'i, kayıt kimliği, kurallar, tamamlanmış sonuç, PDF | SMT ve fonksiyon testi |
| PCBA incelemesi | BOM/CPL/parça/yön/stencil/factory preview eşleşmesi | Firmware ve ürün davranışı |
| Fiziksel kabul | Ölçüm koşulları, kart revizyonu, firmware ve gerçek test sonucu | Henüz denenmemiş ortamlar |

KiCad komutlarını kurulu sürümün `--help` çıktısıyla kontrol et. DRC'de ilgili tüm
şiddetleri, bütün yol hatalarını ve şema parity'sini dahil et. Bölge dolgusunu güncel
tut; yayımlanmış dosyaya yanlışlıkla `--save-board` uygulama.
[KiCad 10 CLI belgesi](https://docs.kicad.org/10.0/en/cli/cli.html).

Bir uyarıyı önce gerçek koordinat/geometri ve net ile eşleştir. Benzer iki konumun
aynı hata olduğunu varsayma. Birini düzeltince simetrik diğerini de kontrol et.
Kuralı gevşeterek veya üretici land'ini keyfî küçülterek yeşil sonuç üretme.

Bu çalışma biçiminde son ZIP için **iki yeni, aynı baytlara ait DFM koşusu** alıyoruz.
Bu bizim tekrar doğrulama kuralımızdır; üreticinin evrensel zorunluluğu değildir.
Analizin bittiğini, bütün satırların değerlendirildiğini ve kuralların değişmediğini
görmeden sonucu kabul etme. Web sayfasının açılması analiz sonucu değildir.

## 7. Dizgi, programlama ve çalışan teslim

BOM'da kesin parça, değer/tolerans, paket, refdes ve DNP ayrımı bulunmalı.
CPL'de refdes, yüz, koordinat, birim, orijin ve dönüş açısını üretici önizlemesiyle
eşleştir. DNP'ler ve yalnız temas/test padleri takılacak parça gibi gönderilmemeli.
[JLCPCB BOM gereksinimleri](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly).

Gerçek stok, ikame, alt yüz dizgisi, stencil ve özel montaj işlemleri seçilen sipariş
için teyit edilmeli. Datasheet'te bir parçanın varlığı, fabrikada o parçanın hazır
olduğu anlamına gelmez.

Programlanmış teslim isteniyorsa firmware imajı/hash'i, debug/pogo erişimi,
programlama adımları, seri numarası/kimlik ve test fixture'ı tanımlanmalı.
Kabul testi girişleri, ölçüm sınırları ve başarısız kartın davranışı açık olmalı.

İlk açılışta kısa devre/direnç, polarite, akım sınırlı güç, raylar, reset/debug,
firmware, ardından radyo/sensör ve uçtan uca işlevler sırayla kontrol edilir.
Pil/şarj ve koruma testleri gerçek seçilen hücrenin sınırlarına göre yapılır.
Ölçülmemiş sağlık/sensör başarısını ürün özelliği olarak doğrulanmış gösterme.

## 8. Git, script ve release düzeni

```text
AGENTS.md / CLAUDE.md    Yeni oturumun giriş kuralları
docs/STATUS.md          Güncel revizyon, doğrulananlar, açıklar, kesin sonraki adım
docs/decisions.md       Kararlar, varsayımlar ve dayanakları
docs/WORKLOG.md         Tamamlanan anlamlı adımların kısa kaydı
hardware/              Native kaynak ve yerel kütüphaneler
scripts/               Tekrarlanabilir üretim, kontrol ve dışa aktarma
experiments/<rev>/     Ayrı deneme kaynakları ve kanıtları
references/            Üretici kaynakları, revizyonlar ve hash manifesti
evidence/              Seçilmiş raporlar, ölçümler ve önce/sonra kanıtı
release/               Kaynağa bağlı, değiştirilmeyen teslim paketleri
mechanical/            Kutu, bağlantı ve gerçek parça hacimleri
```

Her repoda gerçek güncel kaynak yolunu STATUS'ta açıkça yaz. `hardware/` isimli
klasörün her zaman en yeni sürüm olduğunu varsayma.

- Ayrı Git deposu kullan; yanlışlıkla üst klasörün deposuna dosya ekleme.
- Bir anlamlı değişiklik = bir commit. Şema/footprint/gerekli PCB değişikliğini
  tutarlı tut; bağımsız düzeltmeleri ayır. Tamamlanmamış işi WIP olarak işaretle.
- Kaynak ve eski release'i koru. Yeni denemeyi ayrı dizinde üret; mevcut bitmiş
  kartı sessizce yeniden oluşturan script çalıştırma.
- Bileşen konumları, pad şekilleri/netleri, kurallar ve kritik yolları semantik
  olarak karşılaştır. Büyük KiCad metin diff'i tek başına inceleme değildir.
- Yeni release; kaynak SHA, araç sürümü, çıktı listesi, ZIP SHA, yerel test ve
  üretici kayıtlarını birbirine bağlayan manifest taşımalı.
- Gerber/delik/mask/paste çıktısını gerçekten aç. Katman sayısı, outline, delikler,
  pad açıklıkları, kart kenarı ve iki yüzün yönünü kontrol et.
- Üreticiye uygun dosyaları gönder. Tarayıcı profili, token, cookie, ham oturum
  kaydı, venv, özel notlar veya ilgisiz dosyalar Git'e/üretim ZIP'ine girmez.
- Son çıktıyı temiz checkout'ta kontrol et. Güçlü bir regresyon kontrolü, yanlış
  kaynak veya değişmiş çıktı verildiğinde başarısız olmalıdır.

## “Bitti” deme ölçütü

Hangi aşamanın bittiğini söyle: şema, yerleşim, yerel kontrol, PCB DFM, PCBA veya
çalışan ürün. Tamamlanması istenen aşamanın her kabul kriterinin kanıtını açıp kontrol et.
Başka revizyonun yeşil sonucu veya rapor başlığı yeterli değildir.

Göksel'e kısa sonuç, kalan gerçek eksik ve teslim dosyasının tam yolunu ver.
Yerel dosya için `open -R "/tam/yol/dosya.zip"` gibi çalıştırılabilir komut kullan.
Yeni oturumun aynı işi tekrar araştırmaması için STATUS'u güncelle; ne yapacağını
ve nerede kaldığını bir sonraki asistana bırak.

## Yeni PCB başlangıç şablonu

```text
Amaç / kullanım:
Kesin gereksinimler:
Açık kararlar / varsayımlar:
Kart + pil + anten + kutu sınırı:
Güç ağacı / tepe ve ortalama akım:
Kritik arayüzler / üretici referansları:
Üretici + süreç + stackup + tasarım marjları:
Güncel native kaynak / revizyon:
Kabul kriteri → kontrol → kanıt dosyası:
Üretim tesliminin kapsamı:
İlk yapılacak somut adım:
```

## Bu karttan kalıcı dersler

- Paul'ün GIMP review'ünü hatırlamak, collar kartına uygulamış olmak değildir.
  Her yeni kartı gerçek kaynak üzerinden yeniden incele.
- İki bakır dolgu görünmesi iki kesintisiz GND referansı olduğunu göstermez.
  Katmanlardaki gerçek yolları ve kaydedilmiş dolguları kontrol et.
- 0.3.3'te aynı ZIP için farklı zamanlarda 0/0 ve 0/1 gözlendi. Son baytları yeniden
  doğrula; ilk sonucu evrensel garantiye çevirme.
- Mask uyarısında benzer iki GND boynu vardı. Koordinatları tek tek eşleştirmek gerekir.
- KiCad 10 SWIG'de koleksiyonu gezerken `Remove` kullanımı sorun çıkardı. Öğeleri
  önce listele; silinecek in-memory öğelerde `Delete` kullan. Native DRC ile sonucu ölç.
- SIM'in fiziksel biçimi modem teknolojisini değiştirmez. Nano-SIM, LTE-M/NB-IoT
  operatör uyumunu veya 1.8 V UICC gereksinimini ortadan kaldırmaz.

Yeni kartlarda çıkan genellenebilir dersleri buraya ekle. Güncel işler ve sonuçlar
bu rehbere günlük gibi birikmez; STATUS ve WORKLOG'da kalır.
