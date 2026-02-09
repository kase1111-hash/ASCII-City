"""
Voice Configuration - Settings for voice input system.

Provides configuration classes for:
- STT engine settings
- Input mode preferences
- Wake word configuration
- Accessibility options
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class STTEngineType(Enum):
    """Available STT engine types."""
    WHISPER = "whisper"
    VOSK = "vosk"
    MOCK = "mock"
    NONE = "none"


class WakeWordMode(Enum):
    """Wake word activation modes."""
    DISABLED = "disabled"           # Always listening (not recommended)
    WAKE_WORD = "wake_word"         # Activate on wake word
    PUSH_TO_TALK = "push_to_talk"   # Activate on key press
    HYBRID = "hybrid"               # Wake word or key press


@dataclass
class STTConfig:
    """Configuration for STT engine."""
    engine_type: STTEngineType = STTEngineType.MOCK
    model_path: Optional[str] = None
    model_size: str = "base"        # For Whisper: tiny, base, small, medium, large
    device: str = "cpu"             # cpu, cuda, mps
    compute_type: str = "int8"      # int8, float16, float32
    language: str = "en"
    sample_rate: int = 16000
    chunk_size: int = 1024
    silence_threshold: float = 0.01
    silence_duration_ms: int = 500  # End of speech detection

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "engine_type": self.engine_type.value,
            "model_path": self.model_path,
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "silence_threshold": self.silence_threshold,
            "silence_duration_ms": self.silence_duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "STTConfig":
        """Deserialize from dictionary."""
        return cls(
            engine_type=STTEngineType(data.get("engine_type", "mock")),
            model_path=data.get("model_path"),
            model_size=data.get("model_size", "base"),
            device=data.get("device", "cpu"),
            compute_type=data.get("compute_type", "int8"),
            language=data.get("language", "en"),
            sample_rate=data.get("sample_rate", 16000),
            chunk_size=data.get("chunk_size", 1024),
            silence_threshold=data.get("silence_threshold", 0.01),
            silence_duration_ms=data.get("silence_duration_ms", 500),
        )


@dataclass
class WakeWordConfig:
    """Configuration for wake word activation."""
    mode: WakeWordMode = WakeWordMode.PUSH_TO_TALK
    wake_phrase: str = "hey shadow"
    alternative_phrases: list[str] = field(default_factory=lambda: ["computer", "game"])
    push_to_talk_key: str = "space"     # Key for push-to-talk
    release_delay_ms: int = 500         # Delay after key release before stopping
    sensitivity: float = 0.5            # Wake word detection sensitivity (0.0-1.0)
    timeout_ms: int = 10000             # Auto-stop after this long

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "mode": self.mode.value,
            "wake_phrase": self.wake_phrase,
            "alternative_phrases": self.alternative_phrases,
            "push_to_talk_key": self.push_to_talk_key,
            "release_delay_ms": self.release_delay_ms,
            "sensitivity": self.sensitivity,
            "timeout_ms": self.timeout_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WakeWordConfig":
        """Deserialize from dictionary."""
        return cls(
            mode=WakeWordMode(data.get("mode", "push_to_talk")),
            wake_phrase=data.get("wake_phrase", "hey shadow"),
            alternative_phrases=data.get("alternative_phrases", ["computer", "game"]),
            push_to_talk_key=data.get("push_to_talk_key", "space"),
            release_delay_ms=data.get("release_delay_ms", 500),
            sensitivity=data.get("sensitivity", 0.5),
            timeout_ms=data.get("timeout_ms", 10000),
        )


@dataclass
class InputConfig:
    """Configuration for input handling."""
    primary_mode: str = "keyboard"      # keyboard, voice, hybrid
    enable_voice: bool = False          # Voice input enabled
    enable_keyboard: bool = True        # Keyboard input enabled
    command_timeout_ms: int = 5000      # Timeout for incomplete commands
    urgent_response_window_ms: int = 2000  # Time to respond to threats
    fuzzy_match_threshold: float = 0.7  # Minimum confidence for fuzzy matching
    max_queue_size: int = 100           # Maximum pending commands
    process_stale: bool = False         # Process stale commands

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "primary_mode": self.primary_mode,
            "enable_voice": self.enable_voice,
            "enable_keyboard": self.enable_keyboard,
            "command_timeout_ms": self.command_timeout_ms,
            "urgent_response_window_ms": self.urgent_response_window_ms,
            "fuzzy_match_threshold": self.fuzzy_match_threshold,
            "max_queue_size": self.max_queue_size,
            "process_stale": self.process_stale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InputConfig":
        """Deserialize from dictionary."""
        return cls(
            primary_mode=data.get("primary_mode", "keyboard"),
            enable_voice=data.get("enable_voice", False),
            enable_keyboard=data.get("enable_keyboard", True),
            command_timeout_ms=data.get("command_timeout_ms", 5000),
            urgent_response_window_ms=data.get("urgent_response_window_ms", 2000),
            fuzzy_match_threshold=data.get("fuzzy_match_threshold", 0.7),
            max_queue_size=data.get("max_queue_size", 100),
            process_stale=data.get("process_stale", False),
        )


@dataclass
class AccessibilityConfig:
    """Accessibility configuration for voice input."""
    # Visual feedback
    show_voice_indicator: bool = True       # Show when listening
    show_transcription: bool = True         # Show real-time transcription
    show_confidence: bool = False           # Show recognition confidence
    highlight_urgent: bool = True           # Highlight urgent commands

    # Audio feedback
    audio_confirmation: bool = False        # Play sound on recognition
    audio_error: bool = True                # Play sound on error

    # Text alternatives
    subtitles_enabled: bool = True          # Show all spoken content as text
    command_echo: bool = True               # Echo recognized commands

    # Timing
    extended_timeout: bool = False          # Longer timeouts for responses
    timeout_multiplier: float = 1.0         # Multiply timeouts by this

    # Input assistance
    command_suggestions: bool = True        # Show command suggestions
    autocomplete: bool = True               # Enable autocomplete
    error_recovery: bool = True             # Suggest corrections for errors

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "show_voice_indicator": self.show_voice_indicator,
            "show_transcription": self.show_transcription,
            "show_confidence": self.show_confidence,
            "highlight_urgent": self.highlight_urgent,
            "audio_confirmation": self.audio_confirmation,
            "audio_error": self.audio_error,
            "subtitles_enabled": self.subtitles_enabled,
            "command_echo": self.command_echo,
            "extended_timeout": self.extended_timeout,
            "timeout_multiplier": self.timeout_multiplier,
            "command_suggestions": self.command_suggestions,
            "autocomplete": self.autocomplete,
            "error_recovery": self.error_recovery,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccessibilityConfig":
        """Deserialize from dictionary."""
        return cls(
            show_voice_indicator=data.get("show_voice_indicator", True),
            show_transcription=data.get("show_transcription", True),
            show_confidence=data.get("show_confidence", False),
            highlight_urgent=data.get("highlight_urgent", True),
            audio_confirmation=data.get("audio_confirmation", False),
            audio_error=data.get("audio_error", True),
            subtitles_enabled=data.get("subtitles_enabled", True),
            command_echo=data.get("command_echo", True),
            extended_timeout=data.get("extended_timeout", False),
            timeout_multiplier=data.get("timeout_multiplier", 1.0),
            command_suggestions=data.get("command_suggestions", True),
            autocomplete=data.get("autocomplete", True),
            error_recovery=data.get("error_recovery", True),
        )


@dataclass
class VoiceConfig:
    """Complete voice input configuration."""
    stt: STTConfig = field(default_factory=STTConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    input: InputConfig = field(default_factory=InputConfig)
    accessibility: AccessibilityConfig = field(default_factory=AccessibilityConfig)

    # Presets
    @classmethod
    def keyboard_only(cls) -> "VoiceConfig":
        """Create keyboard-only configuration."""
        return cls(
            stt=STTConfig(engine_type=STTEngineType.NONE),
            input=InputConfig(
                primary_mode="keyboard",
                enable_voice=False,
                enable_keyboard=True,
            ),
        )

    @classmethod
    def voice_primary(cls) -> "VoiceConfig":
        """Create voice-primary configuration."""
        return cls(
            stt=STTConfig(
                engine_type=STTEngineType.WHISPER,
                model_size="base",
            ),
            wake_word=WakeWordConfig(mode=WakeWordMode.PUSH_TO_TALK),
            input=InputConfig(
                primary_mode="voice",
                enable_voice=True,
                enable_keyboard=True,
            ),
        )

    @classmethod
    def hybrid(cls) -> "VoiceConfig":
        """Create hybrid voice+keyboard configuration."""
        return cls(
            stt=STTConfig(
                engine_type=STTEngineType.VOSK,  # Faster for hybrid
            ),
            wake_word=WakeWordConfig(mode=WakeWordMode.HYBRID),
            input=InputConfig(
                primary_mode="hybrid",
                enable_voice=True,
                enable_keyboard=True,
            ),
        )

    @classmethod
    def accessibility_focused(cls) -> "VoiceConfig":
        """Create accessibility-focused configuration."""
        return cls(
            stt=STTConfig(
                engine_type=STTEngineType.WHISPER,
                model_size="small",  # Better accuracy
            ),
            wake_word=WakeWordConfig(
                mode=WakeWordMode.PUSH_TO_TALK,
                release_delay_ms=1000,  # Longer release delay
            ),
            input=InputConfig(
                primary_mode="hybrid",
                enable_voice=True,
                enable_keyboard=True,
                command_timeout_ms=10000,  # Longer timeout
            ),
            accessibility=AccessibilityConfig(
                extended_timeout=True,
                timeout_multiplier=2.0,
                command_suggestions=True,
                error_recovery=True,
            ),
        )

    def validate(self) -> list[str]:
        """
        Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check STT engine availability
        if self.input.enable_voice and self.stt.engine_type == STTEngineType.NONE:
            errors.append("Voice enabled but no STT engine configured")

        # Check wake word settings
        if self.wake_word.mode == WakeWordMode.WAKE_WORD:
            if not self.wake_word.wake_phrase:
                errors.append("Wake word mode requires wake phrase")

        # Check input settings
        if not self.input.enable_voice and not self.input.enable_keyboard:
            errors.append("At least one input method must be enabled")

        if self.input.fuzzy_match_threshold < 0 or self.input.fuzzy_match_threshold > 1:
            errors.append("Fuzzy match threshold must be between 0 and 1")

        # Check accessibility settings
        if self.accessibility.timeout_multiplier <= 0:
            errors.append("Timeout multiplier must be positive")

        return errors

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "stt": self.stt.to_dict(),
            "wake_word": self.wake_word.to_dict(),
            "input": self.input.to_dict(),
            "accessibility": self.accessibility.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceConfig":
        """Deserialize from dictionary."""
        return cls(
            stt=STTConfig.from_dict(data.get("stt", {})),
            wake_word=WakeWordConfig.from_dict(data.get("wake_word", {})),
            input=InputConfig.from_dict(data.get("input", {})),
            accessibility=AccessibilityConfig.from_dict(data.get("accessibility", {})),
        )
