from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QComboBox, QCheckBox, QGroupBox, QTextEdit, QGridLayout
from PyQt5.QtCore import Qt
from downloader import Downloader
import os # Added for os.startfile
import json
import config_manager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader & Player")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left Panel (Controls)
        self.left_widget = QWidget()
        self.layout = QVBoxLayout(self.left_widget)
        self.main_layout.addWidget(self.left_widget, stretch=7)

        # Right Panel (Logs)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.main_layout.addWidget(self.right_widget, stretch=3)

        # Input Area
        self.input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL veya Dosya Yolu yapıştırın...")
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["720p", "360p", "480p", "1080p", "En İyi"])
        
        self.download_button = QPushButton("İşle")
        self.download_button.clicked.connect(self.start_download)
        
        self.input_layout.addWidget(self.url_input)
        self.input_layout.addWidget(self.resolution_combo)
        self.input_layout.addWidget(self.download_button)

        self.layout.addLayout(self.input_layout)

        # Language Configuration
        self.language_config = self.load_language_config()
        
        # Source Language Selector
        source_lang_layout = QHBoxLayout()
        source_lang_label = QLabel("Kaynak Dil:")
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItem("🔍 Otomatik Algıla", "auto")
        
        # Add languages from config
        for lang_code, lang_info in self.language_config.items():
            flag = lang_info.get('flag', '')
            name = lang_info.get('name', lang_code.upper())
            self.source_lang_combo.addItem(f"{flag} {name}", lang_code)
        
        # Connect to update checkboxes when source language changes
        self.source_lang_combo.currentIndexChanged.connect(self.on_source_lang_changed)
        
        source_lang_layout.addWidget(source_lang_label)
        source_lang_layout.addWidget(self.source_lang_combo)
        source_lang_layout.addStretch()
        self.layout.addLayout(source_lang_layout)
        
        # Multi-Dubbing Checkbox
        self.multi_dub_checkbox = QCheckBox("Çoklu Dublaj")
        self.multi_dub_checkbox.stateChanged.connect(self.toggle_multi_dub)
        self.layout.addWidget(self.multi_dub_checkbox)
        
        # Voice Gender Selector
        voice_gender_layout = QHBoxLayout()
        voice_gender_label = QLabel("Ses Cinsiyeti:")
        self.voice_gender_combo = QComboBox()
        self.voice_gender_combo.addItem("🤖 Otomatik Algıla", "auto")
        self.voice_gender_combo.addItem("👨 Erkek Sesi", "male")
        self.voice_gender_combo.addItem("👩 Kadın Sesi", "female")
        voice_gender_layout.addWidget(voice_gender_label)
        voice_gender_layout.addWidget(self.voice_gender_combo)
        voice_gender_layout.addStretch()
        self.layout.addLayout(voice_gender_layout)
        
        # Language Checkboxes Group
        self.lang_checkboxes_group = QGroupBox("Hedef Diller")
        lang_group_layout = QVBoxLayout()
        
        # Select All Checkbox
        self.select_all_checkbox = QCheckBox("Tümünü Seç")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        lang_group_layout.addWidget(self.select_all_checkbox)
        
        # Language Checkboxes Grid (2 columns)
        lang_grid = QGridLayout()
        self.lang_checkboxes = {}
        
        row = 0
        col = 0
        for lang_code, lang_info in self.language_config.items():
            flag = lang_info.get('flag', '')
            name = lang_info.get('name', lang_code.upper())
            
            checkbox = QCheckBox(f"{flag} {name}")
            checkbox.setProperty("lang_code", lang_code)
            checkbox.stateChanged.connect(self.update_selected_langs_label)
            self.lang_checkboxes[lang_code] = checkbox
            
            lang_grid.addWidget(checkbox, row, col)
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        lang_group_layout.addLayout(lang_grid)
        
        # Selected Languages Label
        self.selected_langs_label = QLabel("Seçili: 0 dil")
        lang_group_layout.addWidget(self.selected_langs_label)
        
        self.lang_checkboxes_group.setLayout(lang_group_layout)
        self.lang_checkboxes_group.setVisible(False)  # Hidden by default
        self.layout.addWidget(self.lang_checkboxes_group)

        # TTS Engine Settings
        settings_group = QGroupBox("TTS Motor Ayarları")
        settings_layout = QVBoxLayout()
        
        # TTS Engine Selector
        engine_layout = QHBoxLayout()
        engine_label = QLabel("TTS Motor:")
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["Edge-TTS (Ücretsiz)", "ElevenLabs (Premium)"])
        self.tts_engine_combo.currentIndexChanged.connect(self.on_tts_engine_changed)
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.tts_engine_combo)
        engine_layout.addStretch()
        settings_layout.addLayout(engine_layout)
        
        # API Key Input (for ElevenLabs)
        api_layout = QHBoxLayout()
        self.api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("ElevenLabs API Key...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_label)
        api_layout.addWidget(self.api_key_input)
        settings_layout.addLayout(api_layout)
        
        # Custom Voice IDs Option
        self.custom_voices_checkbox = QCheckBox("Özel Voice ID'leri Kullan")
        self.custom_voices_checkbox.stateChanged.connect(self.on_custom_voices_changed)
        settings_layout.addWidget(self.custom_voices_checkbox)
        
        # Custom Voice ID Inputs
        self.custom_voice_labels = []
        self.custom_voice_inputs = {}
        
        voice_types = [
            ("tr_male", "Türkçe Erkek Voice ID:"),
            ("tr_female", "Türkçe Kadın Voice ID:"),
            ("en_male", "İngilizce Erkek Voice ID:"),
            ("en_female", "İngilizce Kadın Voice ID:")
        ]
        
        for voice_key, label_text in voice_types:
            voice_layout = QHBoxLayout()
            label = QLabel(label_text)
            input_field = QLineEdit()
            input_field.setPlaceholderText("Voice ID...")
            voice_layout.addWidget(label)
            voice_layout.addWidget(input_field)
            settings_layout.addLayout(voice_layout)
            
            self.custom_voice_labels.append(label)
            self.custom_voice_inputs[voice_key] = input_field
        
        # Prevent Overlap Checkbox
        self.prevent_overlap_checkbox = QCheckBox("Ses Çakışmasını Önle (Hızlandır)")
        self.prevent_overlap_checkbox.setToolTip("Eğer ses altyazı süresinden uzunsa otomatik hızlandırır.")
        settings_layout.addWidget(self.prevent_overlap_checkbox)

        # Save Settings Button
        self.save_settings_button = QPushButton("Ayarları Kaydet")
        self.save_settings_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(self.save_settings_button)
        
        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        # Toggle Log Button
        self.toggle_log_button = QPushButton("Logları Gizle >>")
        self.toggle_log_button.clicked.connect(self.toggle_log_panel)
        self.layout.addWidget(self.toggle_log_button)

        # Status/Log Area (Right Panel)
        log_label = QLabel("Durum ve Loglar:")
        self.right_layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.right_layout.addWidget(self.log_area)
        
        # Cancel Button
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        self.layout.addWidget(self.cancel_button)
        
        # Store paths and config
        self.current_video_path = None
        self.config = config_manager.load_config()
        self.load_settings_to_ui()
        self.downloader = None
        
        # Initial log message
        self.add_log("Hazır")

    def start_download(self):
        url = self.url_input.text()
        resolution = self.resolution_combo.currentText()
        
        if not url:
            self.add_log("❌ HATA: Lütfen bir YouTube URL veya Dosya Yolu girin!")
            return
        
        # Determine target language(s)
        if self.multi_dub_checkbox.isChecked():
            # Multi-language dubbing
            target_languages = self.get_selected_languages()
            if not target_languages:
                self.add_log("❌ HATA: Lütfen en az bir hedef dil seçin!")
                return
            
            lang_names = ", ".join([self.language_config.get(lang, {}).get('name', lang.upper()) for lang in target_languages])
            self.add_log(f"🌐 Çoklu dublaj: {len(target_languages)} dil seçildi ({lang_names})")
        else:
            # Single language or no dubbing
            source_lang = self.source_lang_combo.currentData()
            if source_lang == "auto":
                target_languages = []  # Auto-detect, no dubbing
            else:
                target_languages = [source_lang]

        # Get voice gender preference
        voice_gender = self.voice_gender_combo.currentData()
        self.config['voice_gender_preference'] = voice_gender
        
        # Get prevent overlap preference
        self.config['prevent_overlap'] = self.prevent_overlap_checkbox.isChecked()

        self.add_log("İşleniyor...")
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        self.downloader = Downloader()
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.progress.connect(self.update_status)
        self.downloader.error.connect(self.on_error)
        self.downloader.download(url, resolution, target_languages, self.config)
    
    def add_log(self, message):
        """Add message to log area with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
    
    def cancel_download(self):
        """Cancel ongoing download/dubbing process"""
        if self.downloader and self.downloader.worker:
            self.add_log("⚠️ İşlem iptal ediliyor...")
            self.downloader.worker.terminate()
            self.downloader.worker.wait()
            self.add_log("❌ İşlem iptal edildi")
            self.download_button.setEnabled(True)
            self.cancel_button.setEnabled(False)

    def update_status(self, message): # Kept original name update_status
        self.add_log(message)

    def on_download_finished(self, video_path, subtitle_path):
        self.add_log("✅ İndirme Tamamlandı!")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.current_video_path = video_path
        
        # Don't auto-open - user can manually open if needed
        # self.open_external_player()

    def on_error(self, message): # Kept original name message
        self.add_log(f"❌ HATA: {message}")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def open_external_player(self):
        if self.current_video_path and os.path.exists(self.current_video_path):
            # Windows default player
            os.startfile(self.current_video_path)
        else:
            self.add_log("❌ Video dosyası bulunamadı!")
    
    def load_settings_to_ui(self):
        """Load settings from config to UI"""
        # Set TTS engine
        if self.config.get('tts_engine') == 'elevenlabs':
            self.tts_engine_combo.setCurrentIndex(1)
        else:
            self.tts_engine_combo.setCurrentIndex(0)
        
        # Set API key
        api_key = self.config.get('elevenlabs_api_key', '')
        self.api_key_input.setText(api_key)
        
        # Set custom voices checkbox
        use_custom = self.config.get('use_custom_voices', False)
        self.custom_voices_checkbox.setChecked(use_custom)
        
        # Set custom voice IDs
        custom_voices = self.config.get('custom_voice_ids', {})
        for voice_key, input_field in self.custom_voice_inputs.items():
            input_field.setText(custom_voices.get(voice_key, ''))
        
        # Set prevent overlap
        prevent_overlap = self.config.get('prevent_overlap', True)
        self.prevent_overlap_checkbox.setChecked(prevent_overlap)
        
        # Update visibility
        self.on_tts_engine_changed()
        self.on_custom_voices_changed()
    
    def on_tts_engine_changed(self):
        """Show/hide API key field and custom voices based on selected engine"""
        is_elevenlabs = self.tts_engine_combo.currentIndex() == 1
        self.api_key_label.setVisible(is_elevenlabs)
        self.api_key_input.setVisible(is_elevenlabs)
        self.custom_voices_checkbox.setVisible(is_elevenlabs)
        
        # Update custom voice fields visibility
        if is_elevenlabs:
            self.on_custom_voices_changed()
        else:
            # Hide all custom voice fields if not using ElevenLabs
            for label in self.custom_voice_labels:
                label.setVisible(False)
            for input_field in self.custom_voice_inputs.values():
                input_field.setVisible(False)
    
    def on_custom_voices_changed(self):
        """Show/hide custom voice ID inputs based on checkbox"""
        is_custom = self.custom_voices_checkbox.isChecked()
        is_elevenlabs = self.tts_engine_combo.currentIndex() == 1
        
        # Only show if both ElevenLabs is selected AND custom voices is checked
        show_fields = is_elevenlabs and is_custom
        
        for label in self.custom_voice_labels:
            label.setVisible(show_fields)
        for input_field in self.custom_voice_inputs.values():
            input_field.setVisible(show_fields)
    
    
    def load_language_config(self):
        """Load language configurations from languages.json"""
        try:
            config_path = 'languages.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('languages', {})
            else:
                print("Warning: languages.json not found")
                return {}
        except Exception as e:
            print(f"Error loading language config: {e}")
            return {}
    
    def toggle_multi_dub(self):
        """Show/hide multi-language checkbox group"""
        is_enabled = self.multi_dub_checkbox.isChecked()
        self.lang_checkboxes_group.setVisible(is_enabled)
        if is_enabled:
            self.source_lang_combo.setEnabled(False)
        else:
            self.source_lang_combo.setEnabled(True)
    
    def on_select_all_changed(self, state):
        """Select/deselect all language checkboxes"""
        is_checked = state == Qt.Checked
        for checkbox in self.lang_checkboxes.values():
            checkbox.setChecked(is_checked)
    
    def update_selected_langs_label(self):
        """Update the selected languages count and codes label"""
        selected = self.get_selected_languages()
        count = len(selected)
        if count > 0:
            codes = ", ".join([c.upper() for c in selected])
            self.selected_langs_label.setText(f"Seçili: {count} dil ({codes})")
        else:
            self.selected_langs_label.setText("Seçili: 0 dil")
    
    def get_selected_languages(self):
        """Get list of selected language codes"""
        return [code for code, cb in self.lang_checkboxes.items() if cb.isChecked()]
    
    def on_source_lang_changed(self):
        """Disable source language checkbox in multi-dub mode"""
        source_lang = self.source_lang_combo.currentData()
        
        # Enable all checkboxes first
        for lang_code, checkbox in self.lang_checkboxes.items():
            checkbox.setEnabled(True)
        
        # If a specific source language is selected (not auto), disable it
        if source_lang != "auto" and source_lang in self.lang_checkboxes:
            self.lang_checkboxes[source_lang].setEnabled(False)
            self.lang_checkboxes[source_lang].setChecked(False)
            self.update_selected_langs_label()
    
    def save_settings(self):
        """Save settings from UI to config file"""
        # Update config
        if self.tts_engine_combo.currentIndex() == 1:
            self.config['tts_engine'] = 'elevenlabs'
        else:
            self.config['tts_engine'] = 'edge-tts'
        
        self.config['elevenlabs_api_key'] = self.api_key_input.text()
        
        # Save custom voices settings
        self.config['use_custom_voices'] = self.custom_voices_checkbox.isChecked()
        
        # Save custom voice IDs
        if 'custom_voice_ids' not in self.config:
            self.config['custom_voice_ids'] = {}
        
        for voice_key, input_field in self.custom_voice_inputs.items():
            self.config['custom_voice_ids'][voice_key] = input_field.text()
        
        # Save prevent overlap
        self.config['prevent_overlap'] = self.prevent_overlap_checkbox.isChecked()
        
        # Save to file
        if config_manager.save_config(self.config):
            self.add_log("✅ Ayarlar kaydedildi!")
        else:
            self.add_log("❌ Ayarlar kaydedilemedi!")

    def toggle_log_panel(self):
        """Toggle the visibility of the log panel"""
        if self.right_widget.isVisible():
            self.right_widget.hide()
            self.toggle_log_button.setText("Logları Göster <<")
        else:
            self.right_widget.show()
            self.toggle_log_button.setText("Logları Gizle >>")
