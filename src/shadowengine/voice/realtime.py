"""
Real-Time Input Handler - Fast input processing with threat response.

Manages input from voice and keyboard sources with priority handling
for urgent commands (combat, fleeing) and real-time threat response.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
from datetime import datetime
import uuid
import time
import threading
import queue

from .stt import STTEngine, STTResult, STTStatus
from .intent import IntentParser, Intent, IntentType, NLUResult
from .commands import VoiceVocabulary, CommandMatcher


class InputMode(Enum):
    """Current input mode."""
    KEYBOARD = "keyboard"
    VOICE = "voice"
    HYBRID = "hybrid"       # Both enabled, voice primary
    DISABLED = "disabled"


class InputPriority(Enum):
    """Priority levels for input processing."""
    CRITICAL = 0    # Immediate (flee, dodge, block)
    HIGH = 1        # Combat actions
    NORMAL = 2      # Regular commands
    LOW = 3         # System commands (save, settings)
    BACKGROUND = 4  # Non-urgent queries


@dataclass
class InputEvent:
    """An input event from any source."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: InputMode = InputMode.KEYBOARD
    raw_text: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    priority: InputPriority = InputPriority.NORMAL
    stt_result: Optional[STTResult] = None
    nlu_result: Optional[NLUResult] = None
    processed: bool = False
    response_callback: Optional[Callable[[Any], None]] = None

    @property
    def age_ms(self) -> int:
        """Get age of event in milliseconds."""
        delta = datetime.now() - self.timestamp
        return int(delta.total_seconds() * 1000)

    @property
    def is_stale(self) -> bool:
        """Check if event is too old to process."""
        # Critical events are never stale
        if self.priority == InputPriority.CRITICAL:
            return False
        # Normal events stale after 5 seconds
        return self.age_ms > 5000

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source": self.source.value,
            "raw_text": self.raw_text,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "stt_result": self.stt_result.to_dict() if self.stt_result else None,
            "nlu_result": self.nlu_result.to_dict() if self.nlu_result else None,
            "processed": self.processed,
        }


class InputQueue:
    """
    Priority queue for input events.

    Ensures critical/urgent commands are processed first,
    even if received after lower-priority commands.
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._queues: dict[InputPriority, list[InputEvent]] = {
            priority: [] for priority in InputPriority
        }
        self._lock = threading.Lock()
        self._total_count = 0

    def put(self, event: InputEvent) -> bool:
        """
        Add event to queue.

        Returns:
            True if added, False if queue is full
        """
        with self._lock:
            if self._total_count >= self.max_size:
                # Drop lowest priority events if full
                for priority in reversed(list(InputPriority)):
                    if self._queues[priority]:
                        self._queues[priority].pop(0)
                        self._total_count -= 1
                        break
                else:
                    return False

            self._queues[event.priority].append(event)
            self._total_count += 1
            return True

    def get(self, block: bool = False, timeout: float = None) -> Optional[InputEvent]:
        """
        Get highest priority event.

        Args:
            block: Whether to block waiting for event
            timeout: Timeout in seconds if blocking

        Returns:
            InputEvent or None if queue is empty
        """
        start_time = time.time()

        while True:
            with self._lock:
                # Check queues in priority order
                for priority in InputPriority:
                    if self._queues[priority]:
                        event = self._queues[priority].pop(0)
                        self._total_count -= 1
                        return event

            if not block:
                return None

            if timeout and (time.time() - start_time) >= timeout:
                return None

            time.sleep(0.01)  # Small sleep to prevent busy-waiting

    def peek(self) -> Optional[InputEvent]:
        """Peek at highest priority event without removing."""
        with self._lock:
            for priority in InputPriority:
                if self._queues[priority]:
                    return self._queues[priority][0]
        return None

    def clear(self) -> int:
        """Clear all events and return count cleared."""
        with self._lock:
            count = self._total_count
            for priority in InputPriority:
                self._queues[priority].clear()
            self._total_count = 0
            return count

    def clear_stale(self) -> int:
        """Clear stale events and return count cleared."""
        count = 0
        with self._lock:
            for priority in InputPriority:
                original_len = len(self._queues[priority])
                self._queues[priority] = [
                    e for e in self._queues[priority] if not e.is_stale
                ]
                removed = original_len - len(self._queues[priority])
                count += removed
                self._total_count -= removed
        return count

    @property
    def size(self) -> int:
        """Get total queue size."""
        return self._total_count

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._total_count == 0

    def get_counts(self) -> dict[InputPriority, int]:
        """Get count per priority level."""
        with self._lock:
            return {p: len(self._queues[p]) for p in InputPriority}


class ThreatResponseManager:
    """
    Manages real-time threat response.

    Monitors for threats and ensures player can respond quickly
    with voice commands before threats reach them.
    """

    def __init__(self):
        self._active_threats: dict[str, dict] = {}
        self._response_window_ms = 2000  # Time to respond to threat
        self._threat_callbacks: list[Callable[[dict], None]] = []
        self._lock = threading.Lock()

    def register_threat(
        self,
        threat_id: str,
        threat_type: str,
        distance: float,
        speed: float = 1.0,
        source_position: tuple = (0, 0)
    ) -> float:
        """
        Register an incoming threat.

        Args:
            threat_id: Unique threat identifier
            threat_type: Type of threat (creature, projectile, etc.)
            distance: Distance to player (tiles)
            speed: Threat movement speed
            source_position: Position of threat

        Returns:
            Time until impact (milliseconds)
        """
        # Calculate time to impact
        time_to_impact_ms = int((distance / max(speed, 0.1)) * 1000)

        threat_data = {
            "id": threat_id,
            "type": threat_type,
            "distance": distance,
            "speed": speed,
            "position": source_position,
            "registered_at": datetime.now(),
            "time_to_impact_ms": time_to_impact_ms,
            "responded": False,
        }

        with self._lock:
            self._active_threats[threat_id] = threat_data

        # Notify callbacks
        for callback in self._threat_callbacks:
            try:
                callback(threat_data)
            except Exception:
                pass

        return time_to_impact_ms

    def respond_to_threat(self, threat_id: str, response_type: IntentType) -> bool:
        """
        Record player response to threat.

        Returns:
            True if response was in time, False otherwise
        """
        with self._lock:
            if threat_id not in self._active_threats:
                return False

            threat = self._active_threats[threat_id]
            if threat["responded"]:
                return False

            # Check if response is in time
            elapsed = (datetime.now() - threat["registered_at"]).total_seconds() * 1000
            in_time = elapsed < threat["time_to_impact_ms"]

            threat["responded"] = True
            threat["response_type"] = response_type
            threat["response_time_ms"] = elapsed
            threat["in_time"] = in_time

            return in_time

    def clear_threat(self, threat_id: str) -> bool:
        """Clear a threat from tracking."""
        with self._lock:
            if threat_id in self._active_threats:
                del self._active_threats[threat_id]
                return True
            return False

    def get_active_threats(self) -> list[dict]:
        """Get all active (unresponded) threats."""
        with self._lock:
            return [
                t for t in self._active_threats.values()
                if not t["responded"]
            ]

    def get_most_urgent_threat(self) -> Optional[dict]:
        """Get the most urgent (closest) threat."""
        threats = self.get_active_threats()
        if not threats:
            return None

        return min(threats, key=lambda t: t["time_to_impact_ms"])

    def on_threat(self, callback: Callable[[dict], None]) -> None:
        """Register callback for new threats."""
        self._threat_callbacks.append(callback)

    def clear_all(self) -> int:
        """Clear all threats and return count."""
        with self._lock:
            count = len(self._active_threats)
            self._active_threats.clear()
            return count

    @property
    def response_window(self) -> int:
        """Get response window in milliseconds."""
        return self._response_window_ms

    @response_window.setter
    def response_window(self, value: int) -> None:
        """Set response window in milliseconds."""
        self._response_window_ms = max(100, value)


class RealtimeHandler:
    """
    Real-time input handler for voice and keyboard.

    Coordinates STT, intent parsing, and command matching
    with priority handling for urgent commands.
    """

    def __init__(
        self,
        stt_engine: Optional[STTEngine] = None,
        intent_parser: Optional[IntentParser] = None,
        vocabulary: Optional[VoiceVocabulary] = None
    ):
        self.stt_engine = stt_engine
        self.intent_parser = intent_parser or IntentParser()
        self.vocabulary = vocabulary or VoiceVocabulary()
        self.command_matcher = CommandMatcher(self.vocabulary)

        self._mode = InputMode.KEYBOARD
        self._input_queue = InputQueue()
        self._threat_manager = ThreatResponseManager()

        self._event_callbacks: list[Callable[[InputEvent], None]] = []
        self._intent_callbacks: list[Callable[[Intent], None]] = []

        self._processing_thread: Optional[threading.Thread] = None
        self._running = False
        self._context: dict = {}

        # Statistics
        self._stats = {
            "total_events": 0,
            "voice_events": 0,
            "keyboard_events": 0,
            "urgent_events": 0,
            "avg_processing_ms": 0.0,
        }

    @property
    def mode(self) -> InputMode:
        """Get current input mode."""
        return self._mode

    @mode.setter
    def mode(self, value: InputMode) -> None:
        """Set input mode."""
        self._mode = value

    @property
    def input_queue(self) -> InputQueue:
        """Get input queue."""
        return self._input_queue

    @property
    def threat_manager(self) -> ThreatResponseManager:
        """Get threat response manager."""
        return self._threat_manager

    @property
    def is_running(self) -> bool:
        """Check if handler is running."""
        return self._running

    @property
    def stats(self) -> dict:
        """Get processing statistics."""
        return self._stats.copy()

    def set_context(self, context: dict) -> None:
        """Set current context for intent parsing."""
        self._context = context

    def update_context(self, updates: dict) -> None:
        """Update context with new values."""
        self._context.update(updates)

    def start(self) -> bool:
        """
        Start real-time input processing.

        Returns:
            True if started successfully
        """
        if self._running:
            return True

        self._running = True

        # Start processing thread
        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self._processing_thread.start()

        # Start STT if in voice mode
        if self._mode in (InputMode.VOICE, InputMode.HYBRID):
            if self.stt_engine and not self.stt_engine.is_initialized:
                self.stt_engine.initialize()
                self.stt_engine.on_result(self._on_stt_result)

        return True

    def stop(self) -> None:
        """Stop real-time input processing."""
        self._running = False

        if self._processing_thread:
            self._processing_thread.join(timeout=1.0)
            self._processing_thread = None

        if self.stt_engine:
            self.stt_engine.stop_streaming()

    def submit_keyboard_input(self, text: str) -> InputEvent:
        """
        Submit keyboard input for processing.

        Args:
            text: Keyboard input text

        Returns:
            Created InputEvent
        """
        priority = self._determine_priority(text)

        event = InputEvent(
            source=InputMode.KEYBOARD,
            raw_text=text,
            priority=priority,
        )

        self._input_queue.put(event)
        self._stats["total_events"] += 1
        self._stats["keyboard_events"] += 1

        if priority == InputPriority.CRITICAL:
            self._stats["urgent_events"] += 1

        return event

    def submit_voice_input(self, stt_result: STTResult) -> InputEvent:
        """
        Submit voice input for processing.

        Args:
            stt_result: STT result from voice recognition

        Returns:
            Created InputEvent
        """
        priority = self._determine_priority(stt_result.text)

        event = InputEvent(
            source=InputMode.VOICE,
            raw_text=stt_result.text,
            priority=priority,
            stt_result=stt_result,
        )

        self._input_queue.put(event)
        self._stats["total_events"] += 1
        self._stats["voice_events"] += 1

        if priority == InputPriority.CRITICAL:
            self._stats["urgent_events"] += 1

        return event

    def start_voice_capture(self) -> bool:
        """
        Start voice capture for streaming recognition.

        Returns:
            True if started successfully
        """
        if not self.stt_engine:
            return False

        if not self.stt_engine.is_initialized:
            if not self.stt_engine.initialize():
                return False

        return self.stt_engine.start_streaming()

    def stop_voice_capture(self) -> Optional[STTResult]:
        """
        Stop voice capture and get final result.

        Returns:
            Final STTResult or None
        """
        if not self.stt_engine:
            return None

        result = self.stt_engine.stop_streaming()
        if result and result.text:
            self.submit_voice_input(result)

        return result

    def process_immediate(self, text: str) -> NLUResult:
        """
        Process input immediately (bypass queue).

        Used for urgent commands that need instant processing.

        Args:
            text: Input text

        Returns:
            NLUResult from processing
        """
        return self.intent_parser.parse(text, self._context)

    def on_event(self, callback: Callable[[InputEvent], None]) -> None:
        """Register callback for input events."""
        self._event_callbacks.append(callback)

    def on_intent(self, callback: Callable[[Intent], None]) -> None:
        """Register callback for parsed intents."""
        self._intent_callbacks.append(callback)

    def _determine_priority(self, text: str) -> InputPriority:
        """Determine priority level for input."""
        text_lower = text.lower().strip()

        # Critical (life-threatening)
        critical_patterns = [
            "run", "flee", "dodge", "duck", "block", "defend",
            "escape", "hide", "help",
        ]
        for pattern in critical_patterns:
            if pattern in text_lower:
                return InputPriority.CRITICAL

        # Check if intent parser marks it as urgent
        if self.intent_parser.is_urgent(text):
            return InputPriority.CRITICAL

        # High (combat)
        high_patterns = ["attack", "fight", "strike", "shoot", "kill"]
        for pattern in high_patterns:
            if pattern in text_lower:
                return InputPriority.HIGH

        # Low (system)
        low_patterns = ["save", "load", "settings", "options", "quit"]
        for pattern in low_patterns:
            if pattern in text_lower:
                return InputPriority.LOW

        return InputPriority.NORMAL

    def _processing_loop(self) -> None:
        """Main processing loop (runs in background thread)."""
        while self._running:
            # Clear stale events
            self._input_queue.clear_stale()

            # Get next event
            event = self._input_queue.get(block=True, timeout=0.1)
            if not event:
                continue

            # Process event
            start_time = time.time()
            self._process_event(event)
            processing_time = (time.time() - start_time) * 1000

            # Update stats
            self._update_avg_processing_time(processing_time)

    def _process_event(self, event: InputEvent) -> None:
        """Process a single input event."""
        try:
            # Parse intent
            nlu_result = self.intent_parser.parse(event.raw_text, self._context)
            event.nlu_result = nlu_result
            event.processed = True

            # Check for threat response
            self._check_threat_response(nlu_result.primary_intent)

            # Emit to callbacks
            for callback in self._event_callbacks:
                try:
                    callback(event)
                except Exception:
                    pass

            for callback in self._intent_callbacks:
                try:
                    callback(nlu_result.primary_intent)
                except Exception:
                    pass

            # Execute response callback if present
            if event.response_callback:
                try:
                    event.response_callback(nlu_result)
                except Exception:
                    pass

        except Exception:
            event.processed = False

    def _check_threat_response(self, intent: Intent) -> None:
        """Check if intent responds to a threat."""
        response_intents = {
            IntentType.FLEE,
            IntentType.DODGE,
            IntentType.DEFEND,
            IntentType.HIDE,
            IntentType.ATTACK,
        }

        if intent.type not in response_intents:
            return

        # Check against active threats
        urgent_threat = self._threat_manager.get_most_urgent_threat()
        if urgent_threat:
            self._threat_manager.respond_to_threat(
                urgent_threat["id"],
                intent.type
            )

    def _update_avg_processing_time(self, new_time: float) -> None:
        """Update average processing time with exponential moving average."""
        alpha = 0.1
        current_avg = self._stats["avg_processing_ms"]
        self._stats["avg_processing_ms"] = alpha * new_time + (1 - alpha) * current_avg

    def _on_stt_result(self, result: STTResult) -> None:
        """Handle STT result from voice engine."""
        if result.is_empty:
            return

        self.submit_voice_input(result)

    def get_help(self) -> str:
        """Get help text for voice commands."""
        return self.vocabulary.get_help_text()
