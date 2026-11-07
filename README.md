# Tenis Veri Toplama ve Video Analiz Sistemi
### Tennis Data Collection & Video Analytics Tool

<p align="center">
  <img src="assets/logo.png" alt="Logo" width="120" />
</p>

Tenis müsabakaları ve antrenman kayıtları üzerinden yüksek doğrulukla **veri toplama**, **kort bölgelendirme**, **vuruş analizi** ve **oyuncu performans takibi** gerçekleştirmek üzere geliştirilmiş profesyonel bir masaüstü analiz yazılımıdır. 

Uygulama; C# (.NET Framework / WinForms) kullanıcı arayüzü ile Python (OpenCV, PyQt5, Homografi & Geometri Hesaplama) analiz motorunu hibrit ve yüksek performanslı bir mimaride bir araya getirir.

---

## 📸 Ekran Görüntüleri

### 1. Tenis Video Analizi ve Kort Izgara Katmanı
Video oynatıcı üzerinde homografi matrisi ile oluşturulan perspektif düzeltmeli kort ızgarası, servis alanları, dip kort bantları ve yan şerit bölgeleri:

<p align="center">
  <img src="assets/tenis_video_analiz.png" alt="Tenis Video Analizi ve Kort Izgarası" width="100%" />
</p>

### 2. Sadeleştirilmiş Ana Sayfa
Kullanıcının doğrudan tenis modüllerine odaklanmasını sağlayan modern ve temiz ana kontrol paneli:

<p align="center">
  <img src="assets/ana_sayfa.png" alt="Ana Sayfa" width="90%" />
</p>

### 3. Tenis Veri Girişi ve Kategori Yönetimi
Sporcular, vuruş stilleri, spin çeşitleri ve maç veritabanı yönetim modülü:

<p align="center">
  <img src="assets/tenis_veri_girisi.png" alt="Tenis Veri Girişi" width="55%" />
</p>

---

## 📹 Hazır Örnek Test Videosu
Projeyi hemen test edebilmeniz için depoya örnek bir tenis maçı video kaydı dahil edilmiştir:
* **Örnek Video:** `Novak Djokovic v Carlos Alcaraz Extended Highlights _ Australian Open 2025 Quarterfinal.mp4`
* Video analiz modülünü açıp bu videoyu doğrudan seçerek kort kalibrasyonunu ve veri etiketleme adımlarını anında test edebilirsiniz.

---

## 🎯 Temel Yetenekler

### 1. Tenis Video Analizi ve Kort Eşleme Modülü
* **Gelişmiş Kare Kare Video İnceleme:** Yüksek çözünürlüklü maç kayıtlarını saniye veya kare (frame) hassasiyetiyle durdurup vuruş anını analiz edebilme.
* **Otomatik Kort Tespiti (`court_detect.py`):** Görüntü işleme ve şablon eşleme algoritmalarıyla kortun 4 köşe noktasını tek tıkla otomatik bulma.
* **Sürüklenebilir Referans Noktaları (`test_corners.py`):** Ekran üzerinde beliren 4 adet interaktif kırmızı referans noktasıyla kort sınırlarını milimetrik olarak elle ayarlayabilme (TCP soket ile arayüzle eş zamanlı çift yönlü veri akışı).
* **Homografi Matrisi ile Izgara Çizimi (`overlay_rect.py`):**
  * Perspektif düzeltme (Homography transform) uygulanmış 8×3 ana ızgara bölgesi.
  * Üst servis alanı (25..32) ve alt dip kort bantları (1x..32x).
  * Yan koridor ve şerit bölgeleri (LT1..LT4, RT1..RT4, LB1..LB4, RB1..RB4).
* **Tek Tuşla Hızlı Veri Etiketleme ('X' Kısayolu):**
  * Maç sırasında topun yere çarptığı veya oyuncunun vuruş yaptığı noktaya fare imlecini getirip klavyeden **`X`** tuşuna basıldığında ilgili kort bölge numarası otomatik tespit edilir.
  * *Vurulan Bölge*, *Düştüğü Bölge*, *Nereden Geldi* ve *Buluşulan Bölge* alanları form üzerinde sıralı olarak otomatik doldurulur.
* **Katman Temizleme:** Ekrandaki tüm çizgileri ve süreçleri dilediğiniz anda tek tuşla sıfırlama.

### 2. Tenis Veri Girişi ve Veritabanı Modülü
* **Sporcu Yönetimi:** Oyuncu profilleri, ad, soyad ve antrenör notlarının kaydı.
* **Vuruş ve Spin Kategorizasyonu:** Forehand, backhand, vole gibi vuruş stilleri ile topspin, slice ve flat gibi spin türlerinin dinamik yönetimi.
* **Yapılandırılmış SQLite Depolama:** Tüm toplanan etiketleme verilerinin yerel veritabanında saklanması ve istendiğinde tek tuşla yedeklenmesi.

### 3. Arka Plan Modülleri (Genişletilebilir Altyapı)
Ana ekranda tenis süreçlerine odaklanılmış sade bir görünüm sunulmakla birlikte; proje kod tabanında kaleci analizi, GPS, oryantiring, UTMB ve kinematik analiz gibi çok disiplinli spor teknolojisi altyapısı mevcuttur.

---

## ⚙️ Gereksinimler ve Kurulum

### Sistem Gereksinimleri
* **İşletim Sistemi:** Windows 10 veya Windows 11 (64-bit)
* **Geliştirme Ortamı:** Visual Studio 2019 / 2022 veya MSBuild
* **Framework:** .NET Framework 4.7.2 / 4.8
* **Python Sürümü:** Python 3.10 veya üzeri (PATH'e eklenmiş olmalıdır)

### Python Kütüphanelerinin Kurulumu
Analiz ve çizim motoru için gerekli paketleri yükleyin:

```bash
pip install PyQt5 keyboard opencv-contrib-python numpy mss scikit-image
```

### Projeyi Çalıştırma
1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/purkusur-pixel/spor-yazilimlari.git
   ```
2. `SporcuTakip.sln` çözüm dosyasını Visual Studio ile açın.
3. Çözümü derleyin ve çalıştırın (`F5` veya `Ctrl+Shift+B`).
4. **Tenis Analiz** butonuna basarak örnek videoyu seçip kort analizine başlayabilirsiniz.
