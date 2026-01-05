"""
Tutorial System - Interactive tutorial for new players.

Provides:
- Step-by-step tutorial
- Progress tracking
- Skip/resume functionality
- Tutorial modes
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto


class TutorialPhase(Enum):
    """Phases of the tutorial."""
    NOT_STARTED = auto()
    NAVIGATION = auto()
    EXAMINATION = auto()
    DIALOGUE = auto()
    EVIDENCE = auto()
    DEDUCTION = auto()
    COMPLETE = auto()


@dataclass
class TutorialStep:
    """A single step in the tutorial."""
    id: str
    phase: TutorialPhase
    instruction: str
    expected_action: str  # Command pattern to match
    hint: str = ""
    success_message: str = ""
    allow_skip: bool = True
    validate: Optional[Callable[[str], bool]] = None

    def check_completion(self, command: str) -> bool:
        """Check if the command completes this step."""
        if self.validate:
            return self.validate(command)

        # Simple pattern matching
        cmd = command.lower().strip()
        expected = self.expected_action.lower()

        # Exact match
        if cmd == expected:
            return True

        # Starts with expected
        if expected.endswith("*"):
            return cmd.startswith(expected[:-1])

        # Contains expected
        if expected.startswith("*") and expected.endswith("*"):
            return expected[1:-1] in cmd

        return False


# Predefined tutorial steps
TUTORIAL_STEPS: list[TutorialStep] = [
    # Navigation phase
    TutorialStep(
        id="tutorial_look",
        phase=TutorialPhase.NAVIGATION,
        instruction="Welcome! Let's start by observing your surroundings. Type 'look' to see the room.",
        expected_action="look",
        hint="Type 'look' and press Enter.",
        success_message="Good! You can see the room description and any notable features."
    ),
    TutorialStep(
        id="tutorial_exits",
        phase=TutorialPhase.NAVIGATION,
        instruction="Now let's see where we can go. Type 'exits' to see available exits.",
        expected_action="exits",
        hint="Type 'exits' to see where you can go.",
        success_message="Exits are shown with numbers. You can use these to navigate."
    ),
    TutorialStep(
        id="tutorial_go",
        phase=TutorialPhase.NAVIGATION,
        instruction="Move to another location by typing 'go' followed by an exit name or number.",
        expected_action="go *",
        hint="Type 'go 1' or 'go' followed by an exit name.",
        success_message="Great! You've moved to a new location."
    ),

    # Examination phase
    TutorialStep(
        id="tutorial_examine",
        phase=TutorialPhase.EXAMINATION,
        instruction="Now let's examine something. Use 'examine' followed by an object or number.",
        expected_action="examine *",
        hint="Type 'examine 1' or 'examine' followed by an object name.",
        success_message="Examining objects reveals clues and details."
    ),
    TutorialStep(
        id="tutorial_take",
        phase=TutorialPhase.EXAMINATION,
        instruction="Some items can be picked up. Try 'take' followed by an item name.",
        expected_action="take *",
        hint="Type 'take' followed by an item you see.",
        success_message="Item collected! Check your inventory to see it."
    ),
    TutorialStep(
        id="tutorial_inventory",
        phase=TutorialPhase.EXAMINATION,
        instruction="View your inventory by typing 'inventory' or just 'i'.",
        expected_action="i*",
        hint="Type 'inventory' or 'i'.",
        success_message="Your inventory shows all collected items."
    ),

    # Dialogue phase
    TutorialStep(
        id="tutorial_talk",
        phase=TutorialPhase.DIALOGUE,
        instruction="Let's talk to someone. Type 'talk' followed by a person's name.",
        expected_action="talk *",
        hint="Type 'talk' followed by a character name.",
        success_message="Conversations reveal information and build trust."
    ),
    TutorialStep(
        id="tutorial_ask",
        phase=TutorialPhase.DIALOGUE,
        instruction="You can ask about specific topics. Try 'ask <person> about <topic>'.",
        expected_action="ask *",
        hint="Type 'ask <person> about <topic>'.",
        success_message="Asking about topics can unlock new information."
    ),

    # Evidence phase
    TutorialStep(
        id="tutorial_evidence",
        phase=TutorialPhase.EVIDENCE,
        instruction="Review your evidence by typing 'evidence'.",
        expected_action="evidence",
        hint="Type 'evidence' to see collected clues.",
        success_message="Evidence is key to solving the mystery."
    ),
    TutorialStep(
        id="tutorial_present",
        phase=TutorialPhase.EVIDENCE,
        instruction="Present evidence to a character with 'present <item> to <person>'.",
        expected_action="present *",
        hint="Type 'present <evidence> to <person>'.",
        success_message="Presenting evidence reveals character reactions."
    ),

    # Deduction phase
    TutorialStep(
        id="tutorial_deduce",
        phase=TutorialPhase.DEDUCTION,
        instruction="Review your findings with 'deduce' or 'think'.",
        expected_action="deduc*",
        hint="Type 'deduce' to review your conclusions.",
        success_message="Deduction helps you piece together the truth."
    ),
    TutorialStep(
        id="tutorial_accuse",
        phase=TutorialPhase.DEDUCTION,
        instruction="When ready, you can 'accuse <person>' to make your accusation.",
        expected_action="accuse *",
        hint="Type 'accuse' followed by your suspect's name.",
        success_message="Be sure before accusing - wrong accusations have consequences!"
    )
]


class Tutorial:
    """
    Manages the tutorial experience.

    Guides new players through game mechanics.
    """

    def __init__(self, steps: list[TutorialStep] = None):
        self.steps = steps if steps is not None else TUTORIAL_STEPS
        self.current_step: int = 0
        self.phase: TutorialPhase = TutorialPhase.NOT_STARTED
        self.completed_steps: set[str] = set()
        self.active: bool = False
        self.skipped: bool = False

    def start(self) -> str:
        """Start the tutorial."""
        self.active = True
        self.current_step = 0
        self.phase = TutorialPhase.NAVIGATION
        return self.get_current_instruction()

    def skip(self) -> str:
        """Skip the tutorial."""
        self.active = False
        self.skipped = True
        self.phase = TutorialPhase.COMPLETE
        return "Tutorial skipped. Type 'help' if you need assistance."

    def get_current_step(self) -> Optional[TutorialStep]:
        """Get the current tutorial step."""
        if not self.active or self.current_step >= len(self.steps):
            return None
        return self.steps[self.current_step]

    def get_current_instruction(self) -> str:
        """Get instruction for current step."""
        step = self.get_current_step()
        if step:
            return f"[Tutorial] {step.instruction}"
        return ""

    def get_hint(self) -> str:
        """Get hint for current step."""
        step = self.get_current_step()
        if step:
            return f"[Hint] {step.hint}"
        return ""

    def process_command(self, command: str) -> Optional[str]:
        """
        Process a command for tutorial progress.

        Returns success message if step completed.
        """
        if not self.active:
            return None

        step = self.get_current_step()
        if not step:
            return None

        if step.check_completion(command):
            self.completed_steps.add(step.id)
            message = step.success_message

            # Move to next step
            self.current_step += 1
            self._update_phase()

            # Check if tutorial complete
            if self.current_step >= len(self.steps):
                self.active = False
                self.phase = TutorialPhase.COMPLETE
                message += "\n\n[Tutorial Complete] You've learned the basics! Good luck!"
            else:
                next_instruction = self.get_current_instruction()
                message += f"\n\n{next_instruction}"

            return message

        return None

    def _update_phase(self) -> None:
        """Update phase based on current step."""
        step = self.get_current_step()
        if step:
            self.phase = step.phase

    def is_complete(self) -> bool:
        """Check if tutorial is complete."""
        return self.phase == TutorialPhase.COMPLETE

    def get_progress(self) -> float:
        """Get tutorial completion progress."""
        if not self.steps:
            return 0.0
        return len(self.completed_steps) / len(self.steps)

    def get_phase_name(self) -> str:
        """Get current phase name."""
        return self.phase.name.replace("_", " ").title()

    def to_dict(self) -> dict:
        return {
            "current_step": self.current_step,
            "phase": self.phase.name,
            "completed_steps": list(self.completed_steps),
            "active": self.active,
            "skipped": self.skipped
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tutorial":
        tutorial = cls()
        tutorial.current_step = data.get("current_step", 0)
        tutorial.phase = TutorialPhase[data.get("phase", "NOT_STARTED")]
        tutorial.completed_steps = set(data.get("completed_steps", []))
        tutorial.active = data.get("active", False)
        tutorial.skipped = data.get("skipped", False)
        return tutorial


@dataclass
class TutorialPrompt:
    """A prompt to offer tutorial to new players."""
    message: str = "Would you like to play the tutorial? (yes/no)"
    accept_responses: list[str] = field(default_factory=lambda: ["yes", "y", "sure", "ok"])
    decline_responses: list[str] = field(default_factory=lambda: ["no", "n", "skip"])

    def check_response(self, response: str) -> Optional[bool]:
        """
        Check player response.

        Returns True for accept, False for decline, None for invalid.
        """
        response = response.lower().strip()
        if response in self.accept_responses:
            return True
        if response in self.decline_responses:
            return False
        return None
