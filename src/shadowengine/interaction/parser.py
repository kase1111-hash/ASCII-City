"""
Command Parser - Fail-soft input parsing.

Interprets player intent, handles typos, and provides helpful error messages.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum
import re

from .matching import best_match


class CommandType(Enum):
    """Types of commands the player can issue."""
    EXAMINE = "examine"
    TALK = "talk"
    TAKE = "take"
    USE = "use"
    GO = "go"
    INVENTORY = "inventory"
    CASE = "case"
    WAIT = "wait"
    HELP = "help"
    SAVE = "save"
    LOAD = "load"
    SETTINGS = "settings"
    QUIT = "quit"
    HOTSPOT = "hotspot"         # Numeric hotspot selection
    UNKNOWN = "unknown"

    # Dialogue-specific commands
    ASK = "ask"
    ACCUSE = "accuse"
    THREATEN = "threaten"
    SHOW = "show"
    LEAVE = "leave"


@dataclass
class Command:
    """A parsed player command."""

    command_type: CommandType
    target: Optional[str] = None        # What/who the command targets
    secondary: Optional[str] = None     # Secondary target (use X on Y)
    raw_input: str = ""                 # Original input
    hotspot_number: Optional[int] = None  # If hotspot selection
    topic: Optional[str] = None         # For dialogue commands

    def is_valid(self) -> bool:
        """Check if this is a valid, actionable command."""
        return self.command_type != CommandType.UNKNOWN


class CommandParser:
    """
    Fail-soft command parser that interprets player intent.
    """

    def __init__(self):
        # Verb mappings
        self.verb_mappings = {
            CommandType.EXAMINE: [
                "examine", "look", "check", "inspect", "see", "view",
                "read", "study", "observe", "x", "l"
            ],
            CommandType.TALK: [
                "talk", "speak", "ask", "question", "interview",
                "chat", "converse", "say", "t"
            ],
            CommandType.TAKE: [
                "take", "get", "grab", "pick", "collect", "acquire", "g"
            ],
            CommandType.USE: [
                "use", "apply", "put", "insert", "combine", "u"
            ],
            CommandType.GO: [
                "go", "walk", "move", "enter", "exit", "leave", "head",
                "n", "s", "e", "w", "north", "south", "east", "west"
            ],
            CommandType.INVENTORY: [
                "inventory", "inv", "items", "i"
            ],
            CommandType.CASE: [
                "case", "casebook", "notes", "journal", "clues", "evidence"
            ],
            CommandType.WAIT: [
                "wait", "rest", "pass", "z"
            ],
            CommandType.HELP: [
                "help", "?", "commands", "h"
            ],
            CommandType.SAVE: ["save"],
            CommandType.LOAD: ["load"],
            CommandType.SETTINGS: ["settings", "options", "config", "prefs", "preferences"],
            CommandType.QUIT: ["quit", "q"],

            # Dialogue commands
            CommandType.ASK: ["ask about", "ask"],
            CommandType.ACCUSE: ["accuse", "confront", "arrest"],
            CommandType.THREATEN: ["threaten", "intimidate"],
            CommandType.SHOW: ["show", "present", "give"],
            CommandType.LEAVE: ["leave", "goodbye", "bye", "end"]
        }

        # Build reverse mapping
        self.word_to_verb = {}
        for cmd_type, words in self.verb_mappings.items():
            for word in words:
                self.word_to_verb[word] = cmd_type

        # Never guessed from a typo: a misspelled word must not end the
        # session, overwrite a save, or open a menu
        self.no_fuzzy = {
            CommandType.QUIT, CommandType.SAVE, CommandType.LOAD,
            CommandType.SETTINGS,
        }

        # Common words to strip
        self.articles = {"the", "a", "an", "at", "to", "with", "on", "in"}

        # Direction shortcuts
        self.directions = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "ne": "northeast", "nw": "northwest",
            "se": "southeast", "sw": "southwest",
            "u": "up", "d": "down"
        }

    def parse(self, raw_input: str, context: dict = None) -> Command:
        """
        Parse player input into a Command.

        Args:
            raw_input: The raw text input from player
            context: Optional dict with available targets, hotspots, etc.

        Returns:
            A Command object representing the parsed input
        """
        context = context or {}

        # Normalize input
        text = raw_input.lower().strip()

        if not text:
            return Command(
                command_type=CommandType.UNKNOWN,
                raw_input=raw_input
            )

        # Check for hotspot number
        if text.isdigit():
            return Command(
                command_type=CommandType.HOTSPOT,
                hotspot_number=int(text),
                raw_input=raw_input
            )

        # Check for "number verb" pattern (e.g., "1 examine")
        match = re.match(r'^(\d+)\s+(.+)$', text)
        if match:
            hotspot_num = int(match.group(1))
            rest = match.group(2)
            cmd = self._parse_verb_phrase(rest, context)
            cmd.hotspot_number = hotspot_num
            cmd.raw_input = raw_input
            return cmd

        # Parse as verb phrase
        cmd = self._parse_verb_phrase(text, context)
        cmd.raw_input = raw_input
        return cmd

    def _parse_verb_phrase(self, text: str, context: dict) -> Command:
        """Parse a verb phrase (no hotspot number)."""
        tokens = text.split()
        if not tokens:
            return Command(command_type=CommandType.UNKNOWN)

        # Try to find verb
        verb_type, remaining_tokens = self._find_verb(tokens)

        if verb_type == CommandType.UNKNOWN:
            # Maybe they just typed a noun - try to figure out default action
            return self._infer_from_noun(tokens, context)

        # "exit to street" goes somewhere; a bare "exit" means quit (the
        # quit handler asks before anything is lost)
        if tokens[0] == "exit" and not remaining_tokens:
            return Command(command_type=CommandType.QUIT)

        # Extract target
        target = self._extract_target(remaining_tokens, context)

        # Check for "use X on Y" pattern
        secondary = None
        if verb_type == CommandType.USE and target:
            parts = target.split(" on ")
            if len(parts) == 2:
                target = parts[0].strip()
                secondary = parts[1].strip()

        return Command(
            command_type=verb_type,
            target=target,
            secondary=secondary
        )

    def _find_verb(self, tokens: list[str]) -> Tuple[CommandType, list[str]]:
        """Find the verb in tokens and return remaining tokens."""

        # Try two-word verbs first ("ask about")
        if len(tokens) >= 2:
            two_word = f"{tokens[0]} {tokens[1]}"
            if two_word in self.word_to_verb:
                return self.word_to_verb[two_word], tokens[2:]

        # Try single word verb
        if tokens[0] in self.word_to_verb:
            return self.word_to_verb[tokens[0]], tokens[1:]

        # Try fuzzy match for typos
        fuzzy_match = self._fuzzy_find_verb(tokens[0])
        if fuzzy_match:
            return fuzzy_match, tokens[1:]

        return CommandType.UNKNOWN, tokens

    def _fuzzy_find_verb(self, word: str, max_distance: Optional[int] = None) -> Optional[CommandType]:
        """
        Try to find a verb with typo tolerance. Short words get one edit
        (a swapped pair counts as one: "tlak" is "talk"), longer words two;
        otherwise "back" would read as "talk" and "press" as "pass".
        """
        if max_distance is None:
            max_distance = 1 if len(word) <= 5 else 2
        best = None
        for verb_word, cmd_type in self.word_to_verb.items():
            if len(verb_word) <= 2 or cmd_type in self.no_fuzzy:
                continue
            distance = self._levenshtein(word, verb_word)
            if distance > max_distance:
                continue
            # On a tie, a verb the player started typing wins ("tak" -> take)
            rank = (distance, 0 if verb_word.startswith(word) else 1)
            if best is None or rank < best[0]:
                best = (rank, cmd_type)
        return best[1] if best else None

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Edit distance where swapping two adjacent letters counts as one edit."""
        rows, cols = len(s1) + 1, len(s2) + 1
        d = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            d[i][0] = i
        for j in range(cols):
            d[0][j] = j
        for i in range(1, rows):
            for j in range(1, cols):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                d[i][j] = min(
                    d[i - 1][j] + 1,         # deletion
                    d[i][j - 1] + 1,         # insertion
                    d[i - 1][j - 1] + cost,  # substitution
                )
                if (
                    i > 1 and j > 1
                    and s1[i - 1] == s2[j - 2]
                    and s1[i - 2] == s2[j - 1]
                ):
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)  # transposition
        return d[-1][-1]

    def _extract_target(self, tokens: list[str], context: dict) -> Optional[str]:
        """Extract the target from remaining tokens."""
        # Remove articles
        filtered = [t for t in tokens if t not in self.articles]

        if not filtered:
            return None

        target = " ".join(filtered)

        # Match against what's in the scene: whole words first, so "alley"
        # finds the Dark Alley rather than O'Malley's Bar; filler words don't
        # count, so "door to street" still finds "Door to Street"
        known_targets = context.get("targets", [])
        index = best_match(target, known_targets)
        if index is not None:
            return known_targets[index]

        return target if target else None

    def _infer_from_noun(self, tokens: list[str], context: dict) -> Command:
        """
        Infer command from noun only (player just typed object name).
        """
        target = " ".join([t for t in tokens if t not in self.articles])

        # Try to match against known targets and infer action
        hotspots = context.get("hotspots", [])
        index = best_match(target, [h.get("label", "") for h in hotspots]) if target else None
        if index is not None:
            hotspot = hotspots[index]
            hotspot_type = hotspot.get("type", "object")
            if hotspot_type == "person":
                return Command(command_type=CommandType.TALK, target=hotspot.get("label"))
            if hotspot_type == "exit":
                return Command(command_type=CommandType.GO, target=hotspot.get("label"))
            return Command(command_type=CommandType.EXAMINE, target=hotspot.get("label"))

        # Default to examine for unknown nouns
        return Command(
            command_type=CommandType.EXAMINE,
            target=target
        )

    def get_help_text(self) -> str:
        """Return help text for available commands."""
        return """
Getting around:
  [number]                  Use the numbered thing on screen
  examine [thing]           Look at something (x for short)
  look                      Take in the room again
  go [place or exit]        Move: 'go bar', 'go door to street', 'north'
  back                      Return to where you just were

Close inspection:
  look closer [at thing]    Zoom in for finer detail (repeat to go deeper)
  step back                 Zoom back out
  look under/behind [thing] Check around an object
  focus on [feature]        Study a detail you noticed
  use magnifying glass on [thing]

People:
  talk [person]             Start a conversation (t for short)
  ask [person] about [topic]
  show [evidence] to [person]
  threaten [person]         Pressure them (it has a cost)
  accuse [person]           Name them as the killer

While talking, just type what you'd say. Ask about the things they
care about and they'll warm to you. Also: show [evidence], threaten,
accuse, case, inventory, leave.

The case:
  case                      Your case file: leads, evidence, notes
  inventory                 What you're carrying (i)
  take [item]               Pick something up
  wait                      Let time pass

  save / load               Save your case, or pick up a saved one
  settings                  Game options
  quit                      Leave (asks first; your case is saved)
"""

    def get_error_suggestion(self, command: Command, context: dict) -> str:
        """Generate a helpful error message for an unknown command."""
        if command.target:
            targets = context.get("targets", [])
            if targets:
                return f"I don't understand '{command.raw_input}'. Try one of: {', '.join(targets[:5])}"
            return f"I don't see '{command.target}' here."
        return "I don't understand. Type 'help' for available commands."
