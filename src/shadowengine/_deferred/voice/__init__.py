"""
Voice Input System - Phase 6: STT & Real-Time Input

This module provides speech-to-text integration, natural language intent parsing,
voice command vocabulary, and real-time input handling for the ShadowEngine.

Key Components:
- STTEngine: Abstract interface for speech-to-text backends
- IntentParser: Enhanced NLP for natural language understanding
- VoiceCommands: Voice command vocabulary and quick commands
- RealtimeHandler: Real-time input management with threat response
- VoiceConfig: Configuration for voice input system
"""

from .stt import (
    STTEngine, STTResult, STTStatus,
    WhisperEngine, VoskEngine, MockSTTEngine,
    create_stt_engine
)
from .intent import (
    Intent, IntentType, IntentConfidence,
    IntentParser, EntityExtractor, NLUResult
)
from .commands import (
    VoiceCommand, CommandCategory, QuickCommand,
    VoiceVocabulary, CommandMatcher
)
from .realtime import (
    InputMode, InputEvent, InputPriority,
    RealtimeHandler, ThreatResponseManager, InputQueue
)
from .config import (
    VoiceConfig, STTConfig, InputConfig,
    WakeWordConfig, AccessibilityConfig
)

__all__ = [
    # STT
    'STTEngine', 'STTResult', 'STTStatus',
    'WhisperEngine', 'VoskEngine', 'MockSTTEngine',
    'create_stt_engine',
    # Intent
    'Intent', 'IntentType', 'IntentConfidence',
    'IntentParser', 'EntityExtractor', 'NLUResult',
    # Commands
    'VoiceCommand', 'CommandCategory', 'QuickCommand',
    'VoiceVocabulary', 'CommandMatcher',
    # Realtime
    'InputMode', 'InputEvent', 'InputPriority',
    'RealtimeHandler', 'ThreatResponseManager', 'InputQueue',
    # Config
    'VoiceConfig', 'STTConfig', 'InputConfig',
    'WakeWordConfig', 'AccessibilityConfig',
]
