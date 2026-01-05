"""
Voice Command Vocabulary - Quick commands and voice shortcuts.

Provides a vocabulary of voice commands optimized for speech input,
including:
- Quick commands for common actions
- Contextual command variations
- Command aliases and shortcuts
- Fuzzy matching for voice recognition errors
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
import re

from .intent import IntentType


class CommandCategory(Enum):
    """Categories of voice commands."""
    MOVEMENT = "movement"
    COMBAT = "combat"
    INTERACTION = "interaction"
    SOCIAL = "social"
    INVENTORY = "inventory"
    SYSTEM = "system"
    QUICK_RESPONSE = "quick_response"
    CONTEXTUAL = "contextual"


@dataclass
class VoiceCommand:
    """A registered voice command."""
    name: str
    intent_type: IntentType
    category: CommandCategory
    phrases: list[str]
    description: str = ""
    requires_target: bool = False
    is_urgent: bool = False
    shortcut: Optional[str] = None
    examples: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

    def matches(self, text: str) -> tuple[bool, float]:
        """
        Check if text matches this command.

        Returns:
            Tuple of (matches, confidence)
        """
        text_lower = text.lower().strip()

        # Exact match on phrases
        for phrase in self.phrases:
            if phrase.lower() == text_lower:
                return True, 1.0
            if text_lower.startswith(phrase.lower()):
                return True, 0.9

        # Check aliases
        for alias in self.aliases:
            if alias.lower() == text_lower:
                return True, 0.95

        # Check shortcut
        if self.shortcut and self.shortcut.lower() == text_lower:
            return True, 1.0

        # Fuzzy match
        for phrase in self.phrases:
            similarity = self._string_similarity(phrase.lower(), text_lower)
            if similarity > 0.8:
                return True, similarity

        return False, 0.0

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (0.0 to 1.0)."""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # Simple word overlap for now
        words1 = set(s1.split())
        words2 = set(s2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "intent_type": self.intent_type.value,
            "category": self.category.value,
            "phrases": self.phrases,
            "description": self.description,
            "requires_target": self.requires_target,
            "is_urgent": self.is_urgent,
            "shortcut": self.shortcut,
            "examples": self.examples,
            "aliases": self.aliases,
        }


@dataclass
class QuickCommand:
    """A quick command for rapid voice input."""
    trigger: str           # Single word or short phrase
    intent_type: IntentType
    default_target: Optional[str] = None
    is_urgent: bool = False
    context_key: Optional[str] = None  # Get target from context

    def execute(self, context: dict = None) -> tuple[IntentType, Optional[str]]:
        """
        Execute quick command and resolve target.

        Returns:
            Tuple of (intent_type, resolved_target)
        """
        context = context or {}
        target = self.default_target

        if self.context_key and self.context_key in context:
            target = context[self.context_key]

        return self.intent_type, target


class VoiceVocabulary:
    """
    Voice command vocabulary manager.

    Registers and manages all voice commands for the game,
    organized by category with support for quick commands.
    """

    def __init__(self):
        self._commands: dict[str, VoiceCommand] = {}
        self._quick_commands: dict[str, QuickCommand] = {}
        self._category_index: dict[CommandCategory, list[str]] = {
            cat: [] for cat in CommandCategory
        }
        self._register_default_commands()

    def register_command(self, command: VoiceCommand) -> None:
        """Register a voice command."""
        self._commands[command.name] = command
        self._category_index[command.category].append(command.name)

    def register_quick_command(self, quick: QuickCommand) -> None:
        """Register a quick command."""
        self._quick_commands[quick.trigger.lower()] = quick

    def get_command(self, name: str) -> Optional[VoiceCommand]:
        """Get command by name."""
        return self._commands.get(name)

    def get_quick_command(self, trigger: str) -> Optional[QuickCommand]:
        """Get quick command by trigger."""
        return self._quick_commands.get(trigger.lower())

    def get_by_category(self, category: CommandCategory) -> list[VoiceCommand]:
        """Get all commands in a category."""
        return [
            self._commands[name]
            for name in self._category_index.get(category, [])
            if name in self._commands
        ]

    def get_all_commands(self) -> list[VoiceCommand]:
        """Get all registered commands."""
        return list(self._commands.values())

    def get_all_quick_commands(self) -> list[QuickCommand]:
        """Get all quick commands."""
        return list(self._quick_commands.values())

    def find_matches(self, text: str, min_confidence: float = 0.5) -> list[tuple[VoiceCommand, float]]:
        """
        Find all commands matching text.

        Returns:
            List of (command, confidence) tuples sorted by confidence
        """
        matches = []

        for command in self._commands.values():
            matched, confidence = command.matches(text)
            if matched and confidence >= min_confidence:
                matches.append((command, confidence))

        return sorted(matches, key=lambda x: -x[1])

    def is_quick_command(self, text: str) -> bool:
        """Check if text is a quick command."""
        return text.lower().strip() in self._quick_commands

    def get_help_text(self, category: Optional[CommandCategory] = None) -> str:
        """Get help text for commands."""
        lines = []

        if category:
            commands = self.get_by_category(category)
            lines.append(f"\n{category.value.upper()} COMMANDS:")
        else:
            commands = self.get_all_commands()
            lines.append("\nVOICE COMMANDS:")

        for cmd in commands:
            shortcut = f" ({cmd.shortcut})" if cmd.shortcut else ""
            lines.append(f"  {cmd.name}{shortcut}: {cmd.description}")
            if cmd.examples:
                lines.append(f"    Examples: {', '.join(cmd.examples[:2])}")

        return "\n".join(lines)

    def _register_default_commands(self) -> None:
        """Register default voice commands."""
        # Movement commands
        self.register_command(VoiceCommand(
            name="go",
            intent_type=IntentType.MOVE,
            category=CommandCategory.MOVEMENT,
            phrases=["go", "walk", "move", "head"],
            description="Move in a direction or to a location",
            requires_target=True,
            shortcut="g",
            examples=["go north", "walk to the door"],
        ))

        self.register_command(VoiceCommand(
            name="run",
            intent_type=IntentType.FLEE,
            category=CommandCategory.MOVEMENT,
            phrases=["run", "run away", "flee", "escape"],
            description="Run away quickly (urgent)",
            is_urgent=True,
            examples=["run!", "flee now"],
        ))

        self.register_command(VoiceCommand(
            name="approach",
            intent_type=IntentType.APPROACH,
            category=CommandCategory.MOVEMENT,
            phrases=["approach", "go to", "walk toward"],
            description="Approach a target",
            requires_target=True,
            examples=["approach the guard", "go to the table"],
        ))

        self.register_command(VoiceCommand(
            name="hide",
            intent_type=IntentType.HIDE,
            category=CommandCategory.MOVEMENT,
            phrases=["hide", "sneak", "crouch", "stealth"],
            description="Hide or enter stealth mode",
            examples=["hide behind the crate", "sneak past"],
        ))

        # Interaction commands
        self.register_command(VoiceCommand(
            name="look",
            intent_type=IntentType.EXAMINE,
            category=CommandCategory.INTERACTION,
            phrases=["look", "examine", "inspect", "check", "see"],
            description="Examine something closely",
            requires_target=True,
            shortcut="x",
            examples=["look at the desk", "examine the painting"],
            aliases=["l"],
        ))

        self.register_command(VoiceCommand(
            name="take",
            intent_type=IntentType.TAKE,
            category=CommandCategory.INTERACTION,
            phrases=["take", "get", "grab", "pick up", "collect"],
            description="Take or pick up an item",
            requires_target=True,
            shortcut="t",
            examples=["take the key", "grab the letter"],
        ))

        self.register_command(VoiceCommand(
            name="use",
            intent_type=IntentType.USE,
            category=CommandCategory.INTERACTION,
            phrases=["use", "apply", "put", "insert"],
            description="Use an item, optionally on a target",
            requires_target=True,
            shortcut="u",
            examples=["use the key on the door", "use flashlight"],
        ))

        self.register_command(VoiceCommand(
            name="open",
            intent_type=IntentType.INTERACT,
            category=CommandCategory.INTERACTION,
            phrases=["open", "unlock", "activate"],
            description="Open or activate something",
            requires_target=True,
            examples=["open the door", "unlock the chest"],
        ))

        self.register_command(VoiceCommand(
            name="close",
            intent_type=IntentType.INTERACT,
            category=CommandCategory.INTERACTION,
            phrases=["close", "shut", "lock"],
            description="Close or lock something",
            requires_target=True,
            examples=["close the window", "lock the door"],
        ))

        # Social commands
        self.register_command(VoiceCommand(
            name="talk",
            intent_type=IntentType.TALK,
            category=CommandCategory.SOCIAL,
            phrases=["talk", "speak", "chat", "converse"],
            description="Talk to someone",
            requires_target=True,
            examples=["talk to the bartender", "speak with guard"],
        ))

        self.register_command(VoiceCommand(
            name="ask",
            intent_type=IntentType.QUERY,
            category=CommandCategory.SOCIAL,
            phrases=["ask", "ask about", "question"],
            description="Ask someone about something",
            requires_target=True,
            examples=["ask about the murder", "ask the witness"],
        ))

        self.register_command(VoiceCommand(
            name="greet",
            intent_type=IntentType.GREET,
            category=CommandCategory.SOCIAL,
            phrases=["hello", "hi", "hey", "greet", "wave"],
            description="Greet someone",
            examples=["hello", "wave to the guard"],
        ))

        self.register_command(VoiceCommand(
            name="threaten",
            intent_type=IntentType.THREATEN,
            category=CommandCategory.SOCIAL,
            phrases=["threaten", "intimidate", "scare"],
            description="Threaten someone (affects morality)",
            requires_target=True,
            examples=["threaten the merchant", "intimidate witness"],
        ))

        # Combat commands
        self.register_command(VoiceCommand(
            name="attack",
            intent_type=IntentType.ATTACK,
            category=CommandCategory.COMBAT,
            phrases=["attack", "hit", "strike", "fight"],
            description="Attack a target",
            requires_target=True,
            is_urgent=True,
            examples=["attack the guard", "hit him"],
        ))

        self.register_command(VoiceCommand(
            name="defend",
            intent_type=IntentType.DEFEND,
            category=CommandCategory.COMBAT,
            phrases=["defend", "block", "parry", "shield"],
            description="Defend against attack",
            is_urgent=True,
            examples=["defend!", "block the attack"],
        ))

        self.register_command(VoiceCommand(
            name="dodge",
            intent_type=IntentType.DODGE,
            category=CommandCategory.COMBAT,
            phrases=["dodge", "evade", "duck", "sidestep"],
            description="Dodge an attack",
            is_urgent=True,
            examples=["dodge!", "duck now"],
        ))

        # Inventory commands
        self.register_command(VoiceCommand(
            name="inventory",
            intent_type=IntentType.INVENTORY,
            category=CommandCategory.INVENTORY,
            phrases=["inventory", "items", "bag", "check inventory"],
            description="Check your inventory",
            shortcut="i",
            examples=["inventory", "check my items"],
        ))

        self.register_command(VoiceCommand(
            name="drop",
            intent_type=IntentType.DROP,
            category=CommandCategory.INVENTORY,
            phrases=["drop", "discard", "throw away", "leave"],
            description="Drop an item",
            requires_target=True,
            examples=["drop the key", "discard the note"],
        ))

        # System commands
        self.register_command(VoiceCommand(
            name="help",
            intent_type=IntentType.HELP,
            category=CommandCategory.SYSTEM,
            phrases=["help", "commands", "what can i do"],
            description="Get help and available commands",
            shortcut="h",
            examples=["help", "what commands?"],
        ))

        self.register_command(VoiceCommand(
            name="save",
            intent_type=IntentType.SAVE,
            category=CommandCategory.SYSTEM,
            phrases=["save", "save game", "save progress"],
            description="Save the game",
            examples=["save", "save game"],
        ))

        self.register_command(VoiceCommand(
            name="quit",
            intent_type=IntentType.QUIT,
            category=CommandCategory.SYSTEM,
            phrases=["quit", "exit", "end game"],
            description="Quit the game",
            shortcut="q",
            examples=["quit", "exit game"],
        ))

        self.register_command(VoiceCommand(
            name="wait",
            intent_type=IntentType.WAIT,
            category=CommandCategory.SYSTEM,
            phrases=["wait", "pass", "hold", "rest"],
            description="Wait and pass time",
            shortcut="z",
            examples=["wait", "pass time"],
        ))

        # Quick response commands
        self.register_command(VoiceCommand(
            name="yes",
            intent_type=IntentType.YES,
            category=CommandCategory.QUICK_RESPONSE,
            phrases=["yes", "yeah", "yep", "sure", "ok", "okay", "affirmative"],
            description="Confirm/agree",
            examples=["yes", "okay"],
        ))

        self.register_command(VoiceCommand(
            name="no",
            intent_type=IntentType.NO,
            category=CommandCategory.QUICK_RESPONSE,
            phrases=["no", "nope", "nah", "negative", "refuse"],
            description="Decline/disagree",
            examples=["no", "refuse"],
        ))

        self.register_command(VoiceCommand(
            name="cancel",
            intent_type=IntentType.CANCEL,
            category=CommandCategory.QUICK_RESPONSE,
            phrases=["cancel", "nevermind", "abort", "stop"],
            description="Cancel current action",
            examples=["cancel", "nevermind"],
        ))

        # Register quick commands
        self._register_default_quick_commands()

    def _register_default_quick_commands(self) -> None:
        """Register default quick commands."""
        # Directional quick commands
        for direction in ["north", "south", "east", "west", "up", "down"]:
            self.register_quick_command(QuickCommand(
                trigger=direction,
                intent_type=IntentType.MOVE,
                default_target=direction,
            ))

        # Short direction aliases
        direction_aliases = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "u": "up", "d": "down",
        }
        for alias, direction in direction_aliases.items():
            self.register_quick_command(QuickCommand(
                trigger=alias,
                intent_type=IntentType.MOVE,
                default_target=direction,
            ))

        # Urgent commands
        self.register_quick_command(QuickCommand(
            trigger="run",
            intent_type=IntentType.FLEE,
            is_urgent=True,
        ))

        self.register_quick_command(QuickCommand(
            trigger="duck",
            intent_type=IntentType.DODGE,
            is_urgent=True,
        ))

        self.register_quick_command(QuickCommand(
            trigger="block",
            intent_type=IntentType.DEFEND,
            is_urgent=True,
        ))

        # Inventory shortcut
        self.register_quick_command(QuickCommand(
            trigger="i",
            intent_type=IntentType.INVENTORY,
        ))

        # Help shortcut
        self.register_quick_command(QuickCommand(
            trigger="h",
            intent_type=IntentType.HELP,
        ))


class CommandMatcher:
    """
    Matches voice input to commands with fuzzy matching.

    Handles common voice recognition errors and provides
    suggestions for unclear input.
    """

    def __init__(self, vocabulary: Optional[VoiceVocabulary] = None):
        self.vocabulary = vocabulary or VoiceVocabulary()

        # Common voice recognition substitutions
        self.substitutions = {
            # Homophones
            "write": "right",
            "weight": "wait",
            "sea": "see",
            "no": "know",
            "here": "hear",
            "new": "knew",
            "bare": "bear",
            "steal": "steel",
            # Common mishears
            "opened": "open",
            "looked": "look",
            "walked": "walk",
            "attacked": "attack",
            "talked": "talk",
        }

        # Words to strip (filler words)
        self.filler_words = {
            "um", "uh", "like", "you know", "basically",
            "literally", "actually", "please", "just",
        }

    def match(self, text: str, context: dict = None) -> tuple[Optional[VoiceCommand], float]:
        """
        Match text to the best command.

        Returns:
            Tuple of (command or None, confidence)
        """
        context = context or {}
        text = self._preprocess(text)

        if not text:
            return None, 0.0

        # Check quick commands first
        quick = self.vocabulary.get_quick_command(text)
        if quick:
            # Find corresponding full command
            for cmd in self.vocabulary.get_all_commands():
                if cmd.intent_type == quick.intent_type:
                    return cmd, 1.0

        # Find best matching command
        matches = self.vocabulary.find_matches(text)
        if matches:
            return matches[0]

        # Try with substitutions
        corrected = self._apply_substitutions(text)
        if corrected != text:
            matches = self.vocabulary.find_matches(corrected)
            if matches:
                return matches[0][0], matches[0][1] * 0.9  # Slightly lower confidence

        return None, 0.0

    def get_suggestions(self, text: str, max_suggestions: int = 3) -> list[str]:
        """Get command suggestions for unclear input."""
        text = self._preprocess(text)

        if not text:
            return []

        matches = self.vocabulary.find_matches(text, min_confidence=0.3)
        suggestions = []

        for cmd, confidence in matches[:max_suggestions]:
            if cmd.examples:
                suggestions.append(f'Try "{cmd.examples[0]}" ({cmd.name})')
            else:
                suggestions.append(f'Try "{cmd.phrases[0]}" ({cmd.name})')

        return suggestions

    def _preprocess(self, text: str) -> str:
        """Preprocess text for matching."""
        text = text.lower().strip()

        # Remove filler words
        words = text.split()
        words = [w for w in words if w not in self.filler_words]

        return " ".join(words)

    def _apply_substitutions(self, text: str) -> str:
        """Apply common voice recognition corrections."""
        words = text.split()
        corrected = []

        for word in words:
            corrected.append(self.substitutions.get(word, word))

        return " ".join(corrected)
