"""Extended tests for narrative systems."""

import pytest
from src.shadowengine.narrative import (
    NarrativeSpine, SpineGenerator, ConflictType,
    TrueResolution, Revelation, RedHerring,
    MoralShade, MoralDecision, ShadeProfile,
    ShadeNarrator, NarrationStyle, Ending, EndingDeterminator,
    DECISION_TEMPLATES, SHADE_STYLES, ENDINGS,
    TwistType, TwistCondition, Twist,
    TwistManager, TwistGenerator
)


class TestShadeDecisionCombinations:
    """Tests for moral shade decision combinations."""

    def test_conflicting_decisions(self):
        """Profile should handle conflicting decisions."""
        profile = ShadeProfile()

        # Make conflicting decisions
        profile.apply_decision(MoralDecision(
            "compassionate1", "Helped",
            {MoralShade.COMPASSIONATE: 5}
        ))
        profile.apply_decision(MoralDecision(
            "ruthless1", "Punished",
            {MoralShade.RUTHLESS: 5}
        ))

        # Should be conflicted or have slight lean
        assert profile.get_dominant_strength() <= 0.5 or profile.is_conflicted()

    def test_multiple_shade_effects(self):
        """Decisions can affect multiple shades."""
        profile = ShadeProfile()

        # Decision with multiple effects
        profile.apply_decision(MoralDecision(
            "complex", "Complex choice",
            {
                MoralShade.PRAGMATIC: 3,
                MoralShade.CORRUPT: 1,
                MoralShade.RUTHLESS: 2
            }
        ))

        assert profile.scores[MoralShade.PRAGMATIC] == 3
        assert profile.scores[MoralShade.CORRUPT] == 1
        assert profile.scores[MoralShade.RUTHLESS] == 2

    def test_negative_effects(self):
        """Decisions can have negative effects on shades."""
        profile = ShadeProfile()
        profile.scores[MoralShade.IDEALISTIC] = 10

        # Decision that reduces idealistic
        profile.apply_decision(MoralDecision(
            "compromise", "Made a compromise",
            {MoralShade.IDEALISTIC: -5, MoralShade.PRAGMATIC: 3}
        ))

        assert profile.scores[MoralShade.IDEALISTIC] == 5
        assert profile.scores[MoralShade.PRAGMATIC] == 3

    def test_all_decision_templates_are_valid(self):
        """All decision templates should have valid shade effects."""
        profile = ShadeProfile()

        for template_name, effects in DECISION_TEMPLATES.items():
            decision = MoralDecision(
                template_name, template_name, effects
            )
            # Should not raise
            profile.apply_decision(decision)

        # Profile should have been affected
        total = sum(abs(v) for v in profile.scores.values())
        assert total > 0


class TestNarratorEdgeCases:
    """Edge cases for shade narrator."""

    def test_narrator_with_equal_shades(self):
        """Narrator should work with equal shade scores."""
        profile = ShadeProfile()
        for shade in MoralShade:
            profile.scores[shade] = 10

        narrator = ShadeNarrator(profile)

        # Should not crash and return something
        text = narrator.narrate_discovery("item")
        assert isinstance(text, str)

    def test_narrator_with_zero_scores(self):
        """Narrator should work with all zero scores."""
        profile = ShadeProfile()
        narrator = ShadeNarrator(profile)

        text = narrator.narrate_confrontation("suspect")
        assert isinstance(text, str)
        assert "suspect" in text

    def test_narrator_all_shade_texts_unique(self):
        """Each shade should produce distinct narration style."""
        discovery_texts = set()
        confrontation_texts = set()

        for shade in MoralShade:
            profile = ShadeProfile()
            profile.scores[shade] = 100
            narrator = ShadeNarrator(profile)

            discovery_texts.add(narrator.narrate_discovery("key"))
            confrontation_texts.add(narrator.narrate_confrontation("John"))

        # Should have multiple unique texts
        assert len(discovery_texts) >= 3
        assert len(confrontation_texts) >= 3


class TestEndingDetermination:
    """Extended tests for ending determination."""

    def test_all_shade_endings_achievable(self):
        """Each shade should have an achievable ending."""
        determinator = EndingDeterminator()

        for shade in MoralShade:
            profile = ShadeProfile()
            profile.scores[shade] = 100  # Dominant in this shade

            ending = determinator.determine_ending(profile, mystery_solved=True)

            # Should get an ending (either shade-specific or neutral)
            assert ending is not None

    def test_unsolved_endings_available(self):
        """Unsolved game should still get an ending."""
        determinator = EndingDeterminator()

        for shade in MoralShade:
            profile = ShadeProfile()
            profile.scores[shade] = 100

            ending = determinator.determine_ending(profile, mystery_solved=False)
            assert ending is not None
            assert not ending.solved_requirement

    def test_ending_epilogues_exist(self):
        """All predefined endings should have epilogues."""
        for ending in ENDINGS:
            assert ending.epilogue
            assert len(ending.epilogue) > 0


class TestTwistConditions:
    """Extended tests for twist conditions."""

    def test_condition_with_missing_context(self):
        """Conditions should handle missing context gracefully."""
        condition = TwistCondition(type="progress", value=0.5)

        # Missing progress key
        result = condition.check({})
        assert result is False  # Should not match

    def test_all_condition_types(self):
        """All condition types should be testable."""
        conditions = [
            (TwistCondition(type="progress", value=0.5), {"progress": 0.6}, True),
            (TwistCondition(type="progress", value=0.5), {"progress": 0.3}, False),
            (TwistCondition(type="decision", value="key"), {"decisions": ["key"]}, True),
            (TwistCondition(type="decision", value="key"), {"decisions": []}, False),
            (TwistCondition(type="time", value=100), {"time_elapsed": 150}, True),
            (TwistCondition(type="time", value=100), {"time_elapsed": 50}, False),
            (TwistCondition(type="discovery", value="clue"), {"discoveries": ["clue"]}, True),
            (TwistCondition(type="discovery", value="clue"), {"discoveries": []}, False),
        ]

        for condition, context, expected in conditions:
            assert condition.check(context) == expected

    def test_random_condition_boundaries(self):
        """Random condition should respect probability boundaries."""
        # Always true
        always_true = TwistCondition(type="random", value=1.0)
        assert all(always_true.check({}) for _ in range(10))

        # Always false
        always_false = TwistCondition(type="random", value=0.0)
        assert not any(always_false.check({}) for _ in range(10))


class TestTwistInteractions:
    """Tests for twist interactions and combinations."""

    def test_multiple_twists_same_type(self):
        """Multiple twists of same type should work."""
        manager = TwistManager()

        for i in range(3):
            twist = Twist(
                id=f"betrayal_{i}",
                twist_type=TwistType.BETRAYAL,
                name=f"Betrayal {i}",
                description=f"Character {i} betrays",
                trigger_conditions=[
                    TwistCondition(type="progress", value=0.3 + i * 0.2)
                ]
            )
            manager.add_twist(twist)

        # Trigger at different progress levels
        manager.check_triggers({"progress": 0.35})
        assert len(manager.get_triggered_twists()) == 1

        manager.check_triggers({"progress": 0.55})
        assert len(manager.get_triggered_twists()) == 2

    def test_twist_chain_dependencies(self):
        """Twists can depend on other twists being triggered."""
        manager = TwistManager()

        # First twist
        twist1 = Twist(
            id="first",
            twist_type=TwistType.HIDDEN_IDENTITY,
            name="First Twist",
            description="First revelation",
            trigger_conditions=[
                TwistCondition(type="progress", value=0.3)
            ],
            reveals_facts=["identity_known"]
        )

        # Second twist depends on first
        twist2 = Twist(
            id="second",
            twist_type=TwistType.DEEPER_CONSPIRACY,
            name="Second Twist",
            description="Goes deeper",
            trigger_conditions=[
                TwistCondition(type="discovery", value="identity_known")
            ]
        )

        manager.add_twist(twist1)
        manager.add_twist(twist2)

        # Trigger first
        manager.check_triggers({"progress": 0.4})
        manager.reveal_twist("first")

        # Now second can trigger
        manager.check_triggers({"discoveries": ["identity_known"]})

        assert len(manager.get_triggered_twists()) == 2

    def test_twist_generator_variety(self):
        """Generator should produce variety of twists."""
        generator = TwistGenerator()

        character_twists = [
            generator.generate_character_twist(f"char_{i}")
            for i in range(10)
        ]

        twist_types = set(t.twist_type for t in character_twists)

        # Should have variety (at least 2 different types)
        assert len(twist_types) >= 2


class TestSpineRevelations:
    """Extended tests for narrative spine revelations."""

    def test_revelation_prerequisites_chain(self):
        """Revelations with prerequisites should work correctly."""
        spine = NarrativeSpine(
            conflict_type=ConflictType.MURDER,
            conflict_description="A murder",
            true_resolution=TrueResolution(
                culprit_id="villain",
                motive="greed",
                method="poison",
                opportunity="dinner",
                evidence_chain=["clue1", "clue2"]
            ),
            revelations=[
                Revelation(id="base", description="Base fact", importance=1),
                Revelation(id="derived", description="Derived fact", importance=2, prerequisites=["base"]),
                Revelation(id="final", description="Final fact", importance=3, prerequisites=["derived"]),
            ]
        )

        # Cannot make final without chain
        assert not spine.check_revelation("final")
        assert not spine.check_revelation("derived")

        # Can make base
        assert spine.check_revelation("base")
        spine.make_revelation("base")

        # Now can make derived
        assert spine.check_revelation("derived")
        spine.make_revelation("derived")

        # Now can make final
        assert spine.check_revelation("final")

    def test_solution_partial_evidence(self):
        """Solution checking with partial evidence."""
        spine = NarrativeSpine(
            conflict_type=ConflictType.THEFT,
            conflict_description="A theft",
            true_resolution=TrueResolution(
                culprit_id="thief",
                motive="money",
                method="broke in",
                opportunity="night",
                evidence_chain=["evidence1", "evidence2", "evidence3", "evidence4", "evidence5"]
            )
        )

        # Wrong person
        solved, msg = spine.check_solution("wrong_person", {"evidence1", "evidence2"})
        assert not solved

        # Right person, not enough evidence (< 70%)
        solved, msg = spine.check_solution("thief", {"evidence1", "evidence2"})
        assert not solved

        # Right person, enough evidence (>= 70%)
        solved, msg = spine.check_solution("thief", {"evidence1", "evidence2", "evidence3", "evidence4"})
        assert solved


class TestSpineGenerator:
    """Extended tests for spine generator."""

    def test_generator_all_conflict_types(self):
        """Generator should handle all conflict types."""
        generator = SpineGenerator(seed=42)

        for conflict_type in ConflictType:
            spine = generator.generate(conflict_type=conflict_type)

            assert spine.conflict_type == conflict_type
            assert spine.true_resolution is not None
            assert len(spine.revelations) > 0

    def test_generator_with_custom_characters(self):
        """Generator should use provided characters."""
        generator = SpineGenerator(seed=42)
        characters = ["alice", "bob", "charlie", "diana"]

        spine = generator.generate(
            conflict_type=ConflictType.MURDER,
            characters=characters
        )

        # Culprit should be from provided characters
        assert spine.true_resolution.culprit_id in characters

    def test_generator_twist_probability(self):
        """Generator should respect twist probability."""
        generator = SpineGenerator(seed=42)

        # With twist
        spine_with_twist = generator.generate(twist_chance=1.0)
        assert spine_with_twist.twist_probability == 1.0

        # Without twist
        generator = SpineGenerator(seed=42)
        spine_no_twist = generator.generate(twist_chance=0.0)
        assert spine_no_twist.twist_probability == 0.0


class TestShadeStylesCompleteness:
    """Tests for shade styles completeness."""

    def test_all_shades_have_styles(self):
        """Every shade should have a complete style."""
        for shade in MoralShade:
            assert shade in SHADE_STYLES
            style = SHADE_STYLES[shade]

            assert style.tone
            assert len(style.vocabulary) > 0
            assert style.sentence_style
            assert len(style.perspective_phrases) > 0

    def test_styles_are_distinct(self):
        """Each shade style should be distinct."""
        tones = set()
        for shade, style in SHADE_STYLES.items():
            tones.add(style.tone)

        # Each should have unique tone
        assert len(tones) == len(MoralShade)


class TestRedHerrings:
    """Tests for red herring functionality."""

    def test_red_herring_creation(self):
        """Should create red herrings properly."""
        herring = RedHerring(
            suspect_id="innocent",
            description="Looks suspicious",
            plausibility=0.8,
            reveal_condition="early_game",
            debunk_fact="has_alibi"
        )

        assert herring.suspect_id == "innocent"
        assert herring.plausibility == 0.8

    def test_red_herring_serialization(self):
        """Red herring should serialize/deserialize."""
        original = RedHerring(
            suspect_id="suspect",
            description="Was seen near crime",
            plausibility=0.7,
            reveal_condition="examine_scene",
            debunk_fact="was_elsewhere"
        )

        data = original.to_dict()
        restored = RedHerring.from_dict(data)

        assert restored.suspect_id == original.suspect_id
        assert restored.plausibility == original.plausibility
        assert restored.debunk_fact == original.debunk_fact
