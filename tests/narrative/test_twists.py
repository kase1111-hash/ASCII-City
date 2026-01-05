"""Tests for the twist system."""

import pytest
from src.shadowengine.narrative.twists import (
    TwistType, TwistCondition, Twist,
    TwistManager, TwistGenerator
)


class TestTwistType:
    """Tests for TwistType enum."""

    def test_character_twists_defined(self):
        """Character twist types should be defined."""
        assert TwistType.HIDDEN_IDENTITY
        assert TwistType.SECRET_ALLY
        assert TwistType.BETRAYAL
        assert TwistType.REDEMPTION

    def test_plot_twists_defined(self):
        """Plot twist types should be defined."""
        assert TwistType.WRONG_CRIME
        assert TwistType.MULTIPLE_CULPRITS
        assert TwistType.DEEPER_CONSPIRACY

    def test_evidence_twists_defined(self):
        """Evidence twist types should be defined."""
        assert TwistType.PLANTED_EVIDENCE
        assert TwistType.MISINTERPRETED
        assert TwistType.MISSING_PIECE


class TestTwistCondition:
    """Tests for TwistCondition."""

    def test_condition_creation(self):
        """Should create a condition."""
        condition = TwistCondition(
            type="progress",
            value=0.5,
            description="Half progress"
        )
        assert condition.type == "progress"
        assert condition.value == 0.5

    def test_progress_condition_check(self):
        """Should check progress condition."""
        condition = TwistCondition(type="progress", value=0.5)

        assert condition.check({"progress": 0.6})
        assert not condition.check({"progress": 0.4})

    def test_decision_condition_check(self):
        """Should check decision condition."""
        condition = TwistCondition(type="decision", value="confronted_suspect")

        assert condition.check({"decisions": ["confronted_suspect", "other"]})
        assert not condition.check({"decisions": ["other"]})

    def test_time_condition_check(self):
        """Should check time condition."""
        condition = TwistCondition(type="time", value=100)

        assert condition.check({"time_elapsed": 150})
        assert not condition.check({"time_elapsed": 50})

    def test_discovery_condition_check(self):
        """Should check discovery condition."""
        condition = TwistCondition(type="discovery", value="key_evidence")

        assert condition.check({"discoveries": ["key_evidence"]})
        assert not condition.check({"discoveries": []})

    def test_random_condition_check(self):
        """Should check random condition probabilistically."""
        condition = TwistCondition(type="random", value=1.0)  # Always true
        assert condition.check({})

        condition = TwistCondition(type="random", value=0.0)  # Always false
        assert not condition.check({})

    def test_serialization(self):
        """Should serialize and deserialize."""
        condition = TwistCondition(
            type="progress",
            value=0.7,
            description="Late game"
        )

        data = condition.to_dict()
        restored = TwistCondition.from_dict(data)

        assert restored.type == "progress"
        assert restored.value == 0.7


class TestTwist:
    """Tests for Twist dataclass."""

    def test_twist_creation(self):
        """Should create a twist."""
        twist = Twist(
            id="test_twist",
            twist_type=TwistType.BETRAYAL,
            name="Betrayal",
            description="Someone betrays you"
        )
        assert twist.id == "test_twist"
        assert twist.twist_type == TwistType.BETRAYAL

    def test_check_trigger_no_conditions(self):
        """Should not trigger without conditions."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )
        assert not twist.check_trigger({})

    def test_check_trigger_all_conditions(self):
        """Should trigger when all conditions met."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.5),
                TwistCondition(type="decision", value="key_decision")
            ],
            require_all_conditions=True
        )

        game_state = {"progress": 0.6, "decisions": ["key_decision"]}
        assert twist.check_trigger(game_state)

    def test_check_trigger_any_condition(self):
        """Should trigger when any condition met."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.8),
                TwistCondition(type="decision", value="easy_decision")
            ],
            require_all_conditions=False
        )

        game_state = {"progress": 0.3, "decisions": ["easy_decision"]}
        assert twist.check_trigger(game_state)

    def test_trigger_marks_triggered(self):
        """Triggering should mark as triggered."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )
        assert not twist.triggered

        twist.trigger()
        assert twist.triggered

    def test_cannot_trigger_twice(self):
        """Should not trigger again after triggered."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.1)
            ]
        )

        twist.trigger()
        assert not twist.check_trigger({"progress": 1.0})

    def test_reveal(self):
        """Should reveal and return text."""
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            revelation_text="The truth is revealed!"
        )

        text = twist.reveal()
        assert text == "The truth is revealed!"
        assert twist.revealed

    def test_serialization(self):
        """Should serialize and deserialize."""
        twist = Twist(
            id="test",
            twist_type=TwistType.HIDDEN_IDENTITY,
            name="Hidden Identity",
            description="Someone has a secret",
            revelation_text="The truth!",
            affected_characters=["char1"],
            changes_culprit=True,
            new_culprit_id="char2",
            tension_change=0.3,
            triggered=True,
            revealed=False
        )

        data = twist.to_dict()
        restored = Twist.from_dict(data)

        assert restored.id == "test"
        assert restored.twist_type == TwistType.HIDDEN_IDENTITY
        assert restored.changes_culprit is True
        assert restored.triggered is True


class TestTwistManager:
    """Tests for TwistManager."""

    def test_manager_creation(self):
        """Should create manager."""
        manager = TwistManager()
        assert len(manager.twists) == 0

    def test_add_twist(self):
        """Should add twist."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )

        manager.add_twist(twist)
        assert len(manager.twists) == 1

    def test_remove_twist(self):
        """Should remove twist by ID."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )

        manager.add_twist(twist)
        assert manager.remove_twist("test")
        assert len(manager.twists) == 0

    def test_get_twist(self):
        """Should get twist by ID."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )

        manager.add_twist(twist)
        found = manager.get_twist("test")
        assert found is twist

    def test_check_triggers(self):
        """Should check and return newly triggered twists."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.5)
            ]
        )

        manager.add_twist(twist)
        triggered = manager.check_triggers({"progress": 0.6})

        assert len(triggered) == 1
        assert triggered[0].id == "test"

    def test_reveal_twist(self):
        """Should reveal a triggered twist."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            revelation_text="Revealed!"
        )
        twist.trigger()

        manager.add_twist(twist)
        text = manager.reveal_twist("test")

        assert text == "Revealed!"

    def test_reveal_untriggered_returns_none(self):
        """Should return None for untriggered twist."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )

        manager.add_twist(twist)
        text = manager.reveal_twist("test")

        assert text is None

    def test_get_pending_revelations(self):
        """Should get triggered but unrevealed twists."""
        manager = TwistManager()
        twist1 = Twist(
            id="test1",
            twist_type=TwistType.BETRAYAL,
            name="Test1",
            description="Test"
        )
        twist1.trigger()

        twist2 = Twist(
            id="test2",
            twist_type=TwistType.BETRAYAL,
            name="Test2",
            description="Test"
        )
        twist2.trigger()
        twist2.reveal()

        manager.add_twist(twist1)
        manager.add_twist(twist2)

        pending = manager.get_pending_revelations()
        assert len(pending) == 1
        assert pending[0].id == "test1"

    def test_get_story_impact(self):
        """Should calculate cumulative story impact."""
        manager = TwistManager()
        twist1 = Twist(
            id="test1",
            twist_type=TwistType.BETRAYAL,
            name="Test1",
            description="Test",
            tension_change=0.2,
            reveals_facts=["fact1"]
        )
        twist1.trigger()
        twist1.reveal()

        twist2 = Twist(
            id="test2",
            twist_type=TwistType.DEEPER_CONSPIRACY,
            name="Test2",
            description="Test",
            tension_change=0.3,
            reveals_facts=["fact2"],
            changes_culprit=True,
            new_culprit_id="new_culprit"
        )
        twist2.trigger()
        twist2.reveal()

        manager.add_twist(twist1)
        manager.add_twist(twist2)

        impact = manager.get_story_impact()
        assert impact["tension_change"] == 0.5
        assert "fact1" in impact["revealed_facts"]
        assert "fact2" in impact["revealed_facts"]
        assert impact["culprit_changed"] is True
        assert impact["current_culprit"] == "new_culprit"

    def test_on_trigger_callback(self):
        """Should call trigger callback."""
        manager = TwistManager()
        triggered_twists = []

        manager.on_trigger(lambda t: triggered_twists.append(t))

        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.1)
            ]
        )
        manager.add_twist(twist)
        manager.check_triggers({"progress": 0.5})

        assert len(triggered_twists) == 1

    def test_serialization(self):
        """Should serialize and deserialize."""
        manager = TwistManager()
        twist = Twist(
            id="test",
            twist_type=TwistType.BETRAYAL,
            name="Test",
            description="Test"
        )
        manager.add_twist(twist)

        data = manager.to_dict()
        restored = TwistManager.from_dict(data)

        assert len(restored.twists) == 1
        assert restored.twists[0].id == "test"


class TestTwistGenerator:
    """Tests for TwistGenerator."""

    def test_generator_creation(self):
        """Should create generator."""
        generator = TwistGenerator()
        assert generator is not None

    def test_generator_with_seed(self):
        """Should be reproducible with seed."""
        gen1 = TwistGenerator(seed=42)
        twist1 = gen1.generate_character_twist("char1")

        gen2 = TwistGenerator(seed=42)
        twist2 = gen2.generate_character_twist("char1")

        assert twist1.twist_type == twist2.twist_type

    def test_generate_character_twist(self):
        """Should generate character twist."""
        generator = TwistGenerator()
        twist = generator.generate_character_twist("suspect_a")

        assert "suspect_a" in twist.affected_characters
        assert twist.twist_type in [
            TwistType.HIDDEN_IDENTITY,
            TwistType.SECRET_ALLY,
            TwistType.BETRAYAL,
            TwistType.REDEMPTION
        ]

    def test_generate_character_twist_specific_type(self):
        """Should generate specific character twist type."""
        generator = TwistGenerator()
        twist = generator.generate_character_twist(
            "suspect_a",
            twist_type=TwistType.BETRAYAL
        )

        assert twist.twist_type == TwistType.BETRAYAL

    def test_generate_plot_twist(self):
        """Should generate plot twist."""
        generator = TwistGenerator()
        twist = generator.generate_plot_twist()

        assert twist.twist_type in [
            TwistType.WRONG_CRIME,
            TwistType.MULTIPLE_CULPRITS,
            TwistType.DEEPER_CONSPIRACY,
            TwistType.NO_CRIME
        ]

    def test_generate_plot_twist_specific_type(self):
        """Should generate specific plot twist type."""
        generator = TwistGenerator()
        twist = generator.generate_plot_twist(
            twist_type=TwistType.DEEPER_CONSPIRACY
        )

        assert twist.twist_type == TwistType.DEEPER_CONSPIRACY

    def test_generate_evidence_twist(self):
        """Should generate evidence twist."""
        generator = TwistGenerator()
        twist = generator.generate_evidence_twist("murder_weapon")

        assert twist.twist_type in [
            TwistType.PLANTED_EVIDENCE,
            TwistType.MISINTERPRETED,
            TwistType.MISSING_PIECE
        ]

    def test_generated_twists_have_conditions(self):
        """Generated twists should have trigger conditions."""
        generator = TwistGenerator()

        char_twist = generator.generate_character_twist("char1")
        assert len(char_twist.trigger_conditions) > 0

        plot_twist = generator.generate_plot_twist()
        assert len(plot_twist.trigger_conditions) > 0

        evidence_twist = generator.generate_evidence_twist()
        assert len(evidence_twist.trigger_conditions) > 0
