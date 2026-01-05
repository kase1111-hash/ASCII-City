"""
Intent Parser - Natural Language Understanding for voice commands.

Extends the existing CommandParser with enhanced NLU capabilities
for voice input, including:
- Entity extraction (targets, quantities, directions)
- Confidence scoring
- Context-aware disambiguation
- Multi-intent detection
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import re
import uuid

from ..interaction.parser import CommandParser, Command, CommandType


class IntentType(Enum):
    """High-level intent categories for voice commands."""
    # Movement
    MOVE = "move"
    FLEE = "flee"
    APPROACH = "approach"
    FOLLOW = "follow"

    # Interaction
    EXAMINE = "examine"
    INTERACT = "interact"
    TALK = "talk"
    TAKE = "take"
    USE = "use"
    DROP = "drop"
    GIVE = "give"

    # Combat
    ATTACK = "attack"
    DEFEND = "defend"
    DODGE = "dodge"
    HIDE = "hide"

    # Social
    GREET = "greet"
    THREATEN = "threaten"
    BRIBE = "bribe"
    PERSUADE = "persuade"

    # Information
    QUERY = "query"
    INVENTORY = "inventory"
    STATUS = "status"
    HELP = "help"

    # System
    SAVE = "save"
    LOAD = "load"
    QUIT = "quit"
    PAUSE = "pause"
    SETTINGS = "settings"

    # Quick responses
    YES = "yes"
    NO = "no"
    WAIT = "wait"
    CANCEL = "cancel"

    # Unknown
    UNKNOWN = "unknown"


class IntentConfidence(Enum):
    """Confidence level for intent recognition."""
    HIGH = "high"       # > 0.8
    MEDIUM = "medium"   # 0.5 - 0.8
    LOW = "low"         # 0.3 - 0.5
    NONE = "none"       # < 0.3


@dataclass
class Entity:
    """An extracted entity from the input."""
    type: str           # person, object, direction, number, etc.
    value: str          # The actual value
    start: int = 0      # Start position in original text
    end: int = 0        # End position in original text
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "type": self.type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Deserialize from dictionary."""
        return cls(
            type=data["type"],
            value=data["value"],
            start=data.get("start", 0),
            end=data.get("end", 0),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class Intent:
    """A parsed intent from voice input."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: IntentType = IntentType.UNKNOWN
    confidence: float = 0.0
    raw_text: str = ""
    entities: list[Entity] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)
    context_used: bool = False

    @property
    def confidence_level(self) -> IntentConfidence:
        """Get confidence level category."""
        if self.confidence > 0.8:
            return IntentConfidence.HIGH
        elif self.confidence > 0.5:
            return IntentConfidence.MEDIUM
        elif self.confidence > 0.3:
            return IntentConfidence.LOW
        return IntentConfidence.NONE

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid, actionable intent."""
        return self.type != IntentType.UNKNOWN and self.confidence > 0.3

    @property
    def primary_target(self) -> Optional[str]:
        """Get the primary target entity."""
        for entity in self.entities:
            if entity.type in ("target", "person", "object", "location"):
                return entity.value
        return self.parameters.get("target")

    @property
    def direction(self) -> Optional[str]:
        """Get direction entity if present."""
        for entity in self.entities:
            if entity.type == "direction":
                return entity.value
        return self.parameters.get("direction")

    def get_entity(self, entity_type: str) -> Optional[Entity]:
        """Get first entity of given type."""
        for entity in self.entities:
            if entity.type == entity_type:
                return entity
        return None

    def get_all_entities(self, entity_type: str) -> list[Entity]:
        """Get all entities of given type."""
        return [e for e in self.entities if e.type == entity_type]

    def to_command(self) -> Command:
        """Convert intent to legacy Command for compatibility."""
        # Map intent types to command types
        intent_to_command = {
            IntentType.EXAMINE: CommandType.EXAMINE,
            IntentType.TALK: CommandType.TALK,
            IntentType.TAKE: CommandType.TAKE,
            IntentType.USE: CommandType.USE,
            IntentType.MOVE: CommandType.GO,
            IntentType.FLEE: CommandType.GO,
            IntentType.INVENTORY: CommandType.INVENTORY,
            IntentType.WAIT: CommandType.WAIT,
            IntentType.HELP: CommandType.HELP,
            IntentType.SAVE: CommandType.SAVE,
            IntentType.LOAD: CommandType.LOAD,
            IntentType.QUIT: CommandType.QUIT,
            IntentType.THREATEN: CommandType.THREATEN,
        }

        cmd_type = intent_to_command.get(self.type, CommandType.UNKNOWN)

        return Command(
            command_type=cmd_type,
            target=self.primary_target,
            secondary=self.parameters.get("secondary"),
            raw_input=self.raw_text,
            hotspot_number=self.parameters.get("hotspot_number"),
            topic=self.parameters.get("topic"),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "confidence": self.confidence,
            "raw_text": self.raw_text,
            "entities": [e.to_dict() for e in self.entities],
            "parameters": self.parameters,
            "context_used": self.context_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Intent":
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=IntentType(data.get("type", "unknown")),
            confidence=data.get("confidence", 0.0),
            raw_text=data.get("raw_text", ""),
            entities=[Entity.from_dict(e) for e in data.get("entities", [])],
            parameters=data.get("parameters", {}),
            context_used=data.get("context_used", False),
        )


@dataclass
class NLUResult:
    """Result from natural language understanding."""
    primary_intent: Intent
    secondary_intents: list[Intent] = field(default_factory=list)
    ambiguous: bool = False
    suggestions: list[str] = field(default_factory=list)
    processing_time_ms: int = 0

    @property
    def has_multiple_intents(self) -> bool:
        """Check if multiple intents were detected."""
        return len(self.secondary_intents) > 0

    @property
    def needs_clarification(self) -> bool:
        """Check if clarification is needed."""
        return (
            self.ambiguous or
            self.primary_intent.confidence_level == IntentConfidence.LOW
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "primary_intent": self.primary_intent.to_dict(),
            "secondary_intents": [i.to_dict() for i in self.secondary_intents],
            "ambiguous": self.ambiguous,
            "suggestions": self.suggestions,
            "processing_time_ms": self.processing_time_ms,
        }


class EntityExtractor:
    """
    Extracts entities from natural language text.

    Identifies targets, directions, quantities, and other
    semantic components of voice commands.
    """

    def __init__(self):
        # Direction patterns
        self.directions = {
            "north", "south", "east", "west",
            "northeast", "northwest", "southeast", "southwest",
            "up", "down", "left", "right",
            "forward", "backward", "back",
            "n", "s", "e", "w", "ne", "nw", "se", "sw", "u", "d"
        }

        # Direction word mappings
        self.direction_aliases = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "ne": "northeast", "nw": "northwest",
            "se": "southeast", "sw": "southwest",
            "u": "up", "d": "down",
            "forward": "north", "backward": "south", "back": "south",
        }

        # Quantity words
        self.quantity_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "all": -1, "every": -1, "everything": -1,
        }

        # Preposition patterns for target extraction
        self.target_prepositions = {"at", "to", "with", "on", "the", "a", "an"}

        # Pronouns that might refer to context
        self.pronouns = {"it", "them", "that", "this", "him", "her", "they"}

    def extract(self, text: str, context: dict = None) -> list[Entity]:
        """
        Extract all entities from text.

        Args:
            text: Input text
            context: Optional context with known targets, etc.

        Returns:
            List of extracted entities
        """
        context = context or {}
        entities = []
        text_lower = text.lower()
        words = text_lower.split()

        # Extract directions
        entities.extend(self._extract_directions(text_lower, words))

        # Extract numbers and quantities
        entities.extend(self._extract_quantities(text_lower, words))

        # Extract targets
        entities.extend(self._extract_targets(text_lower, words, context))

        # Extract pronouns (may need context resolution)
        entities.extend(self._extract_pronouns(text_lower, words, context))

        return entities

    def _extract_directions(self, text: str, words: list[str]) -> list[Entity]:
        """Extract direction entities."""
        entities = []

        for i, word in enumerate(words):
            if word in self.directions:
                direction = self.direction_aliases.get(word, word)
                start = text.find(word)
                entities.append(Entity(
                    type="direction",
                    value=direction,
                    start=start,
                    end=start + len(word),
                    confidence=0.95,
                ))

        return entities

    def _extract_quantities(self, text: str, words: list[str]) -> list[Entity]:
        """Extract numeric and quantity entities."""
        entities = []

        # Check for numeric words
        for i, word in enumerate(words):
            if word in self.quantity_words:
                start = text.find(word)
                entities.append(Entity(
                    type="quantity",
                    value=str(self.quantity_words[word]),
                    start=start,
                    end=start + len(word),
                    confidence=0.95,
                ))

        # Check for digit numbers
        for match in re.finditer(r'\b(\d+)\b', text):
            entities.append(Entity(
                type="number",
                value=match.group(1),
                start=match.start(),
                end=match.end(),
                confidence=1.0,
            ))

        return entities

    def _extract_targets(self, text: str, words: list[str], context: dict) -> list[Entity]:
        """Extract target entities (objects, people, locations)."""
        entities = []
        known_targets = context.get("targets", [])
        hotspots = context.get("hotspots", [])

        # Check against known targets
        for target in known_targets:
            target_lower = target.lower()
            if target_lower in text:
                start = text.find(target_lower)
                entities.append(Entity(
                    type="target",
                    value=target,
                    start=start,
                    end=start + len(target_lower),
                    confidence=0.95,
                ))

        # Check against hotspots
        for hotspot in hotspots:
            label = hotspot.get("label", "").lower()
            if label and label in text:
                start = text.find(label)
                hotspot_type = hotspot.get("type", "object")
                entity_type = "person" if hotspot_type == "person" else "object"
                entities.append(Entity(
                    type=entity_type,
                    value=hotspot.get("label"),
                    start=start,
                    end=start + len(label),
                    confidence=0.9,
                ))

        # If no known targets, try to extract noun phrases after prepositions
        if not entities:
            entities.extend(self._extract_noun_phrases(text, words))

        return entities

    def _extract_noun_phrases(self, text: str, words: list[str]) -> list[Entity]:
        """Extract potential targets from noun phrases."""
        entities = []

        # Find words after prepositions
        for i, word in enumerate(words):
            if word in self.target_prepositions and i + 1 < len(words):
                # Get the noun phrase (up to next preposition or end)
                noun_phrase = []
                for j in range(i + 1, len(words)):
                    if words[j] in self.target_prepositions:
                        break
                    if words[j] not in {"the", "a", "an"}:
                        noun_phrase.append(words[j])

                if noun_phrase:
                    value = " ".join(noun_phrase)
                    start = text.find(value)
                    entities.append(Entity(
                        type="target",
                        value=value,
                        start=start if start >= 0 else 0,
                        end=start + len(value) if start >= 0 else len(value),
                        confidence=0.7,  # Lower confidence for inferred targets
                    ))

        return entities

    def _extract_pronouns(self, text: str, words: list[str], context: dict) -> list[Entity]:
        """Extract pronoun references."""
        entities = []

        for i, word in enumerate(words):
            if word in self.pronouns:
                # Try to resolve from context
                last_target = context.get("last_target")
                start = text.find(word)

                if last_target:
                    entities.append(Entity(
                        type="pronoun_reference",
                        value=last_target,
                        start=start,
                        end=start + len(word),
                        confidence=0.8,
                    ))
                else:
                    entities.append(Entity(
                        type="unresolved_pronoun",
                        value=word,
                        start=start,
                        end=start + len(word),
                        confidence=0.5,
                    ))

        return entities


class IntentParser:
    """
    Enhanced intent parser for natural language voice commands.

    Builds on the existing CommandParser with:
    - Confidence scoring
    - Entity extraction
    - Context-aware disambiguation
    - Multi-intent detection
    """

    def __init__(self):
        self.command_parser = CommandParser()
        self.entity_extractor = EntityExtractor()

        # Intent verb patterns
        self.intent_patterns = {
            # Movement
            IntentType.MOVE: [
                r"\b(go|walk|move|run|head|travel)\b",
                r"\b(n|s|e|w|north|south|east|west)\b",
            ],
            IntentType.FLEE: [
                r"\b(run away|flee|escape|get out|get away)\b",
            ],
            IntentType.APPROACH: [
                r"\b(approach|go to|walk to|move toward)\b",
            ],
            IntentType.FOLLOW: [
                r"\b(follow|tail|track|pursue)\b",
            ],

            # Interaction
            IntentType.EXAMINE: [
                r"\b(look|examine|inspect|check|see|view|observe|x|l)\b",
            ],
            IntentType.INTERACT: [
                r"\b(interact|touch|press|push|pull|open|close|activate)\b",
            ],
            IntentType.TALK: [
                r"\b(talk|speak|ask|say|tell|chat|converse)\b",
            ],
            IntentType.TAKE: [
                r"\b(take|get|grab|pick|collect|g)\b",
            ],
            IntentType.USE: [
                r"\b(use|apply|put|insert|combine)\b",
            ],
            IntentType.DROP: [
                r"\b(drop|leave|discard|throw away)\b",
            ],
            IntentType.GIVE: [
                r"\b(give|hand|offer|present)\b",
            ],

            # Combat
            IntentType.ATTACK: [
                r"\b(attack|hit|strike|fight|kill|stab|shoot)\b",
            ],
            IntentType.DEFEND: [
                r"\b(defend|block|parry|shield)\b",
            ],
            IntentType.DODGE: [
                r"\b(dodge|evade|duck|sidestep)\b",
            ],
            IntentType.HIDE: [
                r"\b(hide|sneak|stealth|crouch)\b",
            ],

            # Social
            IntentType.GREET: [
                r"\b(hello|hi|hey|greet|wave)\b",
            ],
            IntentType.THREATEN: [
                r"\b(threaten|intimidate|scare|menace)\b",
            ],
            IntentType.BRIBE: [
                r"\b(bribe|pay off|offer money)\b",
            ],
            IntentType.PERSUADE: [
                r"\b(persuade|convince|talk into)\b",
            ],

            # Information
            IntentType.QUERY: [
                r"\b(what|where|who|when|why|how)\b.*\?",
            ],
            IntentType.INVENTORY: [
                r"\b(inventory|items|bag|i)\b",
            ],
            IntentType.STATUS: [
                r"\b(status|health|stats|condition)\b",
            ],
            IntentType.HELP: [
                r"\b(help|\?|commands)\b",
            ],

            # System
            IntentType.SAVE: [r"\bsave\b"],
            IntentType.LOAD: [r"\bload\b"],
            IntentType.QUIT: [r"\b(quit|exit|q)\b"],
            IntentType.PAUSE: [r"\bpause\b"],
            IntentType.SETTINGS: [r"\b(settings|options|config)\b"],

            # Quick responses
            IntentType.YES: [r"\b(yes|yeah|yep|sure|ok|okay|affirmative)\b"],
            IntentType.NO: [r"\b(no|nope|nah|negative|refuse)\b"],
            IntentType.WAIT: [r"\b(wait|hold|pause|stop)\b"],
            IntentType.CANCEL: [r"\b(cancel|nevermind|abort)\b"],
        }

        # Compile patterns
        self.compiled_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.intent_patterns.items()
        }

        # Urgency indicators (boost priority for real-time response)
        self.urgency_patterns = [
            r"\b(quick|quickly|fast|now|hurry|run|flee|help)\b",
            r"!+$",
        ]
        self.compiled_urgency = [re.compile(p, re.IGNORECASE) for p in self.urgency_patterns]

    def parse(self, text: str, context: dict = None) -> NLUResult:
        """
        Parse text into structured intent.

        Args:
            text: Input text (from voice or keyboard)
            context: Optional context with known targets, hotspots, etc.

        Returns:
            NLUResult with primary intent and metadata
        """
        import time
        start_time = time.time()

        context = context or {}
        text = text.strip()

        if not text:
            return NLUResult(
                primary_intent=Intent(type=IntentType.UNKNOWN, confidence=0.0),
                processing_time_ms=0,
            )

        # Extract entities
        entities = self.entity_extractor.extract(text, context)

        # Match intent patterns
        intent_scores: dict[IntentType, float] = {}
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    current_score = intent_scores.get(intent, 0.0)
                    intent_scores[intent] = max(current_score, 0.8)

        # Check for hotspot number
        if text.isdigit():
            intent_scores[IntentType.INTERACT] = 0.95

        # If no patterns matched, use legacy parser as fallback
        if not intent_scores:
            legacy_cmd = self.command_parser.parse(text, context)
            fallback_intent = self._command_to_intent_type(legacy_cmd.command_type)
            if fallback_intent != IntentType.UNKNOWN:
                intent_scores[fallback_intent] = 0.6

        # Determine primary intent
        if intent_scores:
            primary_type = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            confidence = intent_scores[primary_type]
        else:
            primary_type = IntentType.UNKNOWN
            confidence = 0.0

        # Build primary intent
        primary_intent = Intent(
            type=primary_type,
            confidence=confidence,
            raw_text=text,
            entities=entities,
            parameters=self._extract_parameters(text, entities, context),
            context_used=bool(context.get("last_target")),
        )

        # Check for secondary intents (multi-intent)
        secondary_intents = []
        for intent_type, score in sorted(intent_scores.items(), key=lambda x: -x[1]):
            if intent_type != primary_type and score > 0.5:
                secondary_intents.append(Intent(
                    type=intent_type,
                    confidence=score,
                    raw_text=text,
                    entities=entities,
                ))

        # Check for ambiguity
        ambiguous = (
            len([s for s in intent_scores.values() if s > 0.6]) > 1 or
            confidence < 0.6
        )

        # Generate suggestions if needed
        suggestions = []
        if ambiguous:
            suggestions = self._generate_suggestions(text, intent_scores, context)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return NLUResult(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            ambiguous=ambiguous,
            suggestions=suggestions,
            processing_time_ms=processing_time_ms,
        )

    def is_urgent(self, text: str) -> bool:
        """Check if the input indicates urgency."""
        for pattern in self.compiled_urgency:
            if pattern.search(text):
                return True
        return False

    def _command_to_intent_type(self, cmd_type: CommandType) -> IntentType:
        """Convert legacy CommandType to IntentType."""
        mapping = {
            CommandType.EXAMINE: IntentType.EXAMINE,
            CommandType.TALK: IntentType.TALK,
            CommandType.TAKE: IntentType.TAKE,
            CommandType.USE: IntentType.USE,
            CommandType.GO: IntentType.MOVE,
            CommandType.INVENTORY: IntentType.INVENTORY,
            CommandType.WAIT: IntentType.WAIT,
            CommandType.HELP: IntentType.HELP,
            CommandType.SAVE: IntentType.SAVE,
            CommandType.LOAD: IntentType.LOAD,
            CommandType.QUIT: IntentType.QUIT,
            CommandType.THREATEN: IntentType.THREATEN,
            CommandType.HOTSPOT: IntentType.INTERACT,
        }
        return mapping.get(cmd_type, IntentType.UNKNOWN)

    def _extract_parameters(self, text: str, entities: list[Entity], context: dict) -> dict:
        """Extract additional parameters from text and entities."""
        params = {}

        # Extract target
        for entity in entities:
            if entity.type in ("target", "person", "object"):
                params["target"] = entity.value
                break

        # Extract direction
        for entity in entities:
            if entity.type == "direction":
                params["direction"] = entity.value
                break

        # Extract hotspot number
        if text.isdigit():
            params["hotspot_number"] = int(text)
        else:
            for entity in entities:
                if entity.type == "number":
                    params["hotspot_number"] = int(entity.value)
                    break

        # Extract quantity
        for entity in entities:
            if entity.type == "quantity":
                params["quantity"] = int(entity.value)
                break

        # Check for "use X on Y" pattern
        use_match = re.search(r"use\s+(.+?)\s+on\s+(.+)", text, re.IGNORECASE)
        if use_match:
            params["target"] = use_match.group(1).strip()
            params["secondary"] = use_match.group(2).strip()

        return params

    def _generate_suggestions(self, text: str, scores: dict, context: dict) -> list[str]:
        """Generate clarification suggestions."""
        suggestions = []
        targets = context.get("targets", [])
        hotspots = context.get("hotspots", [])

        if targets:
            suggestions.append(f"Did you mean one of: {', '.join(targets[:3])}?")

        if hotspots:
            labels = [h.get("label") for h in hotspots[:3] if h.get("label")]
            if labels:
                suggestions.append(f"Available: {', '.join(labels)}")

        if len(scores) > 1:
            top_intents = sorted(scores.keys(), key=lambda k: -scores[k])[:2]
            suggestions.append(
                f"Did you want to {top_intents[0].value} or {top_intents[1].value}?"
            )

        return suggestions
