"""Tests for the tutorial system."""

import pytest
from src.shadowengine.ui.tutorial import (
    TutorialPhase, TutorialStep, Tutorial,
    TutorialPrompt, TUTORIAL_STEPS
)


class TestTutorialStep:
    """Tests for TutorialStep."""

    def test_creation(self):
        """Should create a tutorial step."""
        step = TutorialStep(
            id="test",
            phase=TutorialPhase.NAVIGATION,
            instruction="Test instruction",
            expected_action="look"
        )
        assert step.id == "test"
        assert step.phase == TutorialPhase.NAVIGATION

    def test_check_completion_exact(self):
        """Should match exact command."""
        step = TutorialStep(
            id="test",
            phase=TutorialPhase.NAVIGATION,
            instruction="Test",
            expected_action="look"
        )

        assert step.check_completion("look")
        assert step.check_completion("LOOK")  # Case insensitive
        assert not step.check_completion("look around")

    def test_check_completion_prefix(self):
        """Should match command prefix."""
        step = TutorialStep(
            id="test",
            phase=TutorialPhase.NAVIGATION,
            instruction="Test",
            expected_action="go *"
        )

        assert step.check_completion("go north")
        assert step.check_completion("go 1")
        assert not step.check_completion("look")

    def test_check_completion_custom_validator(self):
        """Should use custom validator."""
        step = TutorialStep(
            id="test",
            phase=TutorialPhase.NAVIGATION,
            instruction="Test",
            expected_action="any",
            validate=lambda cmd: "examine" in cmd.lower()
        )

        assert step.check_completion("examine desk")
        assert step.check_completion("EXAMINE chair")
        assert not step.check_completion("look")


class TestPredefinedSteps:
    """Tests for predefined tutorial steps."""

    def test_steps_exist(self):
        """Should have predefined steps."""
        assert len(TUTORIAL_STEPS) > 0

    def test_steps_cover_phases(self):
        """Should cover major phases."""
        phases = set(s.phase for s in TUTORIAL_STEPS)
        assert TutorialPhase.NAVIGATION in phases
        assert TutorialPhase.EXAMINATION in phases
        assert TutorialPhase.DIALOGUE in phases

    def test_steps_have_content(self):
        """All steps should have content."""
        for step in TUTORIAL_STEPS:
            assert step.instruction
            assert step.expected_action


class TestTutorial:
    """Tests for Tutorial."""

    def test_creation(self):
        """Should create tutorial."""
        tutorial = Tutorial()
        assert tutorial.phase == TutorialPhase.NOT_STARTED
        assert not tutorial.active

    def test_start(self):
        """Should start tutorial."""
        tutorial = Tutorial()
        message = tutorial.start()

        assert tutorial.active
        assert tutorial.phase == TutorialPhase.NAVIGATION
        assert "Tutorial" in message

    def test_skip(self):
        """Should skip tutorial."""
        tutorial = Tutorial()
        tutorial.start()
        message = tutorial.skip()

        assert not tutorial.active
        assert tutorial.skipped
        assert tutorial.phase == TutorialPhase.COMPLETE
        assert "skip" in message.lower()

    def test_get_current_step(self):
        """Should get current step."""
        tutorial = Tutorial()
        tutorial.start()

        step = tutorial.get_current_step()

        assert step is not None
        assert step.phase == TutorialPhase.NAVIGATION

    def test_get_current_instruction(self):
        """Should get instruction."""
        tutorial = Tutorial()
        tutorial.start()

        instruction = tutorial.get_current_instruction()

        assert "[Tutorial]" in instruction

    def test_get_hint(self):
        """Should get hint."""
        tutorial = Tutorial()
        tutorial.start()

        hint = tutorial.get_hint()

        assert "[Hint]" in hint

    def test_process_command_advances(self):
        """Should advance on correct command."""
        tutorial = Tutorial()
        tutorial.start()

        first_step = tutorial.current_step
        result = tutorial.process_command("look")

        assert result is not None  # Got success message
        assert tutorial.current_step == first_step + 1

    def test_process_command_wrong(self):
        """Should not advance on wrong command."""
        tutorial = Tutorial()
        tutorial.start()

        first_step = tutorial.current_step
        result = tutorial.process_command("wrong command")

        assert result is None
        assert tutorial.current_step == first_step

    def test_complete_tutorial(self):
        """Should complete tutorial after all steps."""
        steps = [
            TutorialStep(
                id="step1",
                phase=TutorialPhase.NAVIGATION,
                instruction="Step 1",
                expected_action="cmd1"
            ),
            TutorialStep(
                id="step2",
                phase=TutorialPhase.NAVIGATION,
                instruction="Step 2",
                expected_action="cmd2"
            )
        ]
        tutorial = Tutorial(steps=steps)
        tutorial.start()

        tutorial.process_command("cmd1")
        result = tutorial.process_command("cmd2")

        assert tutorial.is_complete()
        assert not tutorial.active
        assert "Complete" in result

    def test_is_complete(self):
        """Should detect completion."""
        tutorial = Tutorial()
        assert not tutorial.is_complete()

        tutorial.phase = TutorialPhase.COMPLETE
        assert tutorial.is_complete()

    def test_get_progress(self):
        """Should calculate progress."""
        steps = [
            TutorialStep("s1", TutorialPhase.NAVIGATION, "S1", "c1"),
            TutorialStep("s2", TutorialPhase.NAVIGATION, "S2", "c2"),
            TutorialStep("s3", TutorialPhase.NAVIGATION, "S3", "c3"),
            TutorialStep("s4", TutorialPhase.NAVIGATION, "S4", "c4"),
        ]
        tutorial = Tutorial(steps=steps)
        tutorial.start()

        tutorial.process_command("c1")
        tutorial.process_command("c2")

        assert tutorial.get_progress() == 0.5

    def test_get_phase_name(self):
        """Should get phase name."""
        tutorial = Tutorial()
        tutorial.phase = TutorialPhase.NAVIGATION

        assert tutorial.get_phase_name() == "Navigation"

    def test_serialization(self):
        """Should serialize and deserialize."""
        tutorial = Tutorial()
        tutorial.start()
        tutorial.process_command("look")

        data = tutorial.to_dict()
        restored = Tutorial.from_dict(data)

        assert restored.active
        assert restored.current_step == 1


class TestTutorialPrompt:
    """Tests for TutorialPrompt."""

    def test_creation(self):
        """Should create prompt."""
        prompt = TutorialPrompt()
        assert prompt.message

    def test_check_accept(self):
        """Should recognize accept responses."""
        prompt = TutorialPrompt()

        assert prompt.check_response("yes") is True
        assert prompt.check_response("y") is True
        assert prompt.check_response("YES") is True

    def test_check_decline(self):
        """Should recognize decline responses."""
        prompt = TutorialPrompt()

        assert prompt.check_response("no") is False
        assert prompt.check_response("n") is False
        assert prompt.check_response("skip") is False

    def test_check_invalid(self):
        """Should return None for invalid."""
        prompt = TutorialPrompt()

        assert prompt.check_response("maybe") is None
        assert prompt.check_response("") is None

    def test_custom_responses(self):
        """Should support custom responses."""
        prompt = TutorialPrompt(
            accept_responses=["да", "oui"],
            decline_responses=["нет", "non"]
        )

        assert prompt.check_response("да") is True
        assert prompt.check_response("non") is False
