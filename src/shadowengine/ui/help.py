"""
Help System - In-game help and documentation.

Provides:
- Command help and descriptions
- Contextual hints
- Tutorial integration
- Quick reference
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto


class HelpCategory(Enum):
    """Categories of help topics."""
    NAVIGATION = "navigation"
    EXAMINATION = "examination"
    DIALOGUE = "dialogue"
    INVENTORY = "inventory"
    EVIDENCE = "evidence"
    DEDUCTION = "deduction"
    SYSTEM = "system"
    ADVANCED = "advanced"


@dataclass
class HelpTopic:
    """A help topic with description and examples."""
    id: str
    name: str
    category: HelpCategory
    summary: str
    description: str = ""
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

    def format_short(self) -> str:
        """Format as short one-line help."""
        return f"{self.name}: {self.summary}"

    def format_full(self) -> str:
        """Format as full help text."""
        lines = [
            f"=== {self.name} ===",
            "",
            self.summary,
            ""
        ]

        if self.description:
            lines.append(self.description)
            lines.append("")

        if self.usage:
            lines.append("Usage:")
            lines.append(f"  {self.usage}")
            lines.append("")

        if self.examples:
            lines.append("Examples:")
            for example in self.examples:
                lines.append(f"  > {example}")
            lines.append("")

        if self.aliases:
            lines.append(f"Aliases: {', '.join(self.aliases)}")
            lines.append("")

        if self.related:
            lines.append(f"See also: {', '.join(self.related)}")

        return "\n".join(lines)


# Predefined help topics
HELP_TOPICS: list[HelpTopic] = [
    # Navigation
    HelpTopic(
        id="look",
        name="look",
        category=HelpCategory.NAVIGATION,
        summary="Observe your current location",
        usage="look [direction/object]",
        examples=["look", "look north", "look desk"],
        aliases=["l", "observe"],
        related=["examine", "go"]
    ),
    HelpTopic(
        id="go",
        name="go",
        category=HelpCategory.NAVIGATION,
        summary="Move to a different location",
        usage="go <direction/location>",
        examples=["go north", "go hallway", "go 1"],
        description="Move through exits to explore the scene. Use numbers or names.",
        aliases=["move", "walk"],
        related=["look", "exits"]
    ),
    HelpTopic(
        id="exits",
        name="exits",
        category=HelpCategory.NAVIGATION,
        summary="List available exits",
        usage="exits",
        aliases=["doors", "ways"],
        related=["go", "look"]
    ),

    # Examination
    HelpTopic(
        id="examine",
        name="examine",
        category=HelpCategory.EXAMINATION,
        summary="Examine something closely",
        usage="examine <object/person/number>",
        examples=["examine desk", "examine 3", "examine body"],
        description="Closely examine objects, people, or hotspots to find clues.",
        aliases=["x", "inspect", "check"],
        related=["look", "take", "search"]
    ),
    HelpTopic(
        id="search",
        name="search",
        category=HelpCategory.EXAMINATION,
        summary="Search an area thoroughly",
        usage="search <area>",
        examples=["search room", "search drawers"],
        aliases=["look in"],
        related=["examine", "take"]
    ),

    # Dialogue
    HelpTopic(
        id="talk",
        name="talk",
        category=HelpCategory.DIALOGUE,
        summary="Start a conversation",
        usage="talk <person>",
        examples=["talk butler", "talk 2"],
        description="Initiate dialogue with a character. Choose topics to discuss.",
        aliases=["speak", "chat"],
        related=["ask", "accuse", "present"]
    ),
    HelpTopic(
        id="ask",
        name="ask",
        category=HelpCategory.DIALOGUE,
        summary="Ask about a specific topic",
        usage="ask <person> about <topic>",
        examples=["ask butler about murder", "ask 1 about alibi"],
        aliases=["question"],
        related=["talk", "present"]
    ),
    HelpTopic(
        id="present",
        name="present",
        category=HelpCategory.DIALOGUE,
        summary="Present evidence to a character",
        usage="present <evidence> to <person>",
        examples=["present knife to butler", "present letter to 2"],
        description="Show evidence to a character to gauge their reaction.",
        aliases=["show"],
        related=["evidence", "inventory", "accuse"]
    ),

    # Inventory
    HelpTopic(
        id="inventory",
        name="inventory",
        category=HelpCategory.INVENTORY,
        summary="View your inventory",
        usage="inventory",
        aliases=["i", "inv", "items"],
        related=["take", "examine", "use"]
    ),
    HelpTopic(
        id="take",
        name="take",
        category=HelpCategory.INVENTORY,
        summary="Pick up an item",
        usage="take <item>",
        examples=["take key", "take letter"],
        aliases=["get", "grab", "pick up"],
        related=["inventory", "drop", "examine"]
    ),
    HelpTopic(
        id="use",
        name="use",
        category=HelpCategory.INVENTORY,
        summary="Use an item",
        usage="use <item> [on <target>]",
        examples=["use key", "use key on door"],
        aliases=["apply"],
        related=["inventory", "combine"]
    ),
    HelpTopic(
        id="combine",
        name="combine",
        category=HelpCategory.INVENTORY,
        summary="Combine two items",
        usage="combine <item1> with <item2>",
        examples=["combine torn page with book"],
        related=["inventory", "use"]
    ),

    # Evidence
    HelpTopic(
        id="evidence",
        name="evidence",
        category=HelpCategory.EVIDENCE,
        summary="Review collected evidence",
        usage="evidence [item]",
        examples=["evidence", "evidence knife"],
        description="List all evidence or examine a specific piece.",
        aliases=["clues"],
        related=["present", "deduce", "accuse"]
    ),
    HelpTopic(
        id="notes",
        name="notes",
        category=HelpCategory.EVIDENCE,
        summary="View your investigation notes",
        usage="notes",
        description="Review facts and observations you've gathered.",
        aliases=["journal", "log"],
        related=["evidence", "deduce"]
    ),

    # Deduction
    HelpTopic(
        id="deduce",
        name="deduce",
        category=HelpCategory.DEDUCTION,
        summary="Make deductions from evidence",
        usage="deduce",
        description="Review your evidence and form conclusions.",
        aliases=["think", "reason"],
        related=["evidence", "accuse"]
    ),
    HelpTopic(
        id="accuse",
        name="accuse",
        category=HelpCategory.DEDUCTION,
        summary="Accuse someone of the crime",
        usage="accuse <person> [with <evidence>]",
        examples=["accuse butler", "accuse butler with knife"],
        description="Make a formal accusation. Be sure of your evidence!",
        related=["evidence", "present", "deduce"]
    ),

    # System
    HelpTopic(
        id="help",
        name="help",
        category=HelpCategory.SYSTEM,
        summary="Show help information",
        usage="help [topic]",
        examples=["help", "help examine", "help dialogue"],
        aliases=["?", "h"],
        related=["commands", "tutorial"]
    ),
    HelpTopic(
        id="commands",
        name="commands",
        category=HelpCategory.SYSTEM,
        summary="List all commands",
        usage="commands [category]",
        examples=["commands", "commands inventory"],
        related=["help"]
    ),
    HelpTopic(
        id="save",
        name="save",
        category=HelpCategory.SYSTEM,
        summary="Save the game",
        usage="save [name]",
        examples=["save", "save checkpoint1"],
        related=["load", "quit"]
    ),
    HelpTopic(
        id="load",
        name="load",
        category=HelpCategory.SYSTEM,
        summary="Load a saved game",
        usage="load [name]",
        examples=["load", "load checkpoint1"],
        related=["save"]
    ),
    HelpTopic(
        id="quit",
        name="quit",
        category=HelpCategory.SYSTEM,
        summary="Exit the game",
        usage="quit",
        aliases=["exit", "q"],
        related=["save"]
    ),

    # Advanced
    HelpTopic(
        id="time",
        name="time",
        category=HelpCategory.ADVANCED,
        summary="Check the current time",
        usage="time",
        description="See the current in-game time. Some events are time-sensitive.",
        related=["wait"]
    ),
    HelpTopic(
        id="wait",
        name="wait",
        category=HelpCategory.ADVANCED,
        summary="Wait for time to pass",
        usage="wait [duration]",
        examples=["wait", "wait 1 hour"],
        description="Let time pass. NPCs may change location.",
        related=["time"]
    )
]


class HelpSystem:
    """
    Provides in-game help and documentation.

    Features contextual hints and command help.
    """

    def __init__(self, topics: list[HelpTopic] = None):
        self.topics = topics if topics is not None else HELP_TOPICS
        self._build_index()

    def _build_index(self) -> None:
        """Build search index for quick lookup."""
        self._by_id: dict[str, HelpTopic] = {}
        self._by_alias: dict[str, HelpTopic] = {}
        self._by_category: dict[HelpCategory, list[HelpTopic]] = {}

        for topic in self.topics:
            self._by_id[topic.id] = topic
            for alias in topic.aliases:
                self._by_alias[alias] = topic

            if topic.category not in self._by_category:
                self._by_category[topic.category] = []
            self._by_category[topic.category].append(topic)

    def get_topic(self, query: str) -> Optional[HelpTopic]:
        """Get a topic by ID or alias."""
        query = query.lower()
        if query in self._by_id:
            return self._by_id[query]
        if query in self._by_alias:
            return self._by_alias[query]
        return None

    def search(self, query: str) -> list[HelpTopic]:
        """Search topics by keyword."""
        query = query.lower()
        results = []
        for topic in self.topics:
            if (query in topic.id.lower() or
                query in topic.name.lower() or
                query in topic.summary.lower() or
                query in topic.description.lower()):
                results.append(topic)
        return results

    def get_category(self, category: HelpCategory) -> list[HelpTopic]:
        """Get all topics in a category."""
        return self._by_category.get(category, [])

    def get_all_commands(self) -> list[str]:
        """Get list of all command names."""
        commands = []
        for topic in self.topics:
            commands.append(topic.id)
            commands.extend(topic.aliases)
        return sorted(set(commands))

    def format_command_list(self) -> str:
        """Format a list of all commands by category."""
        lines = ["=== Available Commands ===", ""]

        for category in HelpCategory:
            topics = self.get_category(category)
            if topics:
                lines.append(f"[{category.value.title()}]")
                for topic in topics:
                    aliases = f" ({', '.join(topic.aliases)})" if topic.aliases else ""
                    lines.append(f"  {topic.id}{aliases} - {topic.summary}")
                lines.append("")

        lines.append("Type 'help <command>' for detailed help.")
        return "\n".join(lines)

    def format_quick_reference(self) -> str:
        """Format a quick reference card."""
        lines = [
            "=== Quick Reference ===",
            "",
            "MOVEMENT:  look, go <dir>, exits",
            "EXAMINE:   examine <obj>, search <area>",
            "DIALOGUE:  talk <person>, ask about <topic>",
            "EVIDENCE:  present <item> to <person>",
            "ITEMS:     inventory, take <item>, use <item>",
            "SOLVE:     deduce, accuse <person>",
            "",
            "Type 'help <command>' for more info."
        ]
        return "\n".join(lines)


@dataclass
class ContextualHint:
    """A contextual hint that can appear during gameplay."""
    id: str
    message: str
    condition: Callable[..., bool]
    priority: int = 0
    shown: bool = False
    max_shows: int = 1


class HintSystem:
    """
    Provides contextual hints to guide players.

    Shows hints based on game state without spoiling.
    """

    def __init__(self):
        self.hints: list[ContextualHint] = []
        self._shown_counts: dict[str, int] = {}

    def add_hint(self, hint: ContextualHint) -> None:
        """Add a contextual hint."""
        self.hints.append(hint)

    def check_hints(self, context: dict) -> Optional[str]:
        """
        Check for applicable hints.

        Returns hint message or None.
        """
        applicable = []

        for hint in self.hints:
            count = self._shown_counts.get(hint.id, 0)
            if count >= hint.max_shows:
                continue

            try:
                if hint.condition(context):
                    applicable.append(hint)
            except Exception:
                pass  # Skip hints with bad conditions

        if not applicable:
            return None

        # Sort by priority and return highest
        applicable.sort(key=lambda h: h.priority, reverse=True)
        hint = applicable[0]

        self._shown_counts[hint.id] = self._shown_counts.get(hint.id, 0) + 1
        return hint.message

    def reset(self) -> None:
        """Reset shown status."""
        self._shown_counts.clear()


# Standard gameplay hints
def create_standard_hints() -> list[ContextualHint]:
    """Create standard hints for new players."""
    return [
        ContextualHint(
            id="first_room",
            message="Tip: Use 'look' to observe your surroundings.",
            condition=lambda ctx: ctx.get("commands_entered", 0) == 0,
            priority=10
        ),
        ContextualHint(
            id="examine_hotspot",
            message="Tip: Use 'examine' to investigate numbered items.",
            condition=lambda ctx: ctx.get("hotspots_visible", 0) > 0 and ctx.get("examined_count", 0) == 0,
            priority=8
        ),
        ContextualHint(
            id="talk_to_people",
            message="Tip: Use 'talk' to speak with people in the scene.",
            condition=lambda ctx: ctx.get("people_present", 0) > 0 and ctx.get("talked_count", 0) == 0,
            priority=7
        ),
        ContextualHint(
            id="check_inventory",
            message="Tip: Use 'inventory' to see what you're carrying.",
            condition=lambda ctx: ctx.get("items_collected", 0) > 0 and not ctx.get("inventory_viewed", False),
            priority=5
        ),
        ContextualHint(
            id="present_evidence",
            message="Tip: Use 'present <evidence> to <person>' to show evidence.",
            condition=lambda ctx: ctx.get("evidence_count", 0) > 0 and ctx.get("presented_count", 0) == 0,
            priority=6
        ),
        ContextualHint(
            id="stuck_hint",
            message="Tip: Try examining everything and talking to everyone.",
            condition=lambda ctx: ctx.get("commands_entered", 0) > 50 and ctx.get("progress", 0) < 0.2,
            priority=3
        )
    ]
