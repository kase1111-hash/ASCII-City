"""
Tests for Speech-to-Text engine.
"""

import pytest
import time
from src.shadowengine.voice.stt import (
    STTEngine, STTResult, STTStatus,
    MockSTTEngine, WhisperEngine, VoskEngine,
    create_stt_engine
)


class TestSTTResult:
    """Tests for STTResult class."""

    def test_create_result(self):
        """Can create STT result."""
        result = STTResult(
            text="hello world",
            confidence=0.95,
            duration_ms=500,
        )
        assert result.text == "hello world"
        assert result.confidence == 0.95
        assert result.duration_ms == 500

    def test_is_empty(self):
        """Can check if result is empty."""
        empty = STTResult(text="")
        assert empty.is_empty is True

        non_empty = STTResult(text="hello")
        assert non_empty.is_empty is False

        whitespace = STTResult(text="   ")
        assert whitespace.is_empty is True

    def test_words(self):
        """Can get words from text."""
        result = STTResult(text="Hello World Test")
        assert result.words == ["hello", "world", "test"]

    def test_serialization(self):
        """Result can be serialized and deserialized."""
        result = STTResult(
            text="test",
            confidence=0.9,
            duration_ms=100,
            language="en",
            alternatives=["tess", "test"],
        )
        data = result.to_dict()
        restored = STTResult.from_dict(data)

        assert restored.text == result.text
        assert restored.confidence == result.confidence
        assert restored.language == result.language


class TestMockSTTEngine:
    """Tests for MockSTTEngine."""

    def test_initialize(self, mock_stt):
        """Can initialize mock engine."""
        assert mock_stt.is_initialized is True
        assert mock_stt.status == STTStatus.IDLE

    def test_set_response(self, mock_stt):
        """Can set and get responses."""
        mock_stt.set_response("hello world", 0.95)

        result = mock_stt.transcribe(b"audio")
        assert result.text == "hello world"
        assert result.confidence == 0.95

    def test_set_multiple_responses(self, mock_stt):
        """Can set and get multiple responses in order."""
        mock_stt.set_responses([
            ("first", 0.9),
            ("second", 0.8),
            ("third", 0.7),
        ])

        assert mock_stt.transcribe(b"").text == "first"
        assert mock_stt.transcribe(b"").text == "second"
        assert mock_stt.transcribe(b"").text == "third"
        assert mock_stt.transcribe(b"").text == ""  # Queue empty

    def test_streaming_mode(self, mock_stt):
        """Can use streaming mode."""
        mock_stt.set_streaming_responses([
            ("hel", 0.5, False),
            ("hello", 0.7, False),
            ("hello world", 0.95, True),
        ])

        assert mock_stt.start_streaming() is True
        assert mock_stt.status == STTStatus.LISTENING

        # Feed audio and get partial results
        result1 = mock_stt.feed_audio(b"chunk1")
        assert result1.text == "hel"
        assert result1.is_final is False

        result2 = mock_stt.feed_audio(b"chunk2")
        assert result2.text == "hello"

        result3 = mock_stt.feed_audio(b"chunk3")
        assert result3.text == "hello world"
        assert result3.is_final is True

        # Stop streaming
        final = mock_stt.stop_streaming()
        assert final.text == "hello world"
        assert mock_stt.status == STTStatus.IDLE

    def test_shutdown(self, mock_stt):
        """Can shutdown engine."""
        mock_stt.shutdown()
        assert mock_stt.is_initialized is False
        assert mock_stt.status == STTStatus.DISABLED

    def test_transcribe_file(self, mock_stt):
        """Can transcribe file."""
        mock_stt.set_response("file content", 0.9)

        result = mock_stt.transcribe_file("/path/to/file.wav")
        assert result.text == "file content"
        assert result.raw_audio_path == "/path/to/file.wav"

    def test_set_language(self, mock_stt):
        """Can set language."""
        assert mock_stt.set_language("es") is True
        assert mock_stt.set_language("test") is True  # Mock accepts anything

    def test_get_supported_languages(self, mock_stt):
        """Can get supported languages."""
        languages = mock_stt.get_supported_languages()
        assert "en" in languages
        assert "test" in languages

    def test_callbacks(self, mock_stt):
        """Callbacks are invoked."""
        results = []
        mock_stt.on_result(lambda r: results.append(r))

        mock_stt.set_response("test", 0.9)
        mock_stt.transcribe(b"")

        assert len(results) == 1
        assert results[0].text == "test"

    def test_delay(self, mock_stt):
        """Can add artificial delay."""
        mock_stt.set_delay(100)  # 100ms delay
        mock_stt.set_response("delayed", 0.9)

        start = time.time()
        mock_stt.transcribe(b"")
        elapsed = (time.time() - start) * 1000

        assert elapsed >= 90  # Allow some tolerance

    def test_engine_info(self, mock_stt):
        """Can get engine info."""
        info = mock_stt.get_engine_info()
        assert "name" in info
        assert info["name"] == "MockSTTEngine"
        assert info["initialized"] is True


class TestWhisperEngine:
    """Tests for WhisperEngine."""

    def test_create_whisper(self, whisper_engine):
        """Can create Whisper engine."""
        assert whisper_engine.model_size == "base"
        assert whisper_engine.device == "cpu"

    def test_initialize(self, whisper_engine):
        """Can initialize Whisper engine."""
        assert whisper_engine.initialize() is True
        assert whisper_engine.is_initialized is True

    def test_supported_languages(self, whisper_engine):
        """Whisper supports many languages."""
        whisper_engine.initialize()
        languages = whisper_engine.get_supported_languages()
        assert "en" in languages
        assert "es" in languages
        assert "zh" in languages
        assert len(languages) >= 10

    def test_set_language(self, whisper_engine):
        """Can set language."""
        whisper_engine.initialize()
        assert whisper_engine.set_language("fr") is True
        assert whisper_engine.set_language("invalid") is False

    def test_streaming(self, whisper_engine):
        """Can use streaming mode."""
        whisper_engine.initialize()
        assert whisper_engine.start_streaming() is True
        assert whisper_engine.status == STTStatus.LISTENING

        whisper_engine.stop_streaming()
        assert whisper_engine.status == STTStatus.IDLE


class TestVoskEngine:
    """Tests for VoskEngine."""

    def test_create_vosk(self, vosk_engine):
        """Can create Vosk engine."""
        assert vosk_engine.model_path is None

    def test_initialize(self, vosk_engine):
        """Can initialize Vosk engine."""
        assert vosk_engine.initialize() is True
        assert vosk_engine.is_initialized is True

    def test_supported_languages(self, vosk_engine):
        """Vosk supports multiple languages."""
        vosk_engine.initialize()
        languages = vosk_engine.get_supported_languages()
        assert "en" in languages
        assert "es" in languages

    def test_streaming(self, vosk_engine):
        """Can use streaming mode."""
        vosk_engine.initialize()
        assert vosk_engine.start_streaming() is True

        result = vosk_engine.feed_audio(b"audio")
        assert result is not None
        assert result.is_final is False

        vosk_engine.stop_streaming()


class TestCreateSTTEngine:
    """Tests for engine factory function."""

    def test_create_mock(self):
        """Can create mock engine."""
        engine = create_stt_engine("mock")
        assert isinstance(engine, MockSTTEngine)

    def test_create_whisper(self):
        """Can create Whisper engine."""
        engine = create_stt_engine("whisper", model_size="small")
        assert isinstance(engine, WhisperEngine)
        assert engine.model_size == "small"

    def test_create_vosk(self):
        """Can create Vosk engine."""
        engine = create_stt_engine("vosk", model_path="/path/to/model")
        assert isinstance(engine, VoskEngine)
        assert engine.model_path == "/path/to/model"

    def test_create_unknown_defaults_to_mock(self):
        """Unknown engine type defaults to mock."""
        engine = create_stt_engine("unknown")
        assert isinstance(engine, MockSTTEngine)

    def test_case_insensitive(self):
        """Engine type is case insensitive."""
        engine = create_stt_engine("WHISPER")
        assert isinstance(engine, WhisperEngine)

        engine = create_stt_engine("Vosk")
        assert isinstance(engine, VoskEngine)
