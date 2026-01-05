"""
Tests for Voice Configuration.
"""

import pytest
from src.shadowengine.voice.config import (
    VoiceConfig, STTConfig, InputConfig, WakeWordConfig, AccessibilityConfig,
    STTEngineType, WakeWordMode
)


class TestSTTConfig:
    """Tests for STTConfig."""

    def test_create_config(self):
        """Can create STT config."""
        config = STTConfig()
        assert config.engine_type == STTEngineType.MOCK
        assert config.language == "en"
        assert config.sample_rate == 16000

    def test_custom_config(self):
        """Can create custom config."""
        config = STTConfig(
            engine_type=STTEngineType.WHISPER,
            model_size="large",
            device="cuda",
            language="es",
        )
        assert config.engine_type == STTEngineType.WHISPER
        assert config.model_size == "large"
        assert config.device == "cuda"
        assert config.language == "es"

    def test_serialization(self):
        """Config can be serialized and deserialized."""
        config = STTConfig(
            engine_type=STTEngineType.VOSK,
            model_path="/path/to/model",
            sample_rate=22050,
        )
        data = config.to_dict()
        restored = STTConfig.from_dict(data)

        assert restored.engine_type == config.engine_type
        assert restored.model_path == config.model_path
        assert restored.sample_rate == config.sample_rate


class TestWakeWordConfig:
    """Tests for WakeWordConfig."""

    def test_create_config(self):
        """Can create wake word config."""
        config = WakeWordConfig()
        assert config.mode == WakeWordMode.PUSH_TO_TALK
        assert config.wake_phrase == "hey shadow"

    def test_custom_config(self):
        """Can create custom config."""
        config = WakeWordConfig(
            mode=WakeWordMode.WAKE_WORD,
            wake_phrase="computer",
            sensitivity=0.8,
            timeout_ms=15000,
        )
        assert config.mode == WakeWordMode.WAKE_WORD
        assert config.wake_phrase == "computer"
        assert config.sensitivity == 0.8
        assert config.timeout_ms == 15000

    def test_serialization(self):
        """Config can be serialized and deserialized."""
        config = WakeWordConfig(
            mode=WakeWordMode.HYBRID,
            alternative_phrases=["game", "shadow"],
        )
        data = config.to_dict()
        restored = WakeWordConfig.from_dict(data)

        assert restored.mode == config.mode
        assert restored.alternative_phrases == config.alternative_phrases


class TestInputConfig:
    """Tests for InputConfig."""

    def test_create_config(self):
        """Can create input config."""
        config = InputConfig()
        assert config.primary_mode == "keyboard"
        assert config.enable_keyboard is True
        assert config.enable_voice is False

    def test_custom_config(self):
        """Can create custom config."""
        config = InputConfig(
            primary_mode="voice",
            enable_voice=True,
            enable_keyboard=True,
            fuzzy_match_threshold=0.8,
        )
        assert config.primary_mode == "voice"
        assert config.enable_voice is True
        assert config.fuzzy_match_threshold == 0.8

    def test_serialization(self):
        """Config can be serialized and deserialized."""
        config = InputConfig(
            command_timeout_ms=10000,
            urgent_response_window_ms=3000,
        )
        data = config.to_dict()
        restored = InputConfig.from_dict(data)

        assert restored.command_timeout_ms == config.command_timeout_ms
        assert restored.urgent_response_window_ms == config.urgent_response_window_ms


class TestAccessibilityConfig:
    """Tests for AccessibilityConfig."""

    def test_create_config(self):
        """Can create accessibility config."""
        config = AccessibilityConfig()
        assert config.subtitles_enabled is True
        assert config.command_suggestions is True

    def test_custom_config(self):
        """Can create custom config."""
        config = AccessibilityConfig(
            extended_timeout=True,
            timeout_multiplier=2.0,
            audio_confirmation=True,
        )
        assert config.extended_timeout is True
        assert config.timeout_multiplier == 2.0
        assert config.audio_confirmation is True

    def test_serialization(self):
        """Config can be serialized and deserialized."""
        config = AccessibilityConfig(
            show_confidence=True,
            highlight_urgent=False,
        )
        data = config.to_dict()
        restored = AccessibilityConfig.from_dict(data)

        assert restored.show_confidence == config.show_confidence
        assert restored.highlight_urgent == config.highlight_urgent


class TestVoiceConfig:
    """Tests for VoiceConfig."""

    def test_create_default(self, default_config):
        """Can create default config."""
        assert default_config.stt.engine_type == STTEngineType.MOCK
        assert default_config.input.primary_mode == "keyboard"

    def test_keyboard_only_preset(self, keyboard_only_config):
        """Keyboard-only preset works."""
        assert keyboard_only_config.stt.engine_type == STTEngineType.NONE
        assert keyboard_only_config.input.enable_voice is False
        assert keyboard_only_config.input.enable_keyboard is True

    def test_voice_primary_preset(self, voice_primary_config):
        """Voice-primary preset works."""
        assert voice_primary_config.stt.engine_type == STTEngineType.WHISPER
        assert voice_primary_config.input.enable_voice is True
        assert voice_primary_config.input.primary_mode == "voice"

    def test_hybrid_preset(self, hybrid_config):
        """Hybrid preset works."""
        assert hybrid_config.stt.engine_type == STTEngineType.VOSK
        assert hybrid_config.input.enable_voice is True
        assert hybrid_config.input.enable_keyboard is True
        assert hybrid_config.input.primary_mode == "hybrid"

    def test_accessibility_preset(self, accessibility_config):
        """Accessibility preset works."""
        assert accessibility_config.accessibility.extended_timeout is True
        assert accessibility_config.accessibility.timeout_multiplier == 2.0
        assert accessibility_config.input.command_timeout_ms == 10000

    def test_validate_valid_config(self, default_config):
        """Valid config passes validation."""
        errors = default_config.validate()
        assert len(errors) == 0

    def test_validate_voice_without_engine(self):
        """Validation catches voice without engine."""
        config = VoiceConfig(
            stt=STTConfig(engine_type=STTEngineType.NONE),
            input=InputConfig(enable_voice=True),
        )
        errors = config.validate()
        assert any("no STT engine" in e for e in errors)

    def test_validate_wake_word_without_phrase(self):
        """Validation catches wake word without phrase."""
        config = VoiceConfig(
            wake_word=WakeWordConfig(
                mode=WakeWordMode.WAKE_WORD,
                wake_phrase="",
            ),
        )
        errors = config.validate()
        assert any("wake phrase" in e for e in errors)

    def test_validate_no_input_methods(self):
        """Validation catches no input methods."""
        config = VoiceConfig(
            input=InputConfig(
                enable_voice=False,
                enable_keyboard=False,
            ),
        )
        errors = config.validate()
        assert any("input method" in e for e in errors)

    def test_validate_invalid_threshold(self):
        """Validation catches invalid threshold."""
        config = VoiceConfig(
            input=InputConfig(fuzzy_match_threshold=1.5),
        )
        errors = config.validate()
        assert any("threshold" in e for e in errors)

    def test_validate_invalid_multiplier(self):
        """Validation catches invalid multiplier."""
        config = VoiceConfig(
            accessibility=AccessibilityConfig(timeout_multiplier=0),
        )
        errors = config.validate()
        assert any("multiplier" in e for e in errors)

    def test_serialization(self, voice_primary_config):
        """Config can be serialized and deserialized."""
        data = voice_primary_config.to_dict()
        restored = VoiceConfig.from_dict(data)

        assert restored.stt.engine_type == voice_primary_config.stt.engine_type
        assert restored.input.primary_mode == voice_primary_config.input.primary_mode
        assert restored.wake_word.mode == voice_primary_config.wake_word.mode


class TestSTTEngineType:
    """Tests for STTEngineType enum."""

    def test_engine_types_exist(self):
        """All engine types exist."""
        assert STTEngineType.WHISPER.value == "whisper"
        assert STTEngineType.VOSK.value == "vosk"
        assert STTEngineType.MOCK.value == "mock"
        assert STTEngineType.NONE.value == "none"


class TestWakeWordMode:
    """Tests for WakeWordMode enum."""

    def test_modes_exist(self):
        """All modes exist."""
        assert WakeWordMode.DISABLED.value == "disabled"
        assert WakeWordMode.WAKE_WORD.value == "wake_word"
        assert WakeWordMode.PUSH_TO_TALK.value == "push_to_talk"
        assert WakeWordMode.HYBRID.value == "hybrid"
