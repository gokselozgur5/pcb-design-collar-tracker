# Çalışan ve kullanıcı lehimi gerektirmeyen teslim

2026-10-24 kullanıcı gereksinimi: mümkünse elle lehim işi istemiyor; cihazı
satıcıdan çalışır durumda almak istiyor. Tasarım ve tedarik hedefi budur.
Mevcut 0.3.4 iki ayrı JLC PCB DFM analizinde 0 Danger / 0 Warning aldı;
siparişe hazır ürün değildir. Güncel elektrik/katman/GND ve teslim incelemesi
`docs/order-readiness-0.3.4.md`, DFM düzeltmesi `docs/clearance-revision-0.3.4.md`
içinde. Paul'ün GIMP'teki dönüş-via/iki iç GND yaklaşımı bu kartta tamamlanmadı.

| Teslim koşulu | Mevcut durum | Tamamlanacak iş |
|---|---|---|
| Bütün kart parçaları fabrikada dizilmiş | 46 fiziksel parça, 30 kesin MPN eksik | Kesin BOM, tedarik, CPL ve yön kontrolü; çift taraflı dizgi |
| Pil ve şarj bağlantısı hazır | J3/J4 çıplak PCB temasları; hücre/NTC açık | Uyumlu korumalı hücre ve bağlantı seçimi; üreticide kablo/montaj veya takılabilir bağlantı |
| Gerçek eSIM ile haberleşme | J6 yalnız SIM arayüzü | Parça/profil/operatör seçimi, Türkiye kullanımı ve fabrika testi |
| GNSS/LTE antenleri monte | J1/J2 U.FL; antenler seçilmedi | Anten ve kablo seçimi, RF/beden testi; final montaj sorumluluğu |
| Firmware yüklenmiş | J7 alt yüzde SWD temasları | Lehim gerektirmeyen pogo-pin fikstürü, firmware ve yükleme/doğrulama talimatı |
| Fonksiyon testi geçmiş | Enerjili prototip ve test yazılımı yok | Aşağıdaki kontroller için ölçülmüş sınırlar, üretici uygulanabilirliği ve seri bazlı test kaydı |
| Nabız işlevi | J5 dijital arayüz; sensör seçilmedi | Sensör/temas tasarımı ve referans karşılaştırması; mevcut kart bu işlevi taşımıyor |
| Kutuda kullanıma hazır | Eski maket 30 × 22 mm kart içindi | 35 × 28 mm kart/pil/anten yerleşimi, mekanik montaj ve sızdırmazlık doğrulaması |

**PCB dizgi hizmeti tek başına bütün ürünün kurulup çalıştığı anlamına gelmez.**
Pil, anten ve kutu montajının aynı üretici tarafından yapılıp yapılmayacağı
teyit edilmedi. Başka bir montajcı gerekirse işin kullanıcıya lehim olarak
dönmemesi teslim koşulu olarak korunacak. Fabrikanın kendi montaj yöntemi
ile kullanıcının elle lehim yapması aynı gereksinim değildir.

[JLCPCB programlama hizmeti](https://jlcpcb.com/help/article/pcba-programming-service)
Standard PCBA siparişleri için montajdan sonra programlama sunuyor. Parça
numarası, programlama arayüzü, firmware dosyası ve yöntem gerekiyor;
destek mühendislik incelemesine bağlı. nRF9151/J7 fikstürümüz için henüz
teyit alınmadı. [Fonksiyon testi açıklaması](https://jlcpcb.com/help/article/smt-inspection-and-testing-capabilities)
müşterinin tanımladığı ölçütlerle enerjili test yapıldığını, bu hizmetin
özelleştirilmiş bir seçenek olduğunu belirtiyor. Otomatik olarak siparişe
dahil veya bu tasarım için garanti kabul edilmedi.

## Üretim testinde tanımlanacak kabul ölçütleri

1. Akım sınırlı ilk açılış; besleme gerilimleri, kaçak/uyku akımı ve yük altında
   davranış. UVLO ve VDD_GPIO zamanlaması önce tasarımda çözülüp ölçülecek.
2. SWD programlama, image doğrulama, seri numarası ve açılış kaydı. J7 pinleri
   VIO, SWDIO, GND, SWDCLK, DEBUG_RESET, VSYS; fikstür mekanik erişimi açık.
3. Şarj akımı/sonlandırma, NTC ve pil davranışı; eşikler seçilmiş hücrenin
   şartlarına göre belirlenecek. Şimdiki 100 mA bir taslak değer.
4. İvmeölçer haberleşmesi ve üreticinin self-test'i.
5. SIM/profile okuma, hedef şebekeye veya uygun test sistemine kayıt ve test
   sunucusuna gerçek veri gönderimi. Türkiye profilinin Çin fabrikasında
   çalışacağını varsayma; test erişimi ayrıca çözülecek.
6. GNSS fix ve RF ölçümü için fabrika ortamına uygun anten/sinyal/test yöntemi.
   İçeride rastgele fix denemesi kabul testi sayılmayacak.
7. Seçilmişse nabız sensörü iletişim kontrolü ve ayrıca hayvan üstü ölçüm
   doğrulaması. Fabrikadaki elektronik test, klinik/gerçek temas başarısı değildir.

Sayısal kabul eşikleri ve test fixture'ı henüz hazır değil. İlk prototiplerin
dizgisi ve testi üreticide yapılabilir; ilk tasarımın revizyon gerektirmeyeceği
garanti edilmez. Testten geçmeyen kartların kullanıcıya onarım işi olarak
gönderilmemesi, siparişin somut teslim şartına yazılacak.

Son iki üretici raporu 0.3.4'e ait (2026-10-25 06:39:36 ve 06:41:25):
0 Danger / 0 Warning, yalnız PCB DFM; SMT analizi yok. Aynı ZIP'in kimliği ve
raporlar `release/collar-tracker-0.3.4-verification.json` içinde.
268 padin tamamı maskede açık. U1 stencil, U2'nin JLC prosesine uyarlanmış
maskesi ve U5'in 0.010 mm daraltılmış land'i için montaj doğrulaması gerekiyor.
DFM için dosya yüklemesi yapıldı; sipariş, ödeme veya üreticiye mesaj yapılmadı.
