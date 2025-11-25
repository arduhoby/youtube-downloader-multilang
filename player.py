from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt, QTimer
import webvtt
import os
import re

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        # Subtitle Label (Overlay)
        self.subtitle_label = QLabel(self.video_widget)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("QLabel { color: white; font-size: 24px; background-color: rgba(0, 0, 0, 150); padding: 5px; }")
        self.subtitle_label.hide()
        
        # Player
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.on_position_changed)

        self.subtitles = [] # List of (start_ms, end_ms, text)

    def load_video(self, video_path, subtitle_path):
        print(f"DEBUG: Player loading video: {video_path}")
        print(f"DEBUG: Player loading subtitle: {subtitle_path}")
        
        if not os.path.exists(video_path):
            print("ERROR: Video file does not exist!")
            return

        url = QUrl.fromLocalFile(video_path)
        content = QMediaContent(url)
        self.media_player.setMedia(content)
        self.media_player.play()
        
        # Hata yakalama
        self.media_player.error.connect(self.handle_errors)
        
        if subtitle_path and os.path.exists(subtitle_path):
            self.load_subtitles(subtitle_path)
        else:
            print("DEBUG: No subtitle loaded.")
            self.subtitles = []
            self.subtitle_label.hide()

    def handle_errors(self):
        print(f"ERROR: MediaPlayer Error: {self.media_player.errorString()}")

    def load_subtitles(self, path):
        self.subtitles = []
        try:
            if path.endswith('.vtt'):
                for caption in webvtt.read(path):
                    # webvtt-py caption.start and .end are in string format "HH:MM:SS.mmm"
                    start_ms = self.time_to_ms(caption.start)
                    end_ms = self.time_to_ms(caption.end)
                    self.subtitles.append((start_ms, end_ms, caption.text))
            elif path.endswith('.srt'):
                self.parse_srt(path)
        except Exception as e:
            print(f"Altyazı yükleme hatası: {e}")

    def parse_srt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basit SRT parser
        pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:(?!\n\n).)*)', re.DOTALL)
        
        for match in pattern.finditer(content):
            start_str = match.group(2).replace(',', '.')
            end_str = match.group(3).replace(',', '.')
            text = match.group(4).strip()
            
            start_ms = self.time_to_ms(start_str)
            end_ms = self.time_to_ms(end_str)
            self.subtitles.append((start_ms, end_ms, text))

    def time_to_ms(self, time_str):
        # Format: HH:MM:SS.mmm or MM:SS.mmm
        parts = time_str.split('.')
        ms = int(parts[1]) if len(parts) > 1 else 0
        
        time_parts = parts[0].split(':')
        if len(time_parts) == 3:
            h, m, s = map(int, time_parts)
            return (h * 3600 + m * 60 + s) * 1000 + ms
        elif len(time_parts) == 2:
            m, s = map(int, time_parts)
            return (m * 60 + s) * 1000 + ms
        else:
            return 0 

    def on_position_changed(self, position):
        # Find subtitle for current position
        current_text = ""
        for start, end, text in self.subtitles:
            if start <= position <= end:
                current_text = text
                break
        
        if current_text:
            self.subtitle_label.setText(current_text)
            self.subtitle_label.adjustSize()
            # Center at bottom
            rect = self.video_widget.rect()
            self.subtitle_label.move((rect.width() - self.subtitle_label.width()) // 2, rect.height() - self.subtitle_label.height() - 50)
            self.subtitle_label.show()
        else:
            self.subtitle_label.hide()

    def resizeEvent(self, event):
        # Reposition subtitle on resize
        rect = self.video_widget.rect()
        self.subtitle_label.move((rect.width() - self.subtitle_label.width()) // 2, rect.height() - self.subtitle_label.height() - 50)
        super().resizeEvent(event)
