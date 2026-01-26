"""
TTS Engine System - Text-to-speech synthesis backends.

Provides a unified interface for multiple TTS engines with
fallback support and mock implementation for testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import hashlib
import logging
import time

logger = logging.getLogger(__name__)

from .voice import CharacterVoice, VoiceParameters


class TTSEngineType(Enum):
    """Available TTS engine types."""
    MOCK = "mock"
    COQUI = "coqui"
    PIPER = "piper"
    SYSTEM = "system"  # OS built-in TTS


class AudioFormat(Enum):
    """Output audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    RAW = "raw"  # Raw PCM data


@dataclass
class AudioData:
    """
    Container for synthesized audio data.

    Represents the output of TTS synthesis with metadata.
    """
    # Audio content
    data: bytes
    format: AudioFormat = AudioFormat.WAV

    # Audio properties
    sample_rate: int = 22050
    channels: int = 1
    bit_depth: int = 16

    # Metadata
    duration_ms: int = 0
    text: str = ""
    voice_id: str = ""

    # Generation info
    engine: str = ""
    generation_time_ms: int = 0

    def __post_init__(self):
        """Estimate duration if not provided."""
        if self.duration_ms == 0 and self.data:
            # Estimate from data size
            bytes_per_sample = self.bit_depth // 8
            samples = len(self.data) // (bytes_per_sample * self.channels)
            self.duration_ms = int((samples / self.sample_rate) * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata (not audio data)."""
        return {
            'format': self.format.value,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bit_depth': self.bit_depth,
            'duration_ms': self.duration_ms,
            'text': self.text,
            'voice_id': self.voice_id,
            'engine': self.engine,
            'generation_time_ms': self.generation_time_ms
        }


@dataclass
class TTSRequest:
    """Request for TTS synthesis."""
    text: str
    voice: CharacterVoice
    format: AudioFormat = AudioFormat.WAV

    # Optional overrides
    speed_override: Optional[float] = None
    pitch_override: Optional[float] = None

    # SSML support
    use_ssml: bool = False
    ssml_tags: Dict[str, str] = field(default_factory=dict)

    def get_effective_params(self) -> VoiceParameters:
        """Get parameters with any overrides applied."""
        params = self.voice.get_effective_params()

        if self.speed_override is not None:
            params.speed = self.speed_override
        if self.pitch_override is not None:
            params.pitch = self.pitch_override

        return params

    def get_cache_key(self) -> str:
        """Generate cache key for this request."""
        params = self.get_effective_params()
        key_data = f"{self.text}:{self.voice.character_id}:{params.to_dict()}:{self.format.value}"
        return hashlib.md5(key_data.encode()).hexdigest()


class TTSEngine(ABC):
    """
    Abstract base class for TTS engines.

    All TTS backends must implement this interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize engine with optional configuration."""
        self.config = config or {}
        self._initialized = False

    @property
    @abstractmethod
    def engine_type(self) -> TTSEngineType:
        """Return the engine type identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the engine.

        Returns True if successful, False otherwise.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and ready."""

    @abstractmethod
    def synthesize(self, request: TTSRequest) -> AudioData:
        """
        Synthesize speech from text.

        Args:
            request: TTS request with text and voice parameters

        Returns:
            AudioData containing synthesized speech
        """

    @abstractmethod
    def get_supported_formats(self) -> List[AudioFormat]:
        """Return list of supported output formats."""

    def shutdown(self) -> None:
        """Clean up engine resources."""
        self._initialized = False


class MockTTSEngine(TTSEngine):
    """
    Mock TTS engine for testing.

    Generates predictable audio data based on text length
    without actual speech synthesis.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._synthesis_count = 0
        self._last_request: Optional[TTSRequest] = None
        self._failure_mode = False
        self._latency_ms = config.get('latency_ms', 10) if config else 10

    @property
    def engine_type(self) -> TTSEngineType:
        return TTSEngineType.MOCK

    @property
    def name(self) -> str:
        return "Mock TTS Engine"

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def is_available(self) -> bool:
        return self._initialized and not self._failure_mode

    def set_failure_mode(self, enabled: bool) -> None:
        """Enable/disable failure mode for testing error handling."""
        self._failure_mode = enabled

    def synthesize(self, request: TTSRequest) -> AudioData:
        """Generate mock audio data."""
        if self._failure_mode:
            raise TTSEngineError("Mock engine in failure mode")

        if not self._initialized:
            raise TTSEngineError("Engine not initialized")

        start_time = time.time()

        # Simulate latency
        if self._latency_ms > 0:
            time.sleep(self._latency_ms / 1000.0)

        # Calculate mock audio duration based on text
        # Approximate: 150 words per minute = 2.5 words per second
        # Average word length ~5 chars, so ~12.5 chars per second
        words = len(request.text.split())
        duration_ms = int((words / 2.5) * 1000)
        duration_ms = max(100, duration_ms)  # Minimum 100ms

        # Apply speed modifier
        params = request.get_effective_params()
        speed_factor = 0.5 + params.speed  # 0.5x to 1.5x
        duration_ms = int(duration_ms / speed_factor)

        # Generate mock audio bytes
        # 22050 Hz, 16-bit mono = 44100 bytes per second
        sample_rate = 22050
        bytes_per_second = sample_rate * 2  # 16-bit = 2 bytes
        num_bytes = int((duration_ms / 1000.0) * bytes_per_second)

        # Create deterministic mock data based on text hash
        text_hash = hashlib.md5(request.text.encode()).digest()
        mock_data = (text_hash * ((num_bytes // 16) + 1))[:num_bytes]

        self._synthesis_count += 1
        self._last_request = request

        generation_time = int((time.time() - start_time) * 1000)

        return AudioData(
            data=mock_data,
            format=request.format,
            sample_rate=sample_rate,
            channels=1,
            bit_depth=16,
            duration_ms=duration_ms,
            text=request.text,
            voice_id=request.voice.character_id,
            engine=self.name,
            generation_time_ms=generation_time
        )

    def get_supported_formats(self) -> List[AudioFormat]:
        return [AudioFormat.WAV, AudioFormat.RAW]

    # Test helpers
    @property
    def synthesis_count(self) -> int:
        """Number of synthesis calls made."""
        return self._synthesis_count

    @property
    def last_request(self) -> Optional[TTSRequest]:
        """Last synthesis request received."""
        return self._last_request

    def reset_stats(self) -> None:
        """Reset test statistics."""
        self._synthesis_count = 0
        self._last_request = None


class TTSEngineError(Exception):
    """Exception raised by TTS engines."""


class TTSEngineManager:
    """
    Manages multiple TTS engines with fallback support.

    Provides a unified interface and handles engine selection,
    caching, and error recovery.
    """

    def __init__(self):
        self._engines: Dict[TTSEngineType, TTSEngine] = {}
        self._primary_engine: Optional[TTSEngineType] = None
        self._fallback_order: List[TTSEngineType] = []
        self._cache: Dict[str, AudioData] = {}
        self._cache_enabled = True
        self._max_cache_size = 100

    def register_engine(
        self,
        engine: TTSEngine,
        set_primary: bool = False
    ) -> None:
        """
        Register a TTS engine.

        Args:
            engine: Engine instance to register
            set_primary: If True, set as primary engine
        """
        engine_type = engine.engine_type
        self._engines[engine_type] = engine

        if set_primary or self._primary_engine is None:
            self._primary_engine = engine_type

        if engine_type not in self._fallback_order:
            self._fallback_order.append(engine_type)

    def set_primary_engine(self, engine_type: TTSEngineType) -> bool:
        """Set the primary engine type."""
        if engine_type in self._engines:
            self._primary_engine = engine_type
            return True
        return False

    def set_fallback_order(self, order: List[TTSEngineType]) -> None:
        """Set the fallback order for engines."""
        self._fallback_order = [t for t in order if t in self._engines]

    def get_engine(self, engine_type: TTSEngineType) -> Optional[TTSEngine]:
        """Get a specific engine by type."""
        return self._engines.get(engine_type)

    def get_available_engines(self) -> List[TTSEngine]:
        """Get list of available engines."""
        return [e for e in self._engines.values() if e.is_available()]

    def initialize_all(self) -> Dict[TTSEngineType, bool]:
        """
        Initialize all registered engines.

        Returns dict mapping engine type to success status.
        """
        results = {}
        for engine_type, engine in self._engines.items():
            try:
                results[engine_type] = engine.initialize()
            except Exception as e:
                logger.error("Failed to initialize TTS engine %s: %s", engine_type.name, e)
                results[engine_type] = False
        return results

    def synthesize(
        self,
        request: TTSRequest,
        use_cache: bool = True
    ) -> AudioData:
        """
        Synthesize speech using available engines.

        Tries primary engine first, then fallbacks.

        Args:
            request: TTS request
            use_cache: Whether to use cached results

        Returns:
            Synthesized audio data

        Raises:
            TTSEngineError: If all engines fail
        """
        # Check cache
        if use_cache and self._cache_enabled:
            cache_key = request.get_cache_key()
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Try engines in order
        errors = []

        # Primary first
        if self._primary_engine:
            engine = self._engines.get(self._primary_engine)
            if engine and engine.is_available():
                try:
                    result = engine.synthesize(request)
                    self._cache_result(request, result)
                    return result
                except Exception as e:
                    errors.append(f"{engine.name}: {e}")

        # Then fallbacks
        for engine_type in self._fallback_order:
            if engine_type == self._primary_engine:
                continue

            engine = self._engines.get(engine_type)
            if engine and engine.is_available():
                try:
                    result = engine.synthesize(request)
                    self._cache_result(request, result)
                    return result
                except Exception as e:
                    errors.append(f"{engine.name}: {e}")

        raise TTSEngineError(f"All TTS engines failed: {'; '.join(errors)}")

    def _cache_result(self, request: TTSRequest, result: AudioData) -> None:
        """Cache a synthesis result."""
        if not self._cache_enabled:
            return

        cache_key = request.get_cache_key()

        # Evict oldest if at capacity
        if len(self._cache) >= self._max_cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[cache_key] = result

    def clear_cache(self) -> None:
        """Clear the synthesis cache."""
        self._cache.clear()

    def set_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable caching."""
        self._cache_enabled = enabled

    def shutdown_all(self) -> None:
        """Shutdown all engines."""
        for engine in self._engines.values():
            try:
                engine.shutdown()
            except Exception as e:
                logger.error("Error shutting down TTS engine %s: %s", engine.name, e)


# Placeholder implementations for real engines

class CoquiTTSEngine(TTSEngine):
    """
    Coqui TTS engine implementation.

    Note: Requires coqui-ai TTS package to be installed.
    This is a stub that can be expanded when the package is available.
    """

    @property
    def engine_type(self) -> TTSEngineType:
        return TTSEngineType.COQUI

    @property
    def name(self) -> str:
        return "Coqui TTS"

    def initialize(self) -> bool:
        # Check if TTS package is available
        try:
            import TTS  # noqa: F401
            self._initialized = True
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._initialized

    def synthesize(self, request: TTSRequest) -> AudioData:
        if not self._initialized:
            raise TTSEngineError("Coqui TTS not initialized")

        # Placeholder - actual implementation would use TTS library
        raise TTSEngineError("Coqui TTS synthesis not implemented")

    def get_supported_formats(self) -> List[AudioFormat]:
        return [AudioFormat.WAV, AudioFormat.MP3]


class PiperTTSEngine(TTSEngine):
    """
    Piper TTS engine implementation.

    Note: Requires piper-tts package to be installed.
    This is a stub that can be expanded when the package is available.
    """

    @property
    def engine_type(self) -> TTSEngineType:
        return TTSEngineType.PIPER

    @property
    def name(self) -> str:
        return "Piper TTS"

    def initialize(self) -> bool:
        # Check if piper is available
        try:
            import piper  # noqa: F401
            self._initialized = True
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._initialized

    def synthesize(self, request: TTSRequest) -> AudioData:
        if not self._initialized:
            raise TTSEngineError("Piper TTS not initialized")

        # Placeholder - actual implementation would use piper library
        raise TTSEngineError("Piper TTS synthesis not implemented")

    def get_supported_formats(self) -> List[AudioFormat]:
        return [AudioFormat.WAV, AudioFormat.RAW]
