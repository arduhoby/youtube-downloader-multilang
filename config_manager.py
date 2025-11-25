import json
import os

CONFIG_FILE = "config.json"

def get_default_config():
    """Return default configuration"""
    return {
        "tts_engine": "edge-tts",  # "edge-tts" or "elevenlabs"
        "elevenlabs_api_key": "",
        "use_custom_voices": False,  # True to use custom voice IDs
        "elevenlabs_voices": {
            # ElevenLabs pre-made voice IDs (free tier compatible)
            "tr_male": "pNInz6obpgDQGcFmaJgB",    # Adam (multilingual)
            "tr_female": "EXAVITQu4vr4xnSDxMaL",  # Bella (multilingual)
            "en_male": "2EiwWnXFnvU5JabPnv8n",    # Clyde
            "en_female": "MF3mGyEYCl7XYWbV9V6O"  # Elli
        },
        "custom_voice_ids": {
            "tr_male": "",
            "tr_female": "",
            "en_male": "",
            "en_female": ""
        },
        # Video format settings
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "video_quality": 23,  # CRF value (18-28, lower = higher quality)
        "audio_bitrate": "192k",
        # Multi-language settings
        "default_source_lang": "auto",
        "default_target_lang": "en",
        "enabled_languages": ["tr", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
    }


def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default = get_default_config()
                default.update(config)
                return default
        except Exception as e:
            print(f"Config load error: {e}")
            return get_default_config()
    else:
        # Create default config file
        default = get_default_config()
        save_config(default)
        return default

def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False
