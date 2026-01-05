"""
Pytest fixtures for voice module tests.
"""

import pytest
from src.shadowengine.voice.stt import (
    MockSTTEngine, STTResult, WhisperEngine, VoskEngine
)
from src.shadowengine.voice.intent import (
    IntentParser, EntityExtractor, Intent, IntentType
)
from src.shadowengine.voice.commands import (
    VoiceVocabulary, CommandMatcher, VoiceCommand, QuickCommand, CommandCategory
)
from src.shadowengine.voice.realtime import (
    RealtimeHandler, InputQueue, InputEvent, InputPriority, ThreatResponseManager
)
from src.shadowengine.voice.config import (
    VoiceConfig, STTConfig, InputConfig, WakeWordConfig, AccessibilityConfig,
    STTEngineType, WakeWordMode
)


# === STT Engine Fixtures ===

@pytest.fixture
def mock_stt():
    """Create mock STT engine."""
    engine = MockSTTEngine()
    engine.initialize()
    return engine


@pytest.fixture
def mock_stt_with_responses():
    """Create mock STT engine with predefined responses."""
    engine = MockSTTEngine()
    engine.initialize()
    engine.set_responses([
        ("look at the desk", 0.95),
        ("go north", 0.90),
        ("attack the guard", 0.88),
    ])
    return engine


@pytest.fixture
def whisper_engine():
    """Create Whisper engine (not fully functional without model)."""
    return WhisperEngine()


@pytest.fixture
def vosk_engine():
    """Create Vosk engine (not fully functional without model)."""
    return VoskEngine()


# === Intent Parser Fixtures ===

@pytest.fixture
def intent_parser():
    """Create intent parser."""
    return IntentParser()


@pytest.fixture
def entity_extractor():
    """Create entity extractor."""
    return EntityExtractor()


@pytest.fixture
def game_context():
    """Create game context for intent parsing."""
    return {
        "targets": ["desk", "door", "key", "guard", "bartender"],
        "hotspots": [
            {"label": "Desk", "type": "object"},
            {"label": "Guard", "type": "person"},
            {"label": "North Exit", "type": "exit"},
        ],
        "last_target": "guard",
        "player_position": (5, 5),
    }


# === Voice Command Fixtures ===

@pytest.fixture
def vocabulary():
    """Create voice vocabulary."""
    return VoiceVocabulary()


@pytest.fixture
def command_matcher(vocabulary):
    """Create command matcher."""
    return CommandMatcher(vocabulary)


@pytest.fixture
def custom_command():
    """Create a custom voice command."""
    return VoiceCommand(
        name="custom_action",
        intent_type=IntentType.INTERACT,
        category=CommandCategory.CONTEXTUAL,
        phrases=["do the thing", "activate"],
        description="Custom test action",
        requires_target=True,
        examples=["do the thing now"],
    )


# === Real-Time Handler Fixtures ===

@pytest.fixture
def input_queue():
    """Create input queue."""
    return InputQueue()


@pytest.fixture
def threat_manager():
    """Create threat response manager."""
    return ThreatResponseManager()


@pytest.fixture
def realtime_handler(mock_stt):
    """Create real-time handler with mock STT."""
    return RealtimeHandler(stt_engine=mock_stt)


@pytest.fixture
def realtime_handler_no_stt():
    """Create real-time handler without STT."""
    return RealtimeHandler()


# === Config Fixtures ===

@pytest.fixture
def default_config():
    """Create default voice config."""
    return VoiceConfig()


@pytest.fixture
def voice_primary_config():
    """Create voice-primary config."""
    return VoiceConfig.voice_primary()


@pytest.fixture
def keyboard_only_config():
    """Create keyboard-only config."""
    return VoiceConfig.keyboard_only()


@pytest.fixture
def hybrid_config():
    """Create hybrid config."""
    return VoiceConfig.hybrid()


@pytest.fixture
def accessibility_config():
    """Create accessibility-focused config."""
    return VoiceConfig.accessibility_focused()


# === Helper Fixtures ===

@pytest.fixture
def sample_stt_result():
    """Create sample STT result."""
    return STTResult(
        text="look at the desk",
        confidence=0.95,
        duration_ms=500,
        language="en",
    )


@pytest.fixture
def sample_input_event():
    """Create sample input event."""
    return InputEvent(
        raw_text="examine the painting",
        priority=InputPriority.NORMAL,
    )


@pytest.fixture
def urgent_input_event():
    """Create urgent input event."""
    return InputEvent(
        raw_text="run away!",
        priority=InputPriority.CRITICAL,
    )
