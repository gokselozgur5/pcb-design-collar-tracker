# İlk şema kontrolü — 2026-10-24

Bu belge şema taslağının kontrol kapsamını kaydeder. Üretim onayı değildir.

## Geçen kontroller

- KiCad 10.0.7 şemayı açtı, PDF ve XML netlist dışa aktarımı tamamlandı.
- Varsayılan ERC profilinde 0 hata / 0 uyarı / 0 hariç tutulan ihlal.
  Projede kural bastırması yapılmadı. KiCad varsayılanında kapalı dört kontrol:
  tek global etiket, dört yollu birleşim, SPICE modeli, footprint filtresi.
  Bunlar `evidence/erc.json` içinde `ignored_checks` alanında korunuyor.
- Gerçek KiCad XML çıktısında 18 bağlantı/bütünlük kontrolü geçti.
  113 nRF pini, 30 GND, 27 ayrı bırakılan reserved pin, SIM besleme ayrımı,
  reset/DEC0, RF port ayrımı, LNA köprüsü, şarj ayarları, hareket sensörü ve
  nabız deneme kartı arayüzü bu kapsamda.
- nRF aday footprint'inde 1–113 numaralarının her biri bir kez bulunuyor.
  Bu sadece pin kapsamı kontrolüdür; pad koordinatlarını doğrulamaz.
- PDF görsel olarak incelendi; beş bölüm ve açık tasarım notları sayfaya sığıyor.
  A2 çizim, ekranda yakınlaştırılarak okunmalı.

İlk ERC turundaki çizim ızgarası ve kütüphane tanımları düzeltildi. Güç kaynağı
etiketleri dış 5 V / GND kaynağını ve ferrit sonrası besleme sürekliliğini tarif
eder; eksik düşük voltaj kesmesini veya açılış sıralamasını doğrulamış saymaz.

## Açık olanlar

| Konu | Durum |
|---|---|
| PCB yerleşimi, yollar, katmanlar, DRC | Yeni çalışma `docs/pcb-dfm.md` ve ayrı PCB DRC raporlarında |
| eSIM, şarj, pil, nabız ve debug bağlantılarının fiziksel parçaları | Temas/lehim padleri var; gerçek eSIM ve nabız modülü seçilmedi |
| U2 / U3 / U5 footprint'leri | DFM taslağında atandı |
| nRF footprint geometrisi ve lehim pastası | Üçüncü taraf aday; üretici çizimiyle doğrulanacak |
| Düşük pilde donanımsal kapatma | Henüz tasarlanmadı |
| VDD_GPIO açılış/kapanış sıralaması | Henüz çözülmedi |
| Giriş/ESD koruması, pil ve NTC değerleri | Parça ve hücreye göre tamamlanacak |
| RF, anten, kutu ve beden etkisi | Ölçülmedi |
| Türkiye LTE-M/eSIM operatör uyumu | Hesap/profil/kullanım bölgesi için doğrulanmadı |
| Nabız sensörü ve temas mekanizması | Seçilmedi; yalnız dijital deneme arayüzü var |

Şarj 100 mA / 4.2 V ve giriş limiti 500 mA taslak değerlerdir; seçilecek hücre
için onaylanmış sayılmaz. Pil ömrü, toplam ağırlık, kart ölçüsü ve maliyet ölçülmedi.

## Tekrar çalıştırma

Proje kökünde, GOKSSD bağlı ve yerel KiCad mevcutken:

```sh
scripts/kicad-cli sch erc --format json --severity-all --exit-code-violations \
  --output evidence/erc.json hardware/collar-tracker.kicad_sch
scripts/kicad-cli sch export netlist --format kicadxml \
  --output evidence/collar-tracker.xml hardware/collar-tracker.kicad_sch
/usr/bin/python3 scripts/verify_draft.py
scripts/kicad-cli sch export pdf \
  --output previews/collar-tracker-schematic.pdf hardware/collar-tracker.kicad_sch
```

Kontrol ayrıntıları ve dosya SHA-256'ları `evidence/connectivity-checks.json` içinde.
Donanım veya devre simülasyonu çalıştırılmadı. Bu rapor şema kontrolüyle sınırlıdır;
PCB/Gerber çalışması `docs/pcb-dfm.md` ve paket manifestinde ayrıca tutulur.
