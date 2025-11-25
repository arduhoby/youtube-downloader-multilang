# YouTube Video Downloader & AI Dubbing Tool

Modern bir YouTube video indirme ve yapay zeka destekli dublaj uygulaması. PyQt5 tabanlı kullanıcı dostu arayüz ile videolarınızı indirin, otomatik altyazı oluşturun ve çift yönlü dublaj yapın.

## 🎯 Özellikler

### 📥 Video İndirme
- YouTube videolarını farklı çözünürlüklerde indirme (360p, 480p, 720p, 1080p, En İyi)
- Otomatik format seçimi ve dönüştürme
- İlerleme takibi ve durum bildirimleri
- İndirilen videoları otomatik olarak harici oynatıcıda açma

### 🤖 AI Destekli Altyazı Oluşturma
- **Whisper AI** ile otomatik konuşma tanıma
- Otomatik dil algılama
- Çift yönlü çeviri desteği:
  - Türkçe → İngilizce
  - İngilizce → Türkçe
- SRT formatında altyazı dosyası oluşturma

### 🎙️ Çift Yönlü Dublaj Sistemi

#### **Edge-TTS (Ücretsiz, Varsayılan)**
- Microsoft Edge TTS motoru
- Yüksek kaliteli, doğal sesler
- Otomatik cinsiyet algılama
- **Türkçe Sesler:**
  - Ahmet (Erkek)
  - Emel (Kadın)
- **İngilizce Sesler:**
  - Guy (Erkek)
  - Jenny (Kadın)

#### **ElevenLabs (Premium)**
- Profesyonel kalitede TTS
- Çok daha doğal ve insansı sesler
- Pre-made sesler (ücretsiz tier):
  - Adam (Türkçe Erkek)
  - Bella (Türkçe Kadın)
  - Clyde (İngilizce Erkek)
  - Elli (İngilizce Kadın)
- **Özel Voice ID Desteği:**
  - Kendi klonlanmış seslerinizi kullanabilirsiniz
  - 4 farklı ses için özel ID girişi
  - Otomatik fallback pre-made seslere

### 🎨 Kullanıcı Arayüzü
- Modern ve temiz PyQt5 arayüzü
- Kalıcı log sistemi (tüm işlemler kaydedilir)
- Zaman damgalı mesajlar
- İptal butonu (işlemi istediğiniz zaman durdurun)
- Emoji ile görsel geri bildirim (✅ ❌ ⚠️)
- Ayarları kaydetme/yükleme sistemi

### 📁 Dosya Organizasyonu
- Tüm medya dosyaları `media/` klasöründe
- Otomatik klasör oluşturma
- Düzenli dosya yapısı:
  - Videolar: `media/{video_id}.wmv`
  - Altyazılar: `media/{video_id}.{lang}.srt`
  - Dublajlı videolar: `media/{video_id}_dubbed.wmv`

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- FFmpeg (sistem PATH'inde olmalı)
- Windows işletim sistemi

### Adımlar

1. **Repoyu klonlayın:**
```bash
git clone <repo-url>
cd yt_dld
```

2. **Virtual environment oluşturun:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **FFmpeg kurulumu:**
   - [FFmpeg'i indirin](https://ffmpeg.org/download.html)
   - Sistem PATH'ine ekleyin veya uygulama `C:\Users\{user}\AppData\Local\Microsoft\WinGet\Links` konumunu kontrol eder

5. **Uygulamayı başlatın:**
```bash
python main.py
```

## 📖 Kullanım

### Temel Kullanım

1. **Video İndirme:**
   - YouTube URL'sini yapıştırın
   - Çözünürlük seçin
   - "İndir ve Oynat" butonuna tıklayın

2. **Dublaj Seçenekleri:**
   - **Dublaj Yok:** Sadece video ve altyazı indirilir
   - **Türkçe Dublaj:** İngilizce video → Türkçe dublaj
   - **İngilizce Dublaj:** Türkçe video → İngilizce dublaj

### TTS Motor Ayarları

#### Edge-TTS Kullanımı (Varsayılan)
1. TTS Motor: "Edge-TTS (Ücretsiz)" seçili bırakın
2. Herhangi bir ayar gerekmez
3. Otomatik olarak çalışır

#### ElevenLabs Kullanımı

**Pre-made Sesler:**
1. TTS Motor: "ElevenLabs (Premium)" seçin
2. API Key'inizi girin ([ElevenLabs](https://elevenlabs.io) hesabından alın)
3. "Ayarları Kaydet" butonuna tıklayın
4. Varsayılan sesler kullanılır

**Özel Sesler:**
1. "Özel Voice ID'leri Kullan" checkbox'ını işaretleyin
2. Voice ID alanları görünür
3. ElevenLabs'den aldığınız voice ID'leri girin:
   - Türkçe Erkek Voice ID
   - Türkçe Kadın Voice ID
   - İngilizce Erkek Voice ID
   - İngilizce Kadın Voice ID
4. "Ayarları Kaydet" butonuna tıklayın

### İşlemi İptal Etme
- İndirme veya dublaj sırasında "İptal" butonu aktif olur
- Butona tıklayarak işlemi istediğiniz zaman durdurabilirsiniz

## ⚙️ Yapılandırma

Tüm ayarlar `config.json` dosyasında saklanır:

```json
{
  "tts_engine": "edge-tts",
  "elevenlabs_api_key": "your-api-key",
  "use_custom_voices": false,
  "elevenlabs_voices": {
    "tr_male": "pNInz6obpgDQGcFmaJgB",
    "tr_female": "EXAVITQu4vr4xnSDxMaL",
    "en_male": "2EiwWnXFnvU5JabPnv8n",
    "en_female": "MF3mGyEYCl7XYWbV9V6O"
  },
  "custom_voice_ids": {
    "tr_male": "",
    "tr_female": "",
    "en_male": "",
    "en_female": ""
  }
}
```

## 🏗️ Proje Yapısı

```
yt_dld/
├── main.py                 # Uygulama giriş noktası
├── main_window.py          # Ana pencere ve UI
├── downloader.py           # İndirme ve dublaj mantığı
├── config_manager.py       # Ayar yönetimi
├── requirements.txt        # Python bağımlılıkları
├── config.json            # Kullanıcı ayarları
├── media/                 # İndirilen dosyalar
└── .venv/                 # Virtual environment
```

## 🔧 Teknik Detaylar

### Kullanılan Teknolojiler
- **PyQt5:** GUI framework
- **yt-dlp:** YouTube video indirme
- **Whisper AI:** Konuşma tanıma
- **Deep Translator:** Çeviri
- **Edge-TTS:** Microsoft TTS motoru
- **ElevenLabs:** Premium TTS API
- **pydub:** Ses manipülasyonu
- **FFmpeg:** Video/ses işleme

### Dublaj İş Akışı
1. Video indirilir
2. Ses çıkarılır (FFmpeg)
3. Konuşma metne dönüştürülür (Whisper)
4. Metin çevrilir (Deep Translator)
5. Altyazı oluşturulur (SRT)
6. Cinsiyet algılanır (metin analizi)
7. TTS ile ses oluşturulur (Edge-TTS/ElevenLabs)
8. Ses parçaları birleştirilir (pydub)
9. Video ile birleştirilir (FFmpeg)

### Otomatik Fallback
- ElevenLabs hatası → Edge-TTS'e geçer
- Özel voice ID boş → Pre-made seslere geçer
- API hatası → Detaylı hata mesajı gösterir

## 🐛 Sorun Giderme

### FFmpeg Bulunamadı
```
FFmpeg'i PATH'e ekleyin veya şu konuma kopyalayın:
C:\Users\{user}\AppData\Local\Microsoft\WinGet\Links
```

### Whisper Hatası
```bash
pip uninstall whisper
pip install openai-whisper
```

### Torch Hatası
```bash
pip install torch==2.2.2
pip install numpy==1.26.4
```

### ElevenLabs Voice Not Found
- Voice ID'lerin doğru olduğundan emin olun
- Pre-made voice ID'leri kullanın
- API key'in geçerli olduğunu kontrol edin

## 📝 Notlar

- **ElevenLabs Ücretsiz Tier:** 10,000 karakter/ay
- **Önerilen Video Süresi:** 5-10 dakika (daha uzun videolar için daha fazla işlem süresi)
- **Desteklenen Diller:** Türkçe ↔ İngilizce
- **Video Formatı:** WMV (FFmpeg ile otomatik dönüştürme)

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen pull request gönderin veya issue açın.

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🙏 Teşekkürler

- OpenAI Whisper ekibine
- Microsoft Edge-TTS ekibine
- ElevenLabs ekibine
- yt-dlp geliştiricilerine

---

**Not:** Bu uygulama eğitim amaçlıdır. Telif hakkı korumalı içerikleri indirirken yerel yasalara uyun.
