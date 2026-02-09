"""
Tests for Text-to-Speech engine.
"""

import pytest
import time
from src.shadowengine.audio.tts import (
    TTSEngine, TTSResult, TTSStatus, TTSConfig,
    MockTTSEngine, CoquiTTSEngine, PiperTTSEngine,
    create_tts_engine,
)


class TestTTSConfig:
    """Tests for TTSConfig."""

    def test_create_config(self):
        """Can create TTS config."""
        config = TTSConfig(
            model_name="test_model",
            sample_rate=44100,
            use_cuda=True,
        )
        assert config.model_name == "test_model"
        assert config.sample_rate == 44100
        assert config.use_cuda is True

    def test_default_values(self):
        """Config has sensible defaults."""
        config = TTSConfig()
        assert config.model_name == "default"
        assert config.sample_rate == 22050
        assert config.use_cuda is False
        assert config.cache_enabled is True

    def test_serialization(self):
        """Config can be serialized and deserialized."""
        config = TTSConfig(model_name="custom", sample_rate=16000)
        data = config.to_dict()
        restored = TTSConfig.from_dict(data)

        assert restored.model_name == config.model_name
        assert restored.sample_rate == config.sample_rate


class TestTTSResult:
    """Tests for TTSResult."""

    def test_create_result(self):
        """Can create TTS result."""
        result = TTSResult(
            audio_data=b"audio_content",
            sample_rate=22050,
            duration_ms=1000.0,
            text="hello",
        )
        assert result.audio_data == b"audio_content"
        assert result.duration_ms == 1000.0
        assert result.text == "hello"

    def test_is_empty(self):
        """Can check if result is empty."""
        empty = TTSResult(audio_data=b"")
        assert empty.is_empty is True

        non_empty = TTSResult(audio_data=b"audio")
        assert non_empty.is_empty is False

    def test_duration_seconds(self):
        """Can get duration in seconds."""
        result = TTSResult(duration_ms=2500.0)
        assert result.duration_seconds == 2.5

    def test_serialization(self):
        """Result can be serialized."""
        result = TTSResult(
            audio_data=b"test",
            text="hello",
            voice_id="voice1",
            cached=True,
        )
        data = result.to_dict()

        assert data["text"] == "hello"
        assert data["voice_id"] == "voice1"
        assert data["audio_size_bytes"] == 4


class TestMockTTSEngine:
    """Tests for MockTTSEngine."""

    def test_initialize(self, mock_tts):
        """Can initialize mock engine."""
        assert mock_tts.is_initialized is True
        assert mock_tts.status == TTSStatus.READY

    def test_synthesize(self, mock_tts):
        """Can synthesize speech."""
        result = mock_tts.synthesize("hello world")
        assert result.text == "hello world"
        assert len(result.audio_data) > 0
        assert result.duration_ms > 0

    def test_set_response(self, mock_tts):
        """Can set preset response."""
        mock_tts.set_response(b"custom_audio", 500.0)
        result = mock_tts.synthesize("test")

        assert result.audio_data == b"custom_audio"
        assert result.duration_ms == 500.0

    def test_set_multiple_responses(self, mock_tts):
        """Can set multiple responses in order."""
        mock_tts.set_responses([
            (b"first", 100.0),
            (b"second", 200.0),
            (b"third", 300.0),
        ])

        # Use unique text for each call to avoid caching
        assert mock_tts.synthesize("text1").audio_data == b"first"
        assert mock_tts.synthesize("text2").audio_data == b"second"
        assert mock_tts.synthesize("text3").audio_data == b"third"

    def test_available_voices(self, mock_tts):
        """Can get available voices."""
        voices = mock_tts.get_available_voices()
        assert "default" in voices
        assert len(voices) >= 5

    def test_add_voice(self, mock_tts):
        """Can add custom voice."""
        mock_tts.add_voice("custom_voice")
        assert "custom_voice" in mock_tts.get_available_voices()

    def test_voice_parameter(self, mock_tts):
        """Can use different voices."""
        result = mock_tts.synthesize("test", voice_id="male_1")
        assert result.voice_id == "male_1"

    def test_speed_parameter(self, mock_tts):
        """Can adjust speed."""
        result = mock_tts.synthesize("test", speed=1.5)
        assert result is not None

    def test_pitch_parameter(self, mock_tts):
        """Can adjust pitch."""
        result = mock_tts.synthesize("test", pitch=0.8)
        assert result is not None

    def test_delay(self, mock_tts):
        """Can add artificial delay."""
        mock_tts.set_delay(50)  # 50ms delay

        start = time.time()
        mock_tts.synthesize("test")
        elapsed = (time.time() - start) * 1000

        assert elapsed >= 40  # Allow tolerance

    def test_caching(self, mock_tts):
        """Results are cached."""
        result1 = mock_tts.synthesize("cached text", "voice1")
        result2 = mock_tts.synthesize("cached text", "voice1")

        assert result2.cached is True

    def test_cache_key_includes_parameters(self, mock_tts):
        """Cache key includes all parameters."""
        result1 = mock_tts.synthesize("text", "voice1", 1.0, 1.0)
        result2 = mock_tts.synthesize("text", "voice1", 1.5, 1.0)

        # Different speed should not return cached result
        assert result2.cached is False

    def test_clear_cache(self, mock_tts):
        """Can clear cache."""
        mock_tts.synthesize("test")
        cleared = mock_tts.clear_cache()

        assert cleared >= 1

    def test_callbacks(self, mock_tts):
        """Callbacks are invoked."""
        results = []
        mock_tts.on_result(lambda r: results.append(r))

        mock_tts.synthesize("callback test")

        assert len(results) == 1
        assert results[0].text == "callback test"

    def test_shutdown(self, mock_tts):
        """Can shutdown engine."""
        mock_tts.shutdown()

        assert mock_tts.is_initialized is False
        assert mock_tts.status == TTSStatus.DISABLED

    def test_engine_info(self, mock_tts):
        """Can get engine info."""
        info = mock_tts.get_engine_info()

        assert info["name"] == "MockTTSEngine"
        assert info["initialized"] is True
        assert "config" in info


class TestCoquiTTSEngine:
    """Tests for CoquiTTSEngine."""

    def test_create(self, coqui_tts):
        """Can create Coqui engine."""
        assert coqui_tts.model_name == "tts_models/en/ljspeech/tacotron2-DDC"

    def test_initialize(self, coqui_tts):
        """Can initialize Coqui engine."""
        assert coqui_tts.is_initialized is True
        assert coqui_tts.status == TTSStatus.READY

    def test_available_voices(self, coqui_tts):
        """Coqui has available voices."""
        voices = coqui_tts.get_available_voices()
        assert len(voices) >= 1
        assert "ljspeech" in voices

    def test_synthesize(self, coqui_tts):
        """Can synthesize with Coqui."""
        result = coqui_tts.synthesize("hello")
        assert len(result.audio_data) > 0

    def test_load_custom_voice(self, coqui_tts):
        """Can load custom voice."""
        success = coqui_tts.load_custom_voice("/path/to/voice", "custom")
        assert success is True
        assert "custom" in coqui_tts.get_available_voices()

    def test_shutdown(self, coqui_tts):
        """Can shutdown Coqui."""
        coqui_tts.shutdown()
        assert coqui_tts.is_initialized is False


class TestPiperTTSEngine:
    """Tests for PiperTTSEngine."""

    def test_create(self, piper_tts):
        """Can create Piper engine."""
        assert piper_tts.model_path is None

    def test_initialize(self, piper_tts):
        """Can initialize Piper engine."""
        assert piper_tts.is_initialized is True
        assert piper_tts.status == TTSStatus.READY

    def test_available_voices(self, piper_tts):
        """Piper has available voices."""
        voices = piper_tts.get_available_voices()
        assert len(voices) >= 1
        assert "en_US-lessac-medium" in voices

    def test_synthesize(self, piper_tts):
        """Can synthesize with Piper."""
        result = piper_tts.synthesize("hello")
        assert len(result.audio_data) > 0

    def test_download_voice(self, piper_tts):
        """Can download voice."""
        success = piper_tts.download_voice("new_voice")
        assert success is True
        assert "new_voice" in piper_tts.get_available_voices()


class TestCreateTTSEngine:
    """Tests for engine factory function."""

    def test_create_mock(self):
        """Can create mock engine."""
        engine = create_tts_engine("mock")
        assert isinstance(engine, MockTTSEngine)

    def test_create_coqui(self):
        """Can create Coqui engine."""
        engine = create_tts_engine("coqui")
        assert isinstance(engine, CoquiTTSEngine)

    def test_create_piper(self):
        """Can create Piper engine."""
        engine = create_tts_engine("piper")
        assert isinstance(engine, PiperTTSEngine)

    def test_case_insensitive(self):
        """Engine type is case insensitive."""
        engine = create_tts_engine("MOCK")
        assert isinstance(engine, MockTTSEngine)

        engine = create_tts_engine("Coqui")
        assert isinstance(engine, CoquiTTSEngine)

    def test_unknown_defaults_to_mock(self):
        """Unknown engine type defaults to mock."""
        engine = create_tts_engine("unknown_engine")
        assert isinstance(engine, MockTTSEngine)

    def test_pass_config(self):
        """Can pass configuration to factory."""
        engine = create_tts_engine("mock", sample_rate=44100)
        assert engine.config.sample_rate == 44100

    def test_pass_engine_specific_args(self):
        """Can pass engine-specific arguments."""
        # model_path is a Piper-specific argument
        engine = create_tts_engine("piper", model_path="/custom/path")
        assert engine.model_path == "/custom/path"
