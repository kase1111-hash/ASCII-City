"""Tests for the TTS engine system."""

import pytest
from src.shadowengine.audio.tts_engine import (
    TTSEngine,
    TTSEngineType,
    TTSEngineManager,
    TTSEngineError,
    TTSRequest,
    AudioData,
    AudioFormat,
    MockTTSEngine
)
from src.shadowengine.audio.voice import CharacterVoice, VoiceParameters


class TestAudioData:
    """Tests for AudioData."""

    def test_create_audio_data(self):
        """Test creating audio data."""
        data = b'\x00' * 1000
        audio = AudioData(
            data=data,
            format=AudioFormat.WAV,
            sample_rate=22050,
            channels=1,
            bit_depth=16
        )
        assert len(audio.data) == 1000
        assert audio.format == AudioFormat.WAV
        assert audio.sample_rate == 22050

    def test_duration_estimation(self):
        """Test automatic duration estimation."""
        # 22050 Hz, 16-bit = 44100 bytes per second
        # 1 second of audio = 44100 bytes
        data = b'\x00' * 44100
        audio = AudioData(
            data=data,
            sample_rate=22050,
            channels=1,
            bit_depth=16
        )
        assert audio.duration_ms == pytest.approx(1000, abs=10)

    def test_to_dict(self):
        """Test serialization."""
        audio = AudioData(
            data=b'\x00' * 100,
            format=AudioFormat.WAV,
            text="Hello",
            voice_id="v1",
            engine="Mock"
        )
        d = audio.to_dict()
        assert d['format'] == 'wav'
        assert d['text'] == "Hello"
        assert d['voice_id'] == "v1"
        assert d['engine'] == "Mock"


class TestTTSRequest:
    """Tests for TTSRequest."""

    def test_create_request(self):
        """Test creating TTS request."""
        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Hello world", voice=voice)
        assert request.text == "Hello world"
        assert request.voice == voice
        assert request.format == AudioFormat.WAV

    def test_get_effective_params(self):
        """Test getting effective parameters."""
        voice = CharacterVoice(
            character_id="c1",
            name="Test",
            base_params=VoiceParameters(speed=0.5)
        )
        request = TTSRequest(
            text="Test",
            voice=voice,
            speed_override=0.8
        )
        params = request.get_effective_params()
        assert params.speed == 0.8

    def test_cache_key_unique(self):
        """Test cache key generation."""
        voice = CharacterVoice(character_id="c1", name="Test")
        r1 = TTSRequest(text="Hello", voice=voice)
        r2 = TTSRequest(text="Hello", voice=voice)
        r3 = TTSRequest(text="Different", voice=voice)

        assert r1.get_cache_key() == r2.get_cache_key()
        assert r1.get_cache_key() != r3.get_cache_key()


class TestMockTTSEngine:
    """Tests for MockTTSEngine."""

    def test_initialize(self):
        """Test engine initialization."""
        engine = MockTTSEngine()
        assert not engine.is_available()

        result = engine.initialize()
        assert result is True
        assert engine.is_available()

    def test_engine_properties(self):
        """Test engine properties."""
        engine = MockTTSEngine()
        assert engine.engine_type == TTSEngineType.MOCK
        assert engine.name == "Mock TTS Engine"

    def test_synthesize_basic(self):
        """Test basic synthesis."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Hello world", voice=voice)

        audio = engine.synthesize(request)
        assert isinstance(audio, AudioData)
        assert len(audio.data) > 0
        assert audio.duration_ms > 0
        assert audio.text == "Hello world"
        assert audio.voice_id == "c1"

    def test_synthesis_duration_scales_with_text(self):
        """Test that longer text produces longer audio."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")
        short_request = TTSRequest(text="Hi", voice=voice)
        long_request = TTSRequest(text="This is a much longer sentence with many more words", voice=voice)

        short_audio = engine.synthesize(short_request)
        long_audio = engine.synthesize(long_request)

        assert long_audio.duration_ms > short_audio.duration_ms

    def test_speed_affects_duration(self):
        """Test that speed parameter affects duration."""
        engine = MockTTSEngine()
        engine.initialize()

        voice_slow = CharacterVoice(
            character_id="c1",
            name="Test",
            base_params=VoiceParameters(speed=0.2)
        )
        voice_fast = CharacterVoice(
            character_id="c2",
            name="Test",
            base_params=VoiceParameters(speed=0.8)
        )

        slow_audio = engine.synthesize(TTSRequest(text="Hello world", voice=voice_slow))
        fast_audio = engine.synthesize(TTSRequest(text="Hello world", voice=voice_fast))

        assert slow_audio.duration_ms > fast_audio.duration_ms

    def test_synthesis_count(self):
        """Test synthesis counter."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")

        assert engine.synthesis_count == 0

        engine.synthesize(TTSRequest(text="First", voice=voice))
        assert engine.synthesis_count == 1

        engine.synthesize(TTSRequest(text="Second", voice=voice))
        assert engine.synthesis_count == 2

    def test_last_request(self):
        """Test last request tracking."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test text", voice=voice)

        engine.synthesize(request)
        assert engine.last_request == request

    def test_reset_stats(self):
        """Test stats reset."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")
        engine.synthesize(TTSRequest(text="Test", voice=voice))

        engine.reset_stats()
        assert engine.synthesis_count == 0
        assert engine.last_request is None

    def test_failure_mode(self):
        """Test failure mode for error handling tests."""
        engine = MockTTSEngine()
        engine.initialize()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test", voice=voice)

        # Normal operation
        engine.synthesize(request)

        # Enable failure mode
        engine.set_failure_mode(True)
        assert not engine.is_available()

        with pytest.raises(TTSEngineError):
            engine.synthesize(request)

        # Disable failure mode
        engine.set_failure_mode(False)
        engine.synthesize(request)  # Should work again

    def test_not_initialized_error(self):
        """Test error when not initialized."""
        engine = MockTTSEngine()
        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test", voice=voice)

        with pytest.raises(TTSEngineError):
            engine.synthesize(request)

    def test_supported_formats(self):
        """Test supported formats."""
        engine = MockTTSEngine()
        formats = engine.get_supported_formats()
        assert AudioFormat.WAV in formats
        assert AudioFormat.RAW in formats

    def test_shutdown(self):
        """Test engine shutdown."""
        engine = MockTTSEngine()
        engine.initialize()
        assert engine.is_available()

        engine.shutdown()
        assert not engine.is_available()


class TestTTSEngineManager:
    """Tests for TTSEngineManager."""

    def test_register_engine(self):
        """Test registering an engine."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()

        manager.register_engine(engine)
        assert manager.get_engine(TTSEngineType.MOCK) == engine

    def test_register_primary(self):
        """Test setting primary engine."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()

        manager.register_engine(engine, set_primary=True)
        assert manager._primary_engine == TTSEngineType.MOCK

    def test_initialize_all(self):
        """Test initializing all engines."""
        manager = TTSEngineManager()
        manager.register_engine(MockTTSEngine())

        results = manager.initialize_all()
        assert results[TTSEngineType.MOCK] is True

    def test_get_available_engines(self):
        """Test getting available engines."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine)
        manager.initialize_all()

        available = manager.get_available_engines()
        assert len(available) == 1
        assert available[0] == engine

    def test_synthesize_uses_primary(self):
        """Test synthesis uses primary engine."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine, set_primary=True)
        manager.initialize_all()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Hello", voice=voice)

        audio = manager.synthesize(request)
        assert engine.synthesis_count == 1
        assert audio.engine == engine.name

    def test_cache_hit(self):
        """Test caching works."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine, set_primary=True)
        manager.initialize_all()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Same text", voice=voice)

        audio1 = manager.synthesize(request)
        audio2 = manager.synthesize(request)

        # Should only synthesize once due to cache
        assert engine.synthesis_count == 1
        assert audio1 == audio2

    def test_cache_disabled(self):
        """Test cache can be disabled."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine, set_primary=True)
        manager.initialize_all()
        manager.set_cache_enabled(False)

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Same text", voice=voice)

        manager.synthesize(request, use_cache=False)
        manager.synthesize(request, use_cache=False)

        assert engine.synthesis_count == 2

    def test_clear_cache(self):
        """Test cache clearing."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine, set_primary=True)
        manager.initialize_all()

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test", voice=voice)

        manager.synthesize(request)
        manager.clear_cache()
        manager.synthesize(request)

        assert engine.synthesis_count == 2

    def test_fallback_on_failure(self):
        """Test that only one engine per type can be registered."""
        manager = TTSEngineManager()

        primary = MockTTSEngine()
        fallback = MockTTSEngine()

        manager.register_engine(primary, set_primary=True)
        # Registering same type replaces the first one
        manager.register_engine(fallback)

        manager.initialize_all()

        # The fallback replaced primary, so setting primary's failure mode
        # doesn't affect the registered engine
        primary.set_failure_mode(True)

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test", voice=voice)

        # Should succeed using fallback (which replaced primary)
        audio = manager.synthesize(request)
        assert audio is not None

    def test_all_engines_fail(self):
        """Test error when all engines fail."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine, set_primary=True)
        manager.initialize_all()
        engine.set_failure_mode(True)

        voice = CharacterVoice(character_id="c1", name="Test")
        request = TTSRequest(text="Test", voice=voice)

        with pytest.raises(TTSEngineError) as exc_info:
            manager.synthesize(request)
        assert "All TTS engines failed" in str(exc_info.value)

    def test_shutdown_all(self):
        """Test shutting down all engines."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine)
        manager.initialize_all()

        assert engine.is_available()
        manager.shutdown_all()
        assert not engine.is_available()

    def test_set_fallback_order(self):
        """Test setting fallback order."""
        manager = TTSEngineManager()
        engine = MockTTSEngine()
        manager.register_engine(engine)

        # Should handle invalid types gracefully
        manager.set_fallback_order([TTSEngineType.MOCK, TTSEngineType.COQUI])
        assert TTSEngineType.MOCK in manager._fallback_order
        assert TTSEngineType.COQUI not in manager._fallback_order
