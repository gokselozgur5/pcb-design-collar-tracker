# Nabız ölçümü — araştırma durumu

İstenen özellik nabız ölçümüdür. Bunun bütün boylarda, tüy yapılarında ve hareket
durumlarında çalıştığı henüz gösterilmedi. İşlemci üzerinde AI çalıştırmadan
filtreleme ve tepe aralığı hesabı yapılabilir; önce fiziksel sinyal elde edilmelidir.

## İncelenen kanıt

Kasım 2024'te çevrimiçi yayımlanıp Şubat 2025 sayısında çıkan 12 sağlıklı köpek
çalışmasının özetinde, akıllı tasmanın
24 saatlik ortalama kalp hızı ile Holter arasında yakınlık bulunurken iki dakikalık
ölçümlerde uyum zayıftır. Olası kayıt süresinin %43'ünde tasma kalp hızı verisi
üretmemiştir. Bu sonuç her tasmanın aynı olduğunu veya önerdiğimiz sensörün
çalışacağını göstermez. Çalışmanın burada incelenen kısmı özettir.

[Assessment of heart rate measurements obtained from a smart collar compared to
24-h Holter monitoring in healthy dogs](https://pubmed.ncbi.nlm.nih.gov/39675258/)

2019 mekanokardiyografi çalışması da göğüs üzerine yerleştirilen telefonla,
hareketsiz ölçümün uygulanabilirliğini inceliyor. Tüy, kayma ve sinyal kalitesi
sınırlamaları bildiriliyor. Bu sonuç boyun tasmasının çalıştığının kanıtı değil;
ilk deneyde dinlenme hâlini ve ölçüm kalitesini öne almak için gerekçe.

[Cardiac monitoring of dogs via smartphone mechanocardiography](https://pmc.ncbi.nlm.nih.gov/articles/PMC6480821/)

## Aday yöntemler

| Yöntem | Mekanik gereksinim | Açık konu |
|---|---|---|
| Optik PPG | LED ve fotodiyot, kontrollü cilt teması ve ışık izolasyonu | Tüy, hareket ve temas basıncı |
| ECG | Ayrı cilt temas noktaları, elektrot geometrisi ve analog giriş koruması | Tasma konumunda sinyal, kürk ve hareket |
| Mekanik/akustik | Kalpten gelen çok küçük hareket/sesleri ileten temas | Yürüme ve solunumdan kalp sinyalinin ayrılması |

MAX86176 yaklaşık 2.73 × 2.71 mm bir PPG+ECG analog ön uç adayıdır. Kendi başına
tam nabız sensörü değildir: optik yöntemde LED/fotodiyot ve optik mekanik tasarım,
ECG'de elektrotlar ve uygun giriş devresi gerekir. Üreticinin insan giyilebilir
cihazlarına ilişkin özellikleri köpeklerde doğruluk kanıtı sayılmaz. Tam doküman
erişimi için üretici NDA süreci gösteriyor; bu nedenle şu an parça seçilmedi.

[Analog Devices MAX86176](https://www.analog.com/en/products/MAX86176.html)

## İlk prototipte yapılacaklar

Ana kartta I2C/SPI, interrupt, reset ve besleme bağlantısını bir sensör deneme
kartına çıkar. Elektrotları genel dijital konektöre doğrudan bağlama; analog
koruma ve sensör devresi deneme kartında ayrı tasarlanır.

Önce masaüstünde sinyal yolu ve güç doğrulaması; ardından uygun referans ECG ile,
dinlenme ve hareket ayrı raporlanarak değerlendirme gerekir. Sadece ortalama
hata değil, ölçüm alınabilen süre ve hatalı sonuçların dağılımı da raporlanır.
Farklı boy ve tüy yapıları test kapsamına alınır. Yetersiz sinyalde değer
gösterilmez; aktiviteden tahmin edilen sayı gerçek nabız diye sunulmaz.
