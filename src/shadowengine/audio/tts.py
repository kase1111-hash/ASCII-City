"""
Text-to-Speech Engine for ShadowEngine.

Provides TTS synthesis with multiple backend support including
Coqui TTS, Piper, and mock engine for testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
import time


class TTSStatus(Enum):
    """Status of TTS engine."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    SYNTHESIZING = "synthesizing"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class TTSConfig:
    """Configuration for TTS engine."""

    # Engine settings
    model_name: str = "default"
    sample_rate: int = 22050
    use_cuda: bool = False

    # Voice defaults
    default_speed: float = 1.0
    default_pitch: float = 1.0

    # Caching
    cache_enabled: bool = True
    cache_max_size: int = 100  # MB

    # Quality
    quality: str = "medium"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "sample_rate": self.sample_rate,
            "use_cuda": self.use_cuda,
            "default_speed": self.default_speed,
            "default_pitch": self.default_pitch,
            "cache_enabled": self.cache_enabled,
            "cache_max_size": self.cache_max_size,
            "quality": self.quality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TTSConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TTSResult:
    """Result of TTS synthesis."""

    # Audio data
    audio_data: bytes = b""
    sample_rate: int = 22050
    duration_ms: float = 0.0

    # Metadata
    text: str = ""
    voice_id: str = ""
    cached: bool = False

    # Processing info
    synthesis_time_ms: float = 0.0

    @property
    def is_empty(self) -> bool:
        """Check if result is empty."""
        return len(self.audio_data) == 0

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding audio data)."""
        return {
            "sample_rate": self.sample_rate,
            "duration_ms": self.duration_ms,
            "text": self.text,
            "voice_id": self.voice_id,
            "cached": self.cached,
            "synthesis_time_ms": self.synthesis_time_ms,
            "audio_size_bytes": len(self.audio_data),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], audio_data: bytes = b"") -> 'TTSResult':
        """Create from dictionary."""
        return cls(
            audio_data=audio_data,
            sample_rate=data.get("sample_rate", 22050),
            duration_ms=data.get("duration_ms", 0.0),
            text=data.get("text", ""),
            voice_id=data.get("voice_id", ""),
            cached=data.get("cached", False),
            synthesis_time_ms=data.get("synthesis_time_ms", 0.0),
        )


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._status = TTSStatus.UNINITIALIZED
        self._is_initialized = False
        self._callbacks: List[Callable[[TTSResult], None]] = []
        self._cache: Dict[str, TTSResult] = {}

    @property
    def status(self) -> TTSStatus:
        """Get current status."""
        return self._status

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._is_initialized

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the TTS engine."""

    @abstractmethod
    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   speed: float = 1.0, pitch: float = 1.0) -> TTSResult:
        """Synthesize speech from text."""

    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Get list of available voice IDs."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the TTS engine."""

    def on_result(self, callback: Callable[[TTSResult], None]) -> None:
        """Register a callback for synthesis results."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, result: TTSResult) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            callback(result)

    def _get_cache_key(self, text: str, voice_id: str, speed: float, pitch: float) -> str:
        """Generate cache key for synthesis."""
        return f"{text}_{voice_id}_{speed}_{pitch}"

    def _check_cache(self, text: str, voice_id: str, speed: float, pitch: float) -> Optional[TTSResult]:
        """Check cache for existing synthesis."""
        if not self.config.cache_enabled:
            return None
        key = self._get_cache_key(text, voice_id, speed, pitch)
        result = self._cache.get(key)
        if result:
            result.cached = True
        return result

    def _store_cache(self, text: str, voice_id: str, speed: float, pitch: float, result: TTSResult) -> None:
        """Store synthesis result in cache."""
        if not self.config.cache_enabled:
            return
        key = self._get_cache_key(text, voice_id, speed, pitch)
        self._cache[key] = result

    def clear_cache(self) -> int:
        """Clear the synthesis cache. Returns number of items cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine information."""
        return {
            "name": self.__class__.__name__,
            "initialized": self._is_initialized,
            "status": self._status.value,
            "config": self.config.to_dict(),
            "cache_size": len(self._cache),
        }


class MockTTSEngine(TTSEngine):
    """Mock TTS engine for testing."""

    def __init__(self, config: Optional[TTSConfig] = None):
        super().__init__(config)
        self._responses: List[TTSResult] = []
        self._voices = ["default", "male_1", "male_2", "female_1", "female_2", "elder", "child"]
        self._delay_ms = 0

    def initialize(self) -> bool:
        """Initialize mock engine."""
        self._status = TTSStatus.READY
        self._is_initialized = True
        return True

    def set_response(self, audio_data: bytes = b"mock_audio", duration_ms: float = 1000.0) -> None:
        """Set the next response."""
        self._responses.append(TTSResult(
            audio_data=audio_data,
            duration_ms=duration_ms,
        ))

    def set_responses(self, responses: List[tuple]) -> None:
        """Set multiple responses (audio_data, duration_ms)."""
        for audio_data, duration_ms in responses:
            self._responses.append(TTSResult(
                audio_data=audio_data,
                duration_ms=duration_ms,
            ))

    def set_delay(self, delay_ms: int) -> None:
        """Set artificial delay for synthesis."""
        self._delay_ms = delay_ms

    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   speed: float = 1.0, pitch: float = 1.0) -> TTSResult:
        """Mock synthesis."""
        voice_id = voice_id or "default"

        # Check cache first
        cached = self._check_cache(text, voice_id, speed, pitch)
        if cached:
            self._notify_callbacks(cached)
            return cached

        # Apply delay
        if self._delay_ms > 0:
            time.sleep(self._delay_ms / 1000.0)

        self._status = TTSStatus.SYNTHESIZING
        start_time = time.time()

        # Get preset response or generate mock
        if self._responses:
            result = self._responses.pop(0)
        else:
            # Generate mock audio data based on text length
            audio_size = len(text) * 100  # Approximate bytes per char
            result = TTSResult(
                audio_data=b"x" * audio_size,
                duration_ms=len(text) * 80.0,  # ~80ms per char
            )

        result.text = text
        result.voice_id = voice_id
        result.sample_rate = self.config.sample_rate
        result.synthesis_time_ms = (time.time() - start_time) * 1000

        self._status = TTSStatus.READY
        self._store_cache(text, voice_id, speed, pitch, result)
        self._notify_callbacks(result)

        return result

    def get_available_voices(self) -> List[str]:
        """Get available mock voices."""
        return self._voices.copy()

    def add_voice(self, voice_id: str) -> None:
        """Add a mock voice."""
        if voice_id not in self._voices:
            self._voices.append(voice_id)

    def shutdown(self) -> None:
        """Shutdown mock engine."""
        self._status = TTSStatus.DISABLED
        self._is_initialized = False
        self._responses.clear()


class CoquiTTSEngine(TTSEngine):
    """Coqui TTS engine implementation (local, free)."""

    def __init__(self, config: Optional[TTSConfig] = None, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        super().__init__(config)
        self.model_name = model_name
        self._model = None
        self._voices = []

    def initialize(self) -> bool:
        """Initialize Coqui TTS engine."""
        self._status = TTSStatus.INITIALIZING

        # In a real implementation, this would load the model
        # For now, we simulate successful initialization
        self._voices = [
            "ljspeech",
            "vctk_p225",
            "vctk_p226",
            "vctk_p227",
            "vctk_p228",
        ]

        self._is_initialized = True
        self._status = TTSStatus.READY
        return True

    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   speed: float = 1.0, pitch: float = 1.0) -> TTSResult:
        """Synthesize using Coqui TTS."""
        if not self._is_initialized:
            return TTSResult(text=text)

        voice_id = voice_id or "ljspeech"

        # Check cache
        cached = self._check_cache(text, voice_id, speed, pitch)
        if cached:
            return cached

        self._status = TTSStatus.SYNTHESIZING
        start_time = time.time()

        # In a real implementation, this would call the TTS model
        # For now, generate mock audio
        audio_size = len(text) * 200
        result = TTSResult(
            audio_data=b"coqui_audio_" + (b"x" * audio_size),
            sample_rate=self.config.sample_rate,
            duration_ms=len(text) * 75.0,
            text=text,
            voice_id=voice_id,
            synthesis_time_ms=(time.time() - start_time) * 1000,
        )

        self._status = TTSStatus.READY
        self._store_cache(text, voice_id, speed, pitch, result)
        self._notify_callbacks(result)

        return result

    def get_available_voices(self) -> List[str]:
        """Get available Coqui voices."""
        return self._voices.copy()

    def load_custom_voice(self, voice_path: str, voice_id: str) -> bool:
        """Load a custom voice model."""
        # In real implementation, would load voice model from path
        self._voices.append(voice_id)
        return True

    def shutdown(self) -> None:
        """Shutdown Coqui engine."""
        self._model = None
        self._is_initialized = False
        self._status = TTSStatus.DISABLED


class PiperTTSEngine(TTSEngine):
    """Piper TTS engine implementation (fast, lightweight)."""

    def __init__(self, config: Optional[TTSConfig] = None, model_path: Optional[str] = None):
        super().__init__(config)
        self.model_path = model_path
        self._voices = []

    def initialize(self) -> bool:
        """Initialize Piper TTS engine."""
        self._status = TTSStatus.INITIALIZING

        # Simulate loading Piper model
        self._voices = [
            "en_US-lessac-medium",
            "en_US-lessac-low",
            "en_US-ljspeech-high",
            "en_GB-alan-medium",
            "de_DE-thorsten-medium",
        ]

        self._is_initialized = True
        self._status = TTSStatus.READY
        return True

    def synthesize(self, text: str, voice_id: Optional[str] = None,
                   speed: float = 1.0, pitch: float = 1.0) -> TTSResult:
        """Synthesize using Piper TTS."""
        if not self._is_initialized:
            return TTSResult(text=text)

        voice_id = voice_id or "en_US-lessac-medium"

        # Check cache
        cached = self._check_cache(text, voice_id, speed, pitch)
        if cached:
            return cached

        self._status = TTSStatus.SYNTHESIZING
        start_time = time.time()

        # Piper is faster than Coqui
        audio_size = len(text) * 180
        result = TTSResult(
            audio_data=b"piper_audio_" + (b"x" * audio_size),
            sample_rate=self.config.sample_rate,
            duration_ms=len(text) * 70.0,
            text=text,
            voice_id=voice_id,
            synthesis_time_ms=(time.time() - start_time) * 1000,
        )

        self._status = TTSStatus.READY
        self._store_cache(text, voice_id, speed, pitch, result)
        self._notify_callbacks(result)

        return result

    def get_available_voices(self) -> List[str]:
        """Get available Piper voices."""
        return self._voices.copy()

    def download_voice(self, voice_id: str) -> bool:
        """Download a voice model from Piper repository."""
        # In real implementation, would download voice
        if voice_id not in self._voices:
            self._voices.append(voice_id)
        return True

    def shutdown(self) -> None:
        """Shutdown Piper engine."""
        self._is_initialized = False
        self._status = TTSStatus.DISABLED


def create_tts_engine(engine_type: str = "mock", **kwargs) -> TTSEngine:
    """Factory function to create TTS engines.

    Args:
        engine_type: Type of engine ("mock", "coqui", "piper")
        **kwargs: Additional arguments for the specific engine

    Returns:
        Configured TTS engine
    """
    engine_type = engine_type.lower()

    config = TTSConfig(**{k: v for k, v in kwargs.items() if k in TTSConfig.__dataclass_fields__})
    engine_kwargs = {k: v for k, v in kwargs.items() if k not in TTSConfig.__dataclass_fields__}

    if engine_type == "coqui":
        return CoquiTTSEngine(config, **engine_kwargs)
    elif engine_type == "piper":
        return PiperTTSEngine(config, **engine_kwargs)
    else:
        return MockTTSEngine(config)
