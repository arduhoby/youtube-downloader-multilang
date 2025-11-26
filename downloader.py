import os
import shutil
import json
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import yt_dlp
import whisper
from deep_translator import GoogleTranslator
import torch
import datetime
import edge_tts
import asyncio
from pydub import AudioSegment
import re
from elevenlabs.client import ElevenLabs

class DownloaderWorker(QThread):
    finished = pyqtSignal(str, str) # video_path, subtitle_path
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, resolution="720p", target_languages=None, config=None):
        super().__init__()
        self.url = url
        self.resolution = resolution
        # Accept both single language (string) or multiple languages (list)
        if isinstance(target_languages, str):
            self.target_languages = [target_languages] if target_languages else []
        elif isinstance(target_languages, list):
            self.target_languages = target_languages
        else:
            self.target_languages = []
        self.config = config if config else {}  # Config for TTS engine selection
        self.language_config = self.load_language_config()  # Load language configurations

    def run(self):
        # FFmpeg yolunu PATH'e ekle
        ffmpeg_dir = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links'
        if ffmpeg_dir not in os.environ['PATH']:
            os.environ['PATH'] += os.pathsep + ffmpeg_dir
        
        # FFmpeg kontrolü
        if not shutil.which('ffmpeg'):
            self.error.emit(f"FFmpeg bulunamadı! ({ffmpeg_dir})")
            return

        # Media klasörünü oluştur
        media_dir = 'media'
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)

        # Temizlik
        self.cleanup()

        # Çözünürlük ayarı
        format_str = self.get_format_string()

        try:
            ydl_opts = {
                'format': format_str,
                'outtmpl': 'media/%(id)s.%(ext)s',  # Media klasörüne kaydet
                'skip_download': False,
                'progress_hooks': [self.progress_hook],
                'ignoreerrors': True,
                'ffmpeg_location': ffmpeg_dir,
            }

            filename = None
            
            # Check if input is a local file
            if os.path.exists(self.url) and os.path.isfile(self.url):
                self.progress.emit(f"📂 Yerel dosya algılandı: {self.url}")
                
                # Create a copy in media folder to avoid modifying original
                base_name = os.path.basename(self.url)
                # Remove invalid characters for safety
                base_name = "".join([c for c in base_name if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).rstrip()
                target_path = os.path.join(media_dir, base_name)
                
                try:
                    shutil.copy2(self.url, target_path)
                    filename = target_path
                    self.progress.emit("Dosya kopyalandı, işleniyor...")
                except Exception as e:
                    self.error.emit(f"Dosya kopyalama hatası: {e}")
                    return
            else:
                # It's a URL, download with yt-dlp
                self.progress.emit("Video indiriliyor...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
                    if not info:
                        self.error.emit("Video bilgileri alınamadı.")
                        return
                    filename = ydl.prepare_filename(info)
            
            if filename:
                # 1. Videoyu MP4'e çevir (Evrensel uyumluluk için)
                self.progress.emit("Video formatı dönüştürülüyor (MP4)...")
                final_filename = self.convert_video(filename)
                final_filename = os.path.abspath(final_filename)

                # 2. Process each target language
                subtitle_path = None  # Initialize
                if self.target_languages:
                    for lang_index, target_lang in enumerate(self.target_languages):
                        lang_info = self.language_config.get(target_lang, {})
                        lang_name = lang_info.get('name', target_lang.upper())
                        
                        self.progress.emit(f"🌐 [{lang_index + 1}/{len(self.target_languages)}] {lang_name} işleniyor...")
                        
                        try:
                            # Generate subtitle for this language
                            self.progress.emit(f"AI: {lang_name} altyazı oluşturuluyor...")
                            current_subtitle = self.generate_ai_subtitle(final_filename, target_lang)
                            
                            if current_subtitle:
                                subtitle_path = os.path.abspath(current_subtitle)  # Track last successful
                                
                                # Generate dubbing for this language
                                self.progress.emit(f"🎙️ {lang_name} dublaj oluşturuluyor...")
                                dubbed_video_path = self.generate_dubbing(final_filename, subtitle_path, target_lang, self.config)
                                
                                if dubbed_video_path:
                                    self.progress.emit(f"✅ {lang_name} dublaj tamamlandı: {os.path.basename(dubbed_video_path)}")
                                else:
                                    self.progress.emit(f"⚠️ {lang_name} dublaj oluşturulamadı")
                            else:
                                self.progress.emit(f"⚠️ {lang_name} altyazı oluşturulamadı")
                        except Exception as e:
                            self.progress.emit(f"❌ {lang_name} hatası: {str(e)}")
                    
                    self.progress.emit(f"🎉 Tüm dublajlar tamamlandı! ({len(self.target_languages)} dil)")
                    # Return the original video and last subtitle
                    self.finished.emit(final_filename, subtitle_path if subtitle_path else "")
                else:
                    # No dubbing, just create original subtitle
                    self.progress.emit("Yapay Zeka altyazı oluşturuyor (orijinal dil)...")
                    subtitle_path = self.generate_ai_subtitle(final_filename, None)
                    
                    if subtitle_path:
                        subtitle_path = os.path.abspath(subtitle_path)
                    
                    self.finished.emit(final_filename, subtitle_path if subtitle_path else "")

        except Exception as e:
            self.error.emit(str(e))

    def cleanup(self):
        try:
            for f in os.listdir('.'):
                if f.startswith(self.url.split('=')[-1]) or f.endswith('.part'):
                    try:
                        os.remove(f)
                    except:
                        pass
        except:
            pass

    def get_format_string(self):
        if self.resolution == "1080p":
            return 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif self.resolution == "720p":
            return 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif self.resolution == "480p":
            return 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        elif self.resolution == "360p":
            return 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        return 'bestvideo+bestaudio/best'
    
    def load_language_config(self):
        """Load language configurations from languages.json"""
        try:
            config_path = 'languages.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('languages', {})
            else:
                print("Warning: languages.json not found, using defaults")
                return {}
        except Exception as e:
            print(f"Error loading language config: {e}")
            return {}
    
    def detect_language(self, audio_path):
        """Detect language using Whisper"""
        try:
            model = whisper.load_model("base")
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            return detected_lang
        except Exception as e:
            print(f"Language detection error: {e}")
            return "en"  # Default to English


    def generate_ai_subtitle(self, video_path, target_language=None):
        try:
            # 1. Sesi ayıkla
            self.progress.emit("AI: Ses videodan ayrıştırılıyor...")
            audio_path = "media/temp_audio.mp3"  # Media klasörüne kaydet
            self.extract_audio(video_path, audio_path)

            # 2. Whisper ile Transkript (STT)
            self.progress.emit("AI: Konuşmalar metne dökülüyor (Whisper)...")
            model = whisper.load_model("base") # 'tiny', 'base', 'small', 'medium', 'large'
            result = model.transcribe(audio_path)
            
            # Detect source language
            detected_language = result.get('language', 'en')
            self.progress.emit(f"AI: Tespit edilen dil: {detected_language}")
            
            # 3. Çeviri ve SRT oluşturma
            if target_language:
                # Get language info from config
                lang_info = self.language_config.get(target_language, {})
                lang_name = lang_info.get('name', target_language.upper())
                translator_code = lang_info.get('translator_code', target_language)
                
                self.progress.emit(f"AI: {lang_name}'ye çevriliyor ve SRT oluşturuluyor...")
                translator = GoogleTranslator(source='auto', target=translator_code)
                lang_suffix = f"{detected_language}_{target_language}"
            else:
                # No translation, use original language
                self.progress.emit("AI: SRT oluşturuluyor (orijinal dil)...")
                translator = None
                lang_suffix = detected_language
            
            srt_content = ""
            
            segments = result['segments']
            for i, segment in enumerate(segments):
                start = self.format_timestamp(segment['start'])
                end = self.format_timestamp(segment['end'])
                text = segment['text'].strip()
                
                # Çeviri
                try:
                    if translator:
                        translated_text = translator.translate(text)
                    else:
                        translated_text = text  # No translation
                except:
                    translated_text = text  # Çeviri hatası olursa orijinali kullan

                srt_content += f"{i+1}\n{start} --> {end}\n{translated_text}\n\n"
                
                # İlerleme güncellemesi (her 5 segmentte bir)
                if i % 5 == 0:
                    percent = int((i / len(segments)) * 100)
                    self.progress.emit(f"AI: Çevriliyor %{percent}")

            # SRT Kaydet
            base_name = os.path.splitext(video_path)[0]
            srt_path = f"{base_name}.{lang_suffix}.srt"  # Dil suffix'i ile kaydet
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            # Temizlik
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            # Return subtitle path and detected language for voice selection
            return srt_path

        except Exception as e:
            print(f"AI Subtitle Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def extract_audio(self, video_path, output_audio_path):
        import subprocess
        ffmpeg_exe = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
        cmd = [
            ffmpeg_exe,
            '-i', video_path,
            '-vn', # Video yok
            '-acodec', 'libmp3lame',
            '-y',
            output_audio_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def format_timestamp(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        # datetime.timedelta str formatı: H:MM:SS.micros
        # SRT formatı: HH:MM:SS,mmm
        
        total_seconds = int(seconds)
        milliseconds = int((seconds - total_seconds) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

    def convert_video(self, input_path):
        """Convert video to MP4 format with H.264/AAC codecs"""
        import subprocess
        output_path = os.path.splitext(input_path)[0] + ".mp4"
        ffmpeg_exe = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
        
        # Get config settings
        video_codec = self.config.get('video_codec', 'libx264')
        audio_codec = self.config.get('audio_codec', 'aac')
        video_quality = self.config.get('video_quality', 23)
        audio_bitrate = self.config.get('audio_bitrate', '192k')
        
        cmd = [
            ffmpeg_exe, '-i', input_path,
            '-c:v', video_codec,  # H.264 codec
            '-preset', 'medium',  # Encoding speed/quality balance
            '-crf', str(video_quality),  # Quality (18-28, lower = higher quality)
            '-c:a', audio_codec,  # AAC codec
            '-b:a', audio_bitrate,  # Audio bitrate
            '-ar', '44100',  # Sample rate
            '-movflags', '+faststart',  # Web streaming optimization
            '-y', output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if input_path != output_path and os.path.exists(input_path):
                try: os.remove(input_path)
                except: pass
            return output_path
        except:
            return input_path

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            self.progress.emit(f"İndiriliyor: {p}")
        elif d['status'] == 'finished':
            self.progress.emit("İndirme bitti, işleniyor...")

    def generate_dubbing(self, video_path, subtitle_path, target_language, config):
        """Generate dubbed audio (Turkish or English) and merge with video"""
        try:
            # Parse SRT file
            subtitles = self.parse_srt(subtitle_path)
            if not subtitles:
                self.progress.emit("❌ Dublaj: SRT dosyası okunamadı")
                return None
            
            # Get video duration
            video_duration = self.get_video_duration(video_path)
            if not video_duration:
                self.progress.emit("❌ Dublaj: Video süresi alınamadı")
                return None
            
            # Check TTS engine
            tts_engine = config.get('tts_engine', 'edge-tts')
            
            # Select voice based on engine
            if tts_engine == 'elevenlabs':
                voice = self.select_elevenlabs_voice(subtitles, target_language, config)
                self.progress.emit(f"Dublaj: ElevenLabs sesi - {voice}")
                use_elevenlabs = True
            else:
                voice = self.select_voice(subtitles, target_language)
                self.progress.emit(f"Dublaj: Edge-TTS sesi - {voice}")
                use_elevenlabs = False
            
            # Create silent audio track
            self.progress.emit("Dublaj: Sessiz ses parçası oluşturuluyor...")
            silent_audio = AudioSegment.silent(duration=int(video_duration * 1000))  # milliseconds
            
            # Generate TTS for each subtitle
            temp_audio_files = []
            for i, subtitle in enumerate(subtitles):
                start_time = subtitle['start']
                text = subtitle['text']
                
                if i % 5 == 0:
                    percent = int((i / len(subtitles)) * 100)
                    self.progress.emit(f"Dublaj: TTS oluşturuluyor %{percent}")
                
                # Generate TTS
                temp_tts_file = f"media/temp_tts_{i}.mp3"  # Media klasörüne kaydet
                try:
                    if use_elevenlabs:
                        # Try ElevenLabs
                        try:
                            self.generate_elevenlabs_tts(text, temp_tts_file, voice, config)
                        except Exception as e:
                            # Log error and fallback to Edge-TTS
                            error_msg = f"ElevenLabs hata: {str(e)}"
                            print(error_msg)
                            self.progress.emit(error_msg)
                            self.progress.emit("Edge-TTS'e geçiliyor...")
                            edge_voice = self.select_voice(subtitles, target_language)
                            asyncio.run(self.generate_edge_tts(text, temp_tts_file, edge_voice))
                    else:
                        # Use Edge-TTS
                        asyncio.run(self.generate_edge_tts(text, temp_tts_file, voice))
                    
                    temp_audio_files.append(temp_tts_file)
                    
                    # Load TTS audio
                    tts_audio = AudioSegment.from_mp3(temp_tts_file)
                    tts_duration = len(tts_audio) / 1000.0  # seconds
                    
                    # Calculate available time slot
                    if i < len(subtitles) - 1:
                        next_start = subtitles[i+1]['start']
                    else:
                        next_start = video_duration
                    
                    max_duration = next_start - start_time
                    
                    # Check if TTS is too long
                    prevent_overlap = config.get('prevent_overlap', True)
                    
                    if prevent_overlap and tts_duration > max_duration and max_duration > 0.5: # Ensure max_duration is reasonable
                        speed_rate = tts_duration / max_duration
                        # Add 10% buffer and clamp between 1.0 and 2.0
                        speed_rate = min(max(speed_rate * 1.1, 1.0), 2.0)
                        
                        if speed_rate > 1.05: # Only speed up if significant
                            self.progress.emit(f"⚠️ Hızlandırılıyor: {speed_rate:.2f}x (Segment {i+1})")
                            sped_up_file = f"media/temp_tts_{i}_fast.mp3"
                            if self.speed_up_audio(temp_tts_file, sped_up_file, speed_rate):
                                tts_audio = AudioSegment.from_mp3(sped_up_file)
                                temp_audio_files.append(sped_up_file)
                    
                    # Calculate overlay position (in milliseconds)
                    overlay_position = int(start_time * 1000)
                    
                    # Overlay TTS audio onto silent track
                    silent_audio = silent_audio.overlay(tts_audio, position=overlay_position)
                    
                except Exception as e:
                    error_msg = f"TTS Error for segment {i}: {e}"
                    print(error_msg)
                    self.progress.emit(error_msg)
                    continue
            
            # Export dubbed audio
            self.progress.emit("Dublaj: Ses dosyası kaydediliyor...")
            dubbed_audio_path = "media/temp_dubbed_audio.mp3"  # Media klasörüne kaydet
            silent_audio.export(dubbed_audio_path, format="mp3")
            
            # Merge dubbed audio with video
            self.progress.emit("Dublaj: Video ile birleştiriliyor...")
            base_name = os.path.splitext(video_path)[0]
            dubbed_video_path = f"{base_name}_dubbed_{target_language}.mp4"
            
            ffmpeg_exe = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
            cmd = [
                ffmpeg_exe,
                '-i', video_path,
                '-i', dubbed_audio_path,
                '-c:v', 'copy',  # Copy video stream
                '-map', '0:v:0',  # Use video from first input
                '-map', '1:a:0',  # Use audio from second input
                '-shortest',  # Match shortest stream
                '-y',
                dubbed_video_path
            ]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.progress.emit(f"❌ FFmpeg hatası: {result.stderr[:200]}")
                return None
            
            # Cleanup temp files
            for temp_file in temp_audio_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            if os.path.exists(dubbed_audio_path):
                try:
                    os.remove(dubbed_audio_path)
                except:
                    pass
            
            return dubbed_video_path
            
        except Exception as e:
            error_msg = f"Dubbing Error: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.progress.emit(f"❌ Dublaj hatası: {str(e)}")
            return None
    
    def parse_srt(self, srt_path):
        """Parse SRT subtitle file"""
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # SRT format: index, timestamp, text, blank line
            pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n|\Z)'
            matches = re.findall(pattern, content)
            
            subtitles = []
            for match in matches:
                start_str = match[1]
                end_str = match[2]
                text = match[3].strip()
                
                # Convert timestamp to seconds
                start_seconds = self.timestamp_to_seconds(start_str)
                end_seconds = self.timestamp_to_seconds(end_str)
                
                subtitles.append({
                    'start': start_seconds,
                    'end': end_seconds,
                    'text': text
                })
            
            return subtitles
            
        except Exception as e:
            print(f"SRT Parse Error: {e}")
            return None
    
    def timestamp_to_seconds(self, timestamp):
        """Convert SRT timestamp (HH:MM:SS,mmm) to seconds"""
        # Format: 00:00:01,234
        time_part, ms_part = timestamp.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        
        total_seconds = h * 3600 + m * 60 + s + ms / 1000.0
        return total_seconds
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds using ffprobe"""
        try:
            import subprocess
            ffprobe_exe = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links\ffprobe.exe'
            cmd = [
                ffprobe_exe,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            print(f"Get Duration Error: {e}")
            return None

    async def generate_edge_tts(self, text, output_file, voice):
        """Generate TTS using edge-tts (async)"""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
    
    def select_voice(self, subtitles, target_language):
        """Select appropriate voice based on target language and gender detection"""
        
        # Check if user has manual preference
        user_preference = self.config.get('voice_gender_preference', 'auto')
        
        if user_preference == 'male':
            is_male = True
            self.progress.emit(f"🎭 Cinsiyet: Erkek (Manuel seçim)")
        elif user_preference == 'female':
            is_male = False
            self.progress.emit(f"🎭 Cinsiyet: Kadın (Manuel seçim)")
        else:
            # Auto-detect
            all_text = " ".join([sub['text'] for sub in subtitles]).lower()
            
            # Gender detection (improved heuristic)
            male_indicators = ['bay', 'bey', 'erkek', 'adam', 'abi', 'ağabey', 'he', 'his', 'him', 'man', 'boy', 'mr', 'sir', 'gentleman']
            female_indicators = ['bayan', 'hanım', 'kadın', 'abla', 'kız', 'she', 'her', 'woman', 'girl', 'ms', 'mrs', 'miss', 'lady', 'madam']
            
            male_score = sum(all_text.count(word) for word in male_indicators)
            female_score = sum(all_text.count(word) for word in female_indicators)
            
            # More conservative: only use male voice if clearly male (2x more male indicators)
            # Default to female voice when uncertain
            is_male = male_score > (female_score * 2) and male_score > 2
            
            # Debug logging
            gender = "Erkek" if is_male else "Kadın"
            self.progress.emit(f"🎭 Cinsiyet algılama: {gender} (E:{male_score}, K:{female_score})")
        
        # Get voice from language config
        lang_info = self.language_config.get(target_language, {})
        edge_voices = lang_info.get('edge_tts', {})
        
        if edge_voices:
            selected_voice = edge_voices.get('male' if is_male else 'female', 'en-US-GuyNeural')
        else:
            # Fallback to default voices
            if target_language == 'tr':
                selected_voice = "tr-TR-AhmetNeural" if is_male else "tr-TR-EmelNeural"
            else:
                selected_voice = "en-US-GuyNeural" if is_male else "en-US-JennyNeural"
        
        self.progress.emit(f"🎤 Seçilen ses: {selected_voice}")
        return selected_voice
    
    def generate_elevenlabs_tts(self, text, output_file, voice_id, config):
        """Generate TTS using ElevenLabs API"""
        try:
            api_key = config.get('elevenlabs_api_key', '')
            if not api_key:
                raise Exception("API key boş! Lütfen ayarlardan ElevenLabs API key'inizi girin.")
            
            # Initialize ElevenLabs client
            client = ElevenLabs(api_key=api_key)
            
            # Generate audio using text_to_speech
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )
            
            # Save audio to file (audio_generator is an iterator of bytes)
            with open(output_file, 'wb') as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
        except Exception as e:
            error_str = str(e)
            if "api_key" in error_str.lower() or "unauthorized" in error_str.lower():
                raise Exception(f"Geçersiz API key! Lütfen ayarlarınızı kontrol edin. Hata: {error_str}")
            elif "quota" in error_str.lower() or "limit" in error_str.lower():
                raise Exception(f"ElevenLabs kota aşıldı! Hata: {error_str}")
            else:
                raise Exception(f"ElevenLabs API hatası: {error_str}")
    
    def select_elevenlabs_voice(self, subtitles, target_language, config):
        """Select ElevenLabs voice based on language and gender"""
        all_text = " ".join([sub['text'] for sub in subtitles]).lower()
        
        # Gender detection
        male_indicators = ['bay', 'bey', 'erkek', 'adam', 'abi', 'ağabey', 'he', 'his', 'him', 'man', 'boy', 'mr']
        female_indicators = ['bayan', 'hanım', 'kadın', 'abla', 'kız', 'she', 'her', 'woman', 'girl', 'ms', 'mrs']
        
        male_score = sum(all_text.count(word) for word in male_indicators)
        female_score = sum(all_text.count(word) for word in female_indicators)
        
        is_male = male_score > female_score * 1.5
        
        # Check if using custom voices
        use_custom = config.get('use_custom_voices', False)
        
        if use_custom:
            # Use custom voice IDs (for TR and EN only, for now)
            custom_voices = config.get('custom_voice_ids', {})
            if target_language == 'tr':
                voice_id = custom_voices.get('tr_male' if is_male else 'tr_female', '')
            elif target_language == 'en':
                voice_id = custom_voices.get('en_male' if is_male else 'en_female', '')
            else:
                voice_id = ''
            
            # If custom voice is empty, fallback to language config
            if not voice_id:
                lang_info = self.language_config.get(target_language, {})
                elevenlabs_voices = lang_info.get('elevenlabs', {})
                return elevenlabs_voices.get('male' if is_male else 'female', 'pNInz6obpgDQGcFmaJgB')
            return voice_id
        else:
            # Use voices from language config
            lang_info = self.language_config.get(target_language, {})
            elevenlabs_voices = lang_info.get('elevenlabs', {})
            
            if elevenlabs_voices:
                return elevenlabs_voices.get('male' if is_male else 'female', 'pNInz6obpgDQGcFmaJgB')
            else:
                # Fallback to default multilingual voice
                return 'pNInz6obpgDQGcFmaJgB'

    def speed_up_audio(self, input_path, output_path, speed_rate):
        """Speed up audio using FFmpeg atempo filter"""
        try:
            import subprocess
            ffmpeg_exe = r'C:\Users\melih\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
            
            # atempo filter accepts values between 0.5 and 2.0 (or 100.0 in newer versions, but safe range is 0.5-2.0)
            # If rate > 2.0, we might need multiple passes, but we capped it at 2.0
            
            cmd = [
                ffmpeg_exe,
                '-i', input_path,
                '-filter:a', f"atempo={speed_rate}",
                '-vn',
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            print(f"Speed Up Error: {e}")
            return False

class Downloader(QObject):
    finished = pyqtSignal(str, str)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.worker = None

    def download(self, url, resolution="720p", target_languages=None, config=None):
        self.worker = DownloaderWorker(url, resolution, target_languages, config)
        self.worker.finished.connect(self.finished)
        self.worker.progress.connect(self.progress)
        self.worker.error.connect(self.error)
        self.worker.start()
