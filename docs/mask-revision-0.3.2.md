# 0.3.2 — U2 üretici maske ölçüleri — 2026-10-25

0.3.1'in gerçek JLCDFM sonucu 0 Danger / 45 Warning: önceki 67'den 22 uyarı
kapanmış. Negatif maske 22 → 2, çok parçalı maske 2 → 0. Pad aralığı 10,
maske köprüsü 30, maske–yol 3 değişmedi. Kaynak PDF ve beş görüntü
`evidence/jlc-dfm-20261025-r5` içinde. SMT analizi seçili değil.

Yeni 0.3.2'nin üretici sonucu henüz yok. 45 uyarının kapanışı veya üretim
onayı iddia edilmiyor. Kartı büyütmeyi gerektiren yeni bir yerleşim bulgusu yok.

## Gerekçeli değişiklik

[SKY65943-11, Skyworks 204404H](https://www.skyworksinc.com/-/media/C1965FC4C165469FAEED1BA276874AF1.pdf),
2025-09-04, Figure 7 / sayfa 9 indirildi ve çizim görüntüsü incelendi.
Yerel kopya `references/dfm-r5/SKY65943-11-204404H.pdf`.

| U2 maske açıklığı | 0.3.1 | 0.3.2 |
|---|---|---|
| Merkez, pad 11 | 1.55 × 2.487 mm | 1.55 × 2.90 mm |
| Dört büyük dış pad: 1, 5, 6, 10 | 0.525 × 0.615 mm, r=0.05 köşeler | 0.525 × 0.515 mm, dikdörtgen |
| Altı küçük dış pad | 0.525 × 0.375 mm | Aynı |

Üretici merkez açıklığı için çizilen alanın %60–100'üne izin veriyor;
bu aday tam ölçüyü seçiyor. Önceki kısmi örtü bu nedenle tek başına kanıtlanmış
bir montaj hatası olarak nitelendirilmedi. Dört dış maskenin Y ölçüsü Figure 7'ye
getirildi. Bakır pad küçültülmedi, pasta artırılmadı. Merkez açıklığına
0.64015 mm² eklenirken dış açıklıklardan toplam 0.2014145 mm² çıkarıldı.
Alt baskının sürüm yazısı `COLLAR 0.3.2 TEST` oldu.

## Doğrulama

- KiCad DRC: 0 hata, 0 açık bağlantı, 0 şema uyuşmazlığı; 47 kütüphane
  footprint farkı uyarısı korunuyor. Kurallar/severity/exclusion değişmedi.
- 53 footprint, 792 yol, 77 adet 0.60/0.20 mm via; 35 × 28 × 0.8 mm ve
  dört bakır katmanı. In1 GND olarak ayrılmış durumda.
- Native karşılaştırma bütün bakır pad şekilleri/konumları, yollar, via'lar
  ve dolgu ayarlarının aynı kaldığını doğruluyor. Pad kimliği kullanılıyor;
  aynı pin numaralı U.FL GND padleri birbirine karıştırılmıyor.
- Gerberde dört bakır, iki pasta, alt maske ve dış hat dosyaları, yalnız
  tarih/sürüm üstverisi çıkarıldığında öncekiyle bire bir aynı. Diğer
  parçaların üst maske geometrileri aynı. Üst baskı boş; maske çıkartma
  komutları değişse de yeni mürekkep şekli yok. Alt baskıda yalnız sürüm değişti.
- **214 üst + 54 alt = 268 padin tamamı maske açıklığının içinde**.
  Önceki 267/268 sonucundaki U2.11 kısmi örtü artık yok. Bu, JLC algoritmasının
  bütün negatif-maske kriterlerini veya iki uyarının kapanışını kanıtlamaz.
- Ayrı maske köprüsü minimum 0.125 mm; 0.10 mm altında yok.
  Değişen açıklıklardan farklı-net pad/yol/via'ya minimum 0.1735 mm.
  Bu son ölçüm aynı-net dolgu/boğaz geometrisini kapsamaz.
- Üst/alt görseller incelendi. Gerber dış hattı, 77 delik, ZIP CRC ve tüm
  paket hashleri doğrulandı. Eski kaynaklar ve teslim ZIP'leri korunuyor.

Kontrol geliştirilirken duplicate pin-number eşleştirmesi kimlik tabanına
çevrildi; boş üst baskının negatif maske komutları ve eski maskenin yuvarlak
köşeleri karşılaştırmaya doğru şekilde katıldı. İlk üretimde iki poligon
köşesinde FromMM truncation kaynaklı 1 nm eksiklik, koordinatları yuvarlayarak
düzeltildi; son kaynak ve Gerber kontrolleri bu son sürümde geçti.

## Kalan rapor bulgularının sınırı

0.08 mm maske–yol örneği bakır eşleştirmesi (0.920) ve görsel karşılaştırmayla
U1.71 GND padinin GND dolgusuna bağlandığı boğazda bulunuyor. İki farklı net
arasında 0.08 mm açıklık gösterilmedi. Ancak üreticinin ölçüm kuralı ve diğer
iki örnek bilinmediği için kategori kapatılmadı; bu bölge değiştirilmedi.
İki negatif maske uyarısı güvenilir biçimde konumlandırılamadı. Yeni U2
değişikliğinin bunları kapatıp kapatmadığını sonraki üretici raporu gösterecek.

0.3.1 maskelerinde U2 için 18, U5 için 12 adet 0.20 mm altı komşuluk ölçüldü.
Bu 30 sayısı raporla uyumlu fakat bulgu kimlikleri yok. U5'in padlerini sadece
rapor yeşillensin diye küçültmedik: [LIS2DW12 paket çizimi](https://www.st.com.cn/resource/en/datasheet/lis2dw12.pdf)
ve [ST TN0018 LGA yönergesi](https://www.st.com/resource/en/technical_note/cd00134799.pdf)
mevcut 0.375 × 0.35 mm land için dayanak sağlıyor; proses değerlendirmesi sürüyor.
JLC'nin sınırlarıyla karşılaştırma, siparişe özel fab/montaj onayı değildir.

U1 maske/stencil, kesin BOM, güç/UVLO/VDD_GPIO, pil/NTC/ESD, RF/stackup/anten,
gerçek eSIM/operatör, firmware/fikstür/test ve kutu işleri açık. Kullanıcı
lehimi gerektirmeyen çalışan fabrika teslimi hedefi korunuyor. Bu revizyon
bir DFM deneme paketidir; çalışan ürün veya siparişe hazır PCBA değildir.

## Teslim ve tekrar üretim

ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.2-35x28-dfm.zip`

SHA256: `c09893e5c211a3e98fdaba4b1ae3fafa7e17e737543e1a02530f64e386254d04`

Kaynak: `/Users/gok/codex/projects/collar-tracker/experiments/35x28-mask-r032/hardware/collar-tracker.kicad_pcb`

PCB SHA256: `4dbc5ce1fe08628c8239f155c70aed1a46200ec83cbfd1dc0b765716c79e0b18`

139838 bayt, 20 dosya. Kanıtlar `experiments/35x28-mask-r032/evidence` altında.
Sıra: `revise_mask_032.py` (KiCad Python; mevcut deneyin üstüne yazmayı reddeder),
`dfm_geometry.py`, `check_size_trial.py --mask-revision-032` (.venv-dfm),
`export_mask_revision032.py`, `audit_release_mask.py`, `verify_mask_revision032.py`.
Exporter mevcut ZIP'i değiştirmez. Yeni değişiklikler ayrı revizyon gerektirir.
Sipariş, dış yükleme, üreticiye mesaj veya fiziksel test yapılmadı.
