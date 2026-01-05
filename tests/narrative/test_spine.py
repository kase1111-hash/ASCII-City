"""
Tests for Narrative Spine - the hidden story structure.

These tests verify that narrative spines correctly:
- Generate coherent story structures
- Track revelations and progress
- Validate solutions
- Support procedural generation (expandable for LLM)
"""

import pytest
from shadowengine.narrative import (
    NarrativeSpine, SpineGenerator, ConflictType,
    TrueResolution, Revelation, RedHerring
)


class TestNarrativeSpineBasics:
    """Basic narrative spine functionality."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_create_basic_spine(self, basic_spine):
        """Can create a basic narrative spine."""
        assert basic_spine.conflict_type == ConflictType.THEFT
        assert basic_spine.true_resolution is not None
        assert len(basic_spine.revelations) == 3

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_spine_starts_unsolved(self, basic_spine):
        """Spine starts in unsolved state."""
        assert basic_spine.is_solved is False
        assert len(basic_spine.revealed_facts) == 0


class TestRevelations:
    """Revelation tracking and prerequisites."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_check_revelation_no_prereqs(self, basic_spine):
        """Revelations without prereqs can be made immediately."""
        assert basic_spine.check_revelation("clue_1") is True

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_check_revelation_with_prereqs(self, basic_spine):
        """Revelations with prereqs require those first."""
        # clue_2 requires clue_1
        assert basic_spine.check_revelation("clue_2") is False

        # Make clue_1 first
        basic_spine.make_revelation("clue_1")

        # Now clue_2 is available
        assert basic_spine.check_revelation("clue_2") is True

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_make_revelation(self, basic_spine):
        """Can make revelations."""
        result = basic_spine.make_revelation("clue_1")

        assert result is True
        assert "clue_1" in basic_spine.revealed_facts

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_cannot_make_blocked_revelation(self, basic_spine):
        """Cannot make revelation without prereqs."""
        result = basic_spine.make_revelation("clue_2")

        assert result is False
        assert "clue_2" not in basic_spine.revealed_facts

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_get_revelation_by_id(self, basic_spine):
        """Can get revelation by ID."""
        rev = basic_spine.get_revelation("clue_1")

        assert rev is not None
        assert rev.id == "clue_1"

        # Non-existent
        assert basic_spine.get_revelation("nonexistent") is None

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_get_available_revelations(self, basic_spine):
        """Get currently available revelations."""
        available = basic_spine.get_available_revelations()

        # Initially only clue_1 available
        assert len(available) == 1
        assert available[0].id == "clue_1"

        # Make clue_1
        basic_spine.make_revelation("clue_1")
        available = basic_spine.get_available_revelations()

        # Now clue_2 available
        assert len(available) == 1
        assert available[0].id == "clue_2"


class TestProgressTracking:
    """Story progress tracking."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_initial_progress_zero(self, basic_spine):
        """Progress starts at 0%."""
        assert basic_spine.get_progress() == 0.0

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_progress_increases(self, basic_spine):
        """Progress increases with revelations."""
        basic_spine.make_revelation("clue_1")
        progress = basic_spine.get_progress()

        assert progress == pytest.approx(1/3, abs=0.01)

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_full_progress(self, basic_spine, helpers):
        """Full progress when all revelations made."""
        helpers.discover_all_revelations(basic_spine, None)

        assert basic_spine.get_progress() == pytest.approx(1.0, abs=0.01)


class TestSolutionValidation:
    """Solution checking mechanics."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_wrong_culprit(self, basic_spine):
        """Wrong culprit fails."""
        is_correct, msg = basic_spine.check_solution(
            accused_id="wrong_person",
            evidence={"clue_1", "clue_2", "clue_3"}
        )

        assert is_correct is False
        assert "not the right person" in msg.lower()

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_correct_culprit_insufficient_evidence(self, basic_spine):
        """Right culprit with insufficient evidence."""
        is_correct, msg = basic_spine.check_solution(
            accused_id="culprit",
            evidence={"clue_1"}  # Only 1 of 3
        )

        assert is_correct is False
        assert "evidence" in msg.lower()

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_correct_solution(self, basic_spine):
        """Correct culprit with sufficient evidence."""
        is_correct, msg = basic_spine.check_solution(
            accused_id="culprit",
            evidence={"clue_1", "clue_2", "clue_3"}
        )

        assert is_correct is True
        assert basic_spine.is_solved is True

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_partial_evidence_threshold(self, basic_spine):
        """70% evidence threshold works."""
        # 2 of 3 = 66% - should fail
        is_correct_66, _ = basic_spine.check_solution(
            accused_id="culprit",
            evidence={"clue_1", "clue_2"}
        )

        # Reset for next test
        basic_spine.is_solved = False

        # 3 of 3 = 100% - should pass
        is_correct_100, _ = basic_spine.check_solution(
            accused_id="culprit",
            evidence={"clue_1", "clue_2", "clue_3"}
        )

        assert is_correct_100 is True


class TestTwistMechanics:
    """Twist probability mechanics."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_twist_not_triggered_early(self):
        """Twists don't trigger early in story."""
        spine = NarrativeSpine(
            conflict_type=ConflictType.MURDER,
            conflict_description="A murder",
            true_resolution=TrueResolution(
                culprit_id="killer",
                motive="revenge",
                method="poison",
                opportunity="alone",
                evidence_chain=["a", "b"]
            ),
            revelations=[
                Revelation(id="a", description="A", importance=1),
                Revelation(id="b", description="B", importance=2)
            ],
            twist_probability=1.0,  # 100% chance
            twist_type="sympathetic"
        )

        # Early in story (0 progress)
        assert spine.should_trigger_twist() is False

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_zero_twist_probability(self):
        """No twist with 0% probability."""
        spine = NarrativeSpine(
            conflict_type=ConflictType.THEFT,
            conflict_description="Theft",
            true_resolution=TrueResolution(
                culprit_id="thief",
                motive="greed",
                method="stealth",
                opportunity="night",
                evidence_chain=["a"]
            ),
            revelations=[Revelation(id="a", description="A", importance=1)],
            twist_probability=0.0
        )

        # Even at full progress
        spine.make_revelation("a")
        assert spine.should_trigger_twist() is False


class TestSpineGenerator:
    """Procedural spine generation."""

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    def test_generator_with_seed(self, spine_generator):
        """Generator with seed produces consistent results."""
        spine1 = spine_generator.generate(conflict_type=ConflictType.THEFT)

        # Create new generator with same seed
        gen2 = SpineGenerator(seed=42)
        spine2 = gen2.generate(conflict_type=ConflictType.THEFT)

        assert spine1.conflict_type == spine2.conflict_type

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    def test_generate_theft_spine(self, spine_generator):
        """Can generate theft spine."""
        spine = spine_generator.generate(
            conflict_type=ConflictType.THEFT,
            characters=["alice", "bob", "charlie"]
        )

        assert spine.conflict_type == ConflictType.THEFT
        assert spine.true_resolution.culprit_id in ["alice", "bob"]
        assert len(spine.revelations) > 0

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    def test_generate_murder_spine(self, spine_generator):
        """Can generate murder spine."""
        spine = spine_generator.generate(
            conflict_type=ConflictType.MURDER,
            characters=["suspect_a", "suspect_b", "victim"]
        )

        assert spine.conflict_type == ConflictType.MURDER
        assert "revenge" in spine.true_resolution.motive or len(spine.true_resolution.motive) > 0

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    @pytest.mark.parametrize("conflict_type", list(ConflictType))
    def test_generate_all_conflict_types(self, spine_generator, conflict_type):
        """Can generate spines for all conflict types."""
        spine = spine_generator.generate(
            conflict_type=conflict_type,
            characters=["a", "b", "c"]
        )

        assert spine.conflict_type == conflict_type
        assert spine.true_resolution is not None

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    def test_random_conflict_type(self, spine_generator):
        """Generator picks random conflict type when not specified."""
        spine = spine_generator.generate(characters=["a", "b"])

        assert spine.conflict_type in ConflictType

    @pytest.mark.unit
    @pytest.mark.narrative
    @pytest.mark.procedural
    def test_twist_probability_passed(self, spine_generator):
        """Twist probability is set correctly."""
        spine = spine_generator.generate(
            conflict_type=ConflictType.THEFT,
            twist_chance=0.75
        )

        assert spine.twist_probability == 0.75


class TestSpineSerialization:
    """Serialization and deserialization."""

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_serialize_spine(self, basic_spine):
        """Can serialize spine."""
        basic_spine.make_revelation("clue_1")
        data = basic_spine.to_dict()

        assert data["conflict_type"] == "theft"
        assert "true_resolution" in data
        assert len(data["revelations"]) == 3
        assert "clue_1" in data["revealed_facts"]

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_deserialize_spine(self, basic_spine):
        """Can deserialize spine."""
        basic_spine.make_revelation("clue_1")
        data = basic_spine.to_dict()

        restored = NarrativeSpine.from_dict(data)

        assert restored.conflict_type == ConflictType.THEFT
        assert "clue_1" in restored.revealed_facts
        assert len(restored.revelations) == 3

    @pytest.mark.unit
    @pytest.mark.narrative
    def test_roundtrip_preserves_state(self, basic_spine):
        """Roundtrip preserves complete state."""
        basic_spine.make_revelation("clue_1")
        basic_spine.twist_probability = 0.5
        basic_spine.twist_type = "double_cross"

        data = basic_spine.to_dict()
        restored = NarrativeSpine.from_dict(data)

        assert restored.twist_probability == 0.5
        assert restored.twist_type == "double_cross"
        assert restored.check_revelation("clue_2") is True


class TestProceduralExpansion:
    """Tests designed to expand with LLM integration.

    These tests establish patterns for procedural generation
    that can be extended when LLM-based generation is added.
    """

    @pytest.mark.procedural
    @pytest.mark.narrative
    def test_spine_coherence(self, generation_seeds):
        """Generated spines are internally coherent."""
        for seed in generation_seeds:
            gen = SpineGenerator(seed=seed)
            spine = gen.generate()

            # Culprit exists
            assert spine.true_resolution.culprit_id is not None

            # Has method and motive
            assert spine.true_resolution.method is not None
            assert spine.true_resolution.motive is not None

            # Revelations form valid chain
            assert len(spine.revelations) > 0

    @pytest.mark.procedural
    @pytest.mark.narrative
    def test_revelation_chain_solvable(self, generation_seeds):
        """All generated revelation chains are solvable."""
        for seed in generation_seeds:
            gen = SpineGenerator(seed=seed)
            spine = gen.generate()

            # Should be able to discover all revelations in order
            discovered = []
            max_iterations = 100

            for _ in range(max_iterations):
                available = spine.get_available_revelations()
                if not available:
                    break

                spine.make_revelation(available[0].id)
                discovered.append(available[0].id)

            # All revelations should be discoverable
            assert len(discovered) == len(spine.revelations)

    @pytest.mark.procedural
    @pytest.mark.narrative
    @pytest.mark.slow
    def test_generation_variety(self, conflict_types):
        """Different seeds produce variety."""
        spines = []

        for i, conflict in enumerate(conflict_types[:3]):
            gen = SpineGenerator(seed=i * 100)
            spine = gen.generate(conflict_type=conflict)
            spines.append(spine)

        # Should have different conflict types
        types = {s.conflict_type for s in spines}
        assert len(types) == 3
