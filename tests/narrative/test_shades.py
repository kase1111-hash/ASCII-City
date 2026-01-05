"""Tests for the moral shades system."""

import pytest
from src.shadowengine.narrative.shades import (
    MoralShade, MoralDecision, ShadeProfile,
    ShadeNarrator, NarrationStyle, Ending, EndingDeterminator,
    DECISION_TEMPLATES, SHADE_STYLES, ENDINGS
)


class TestMoralShade:
    """Tests for MoralShade enum."""

    def test_all_shades_defined(self):
        """All moral shades should be defined."""
        assert MoralShade.PRAGMATIC
        assert MoralShade.CORRUPT
        assert MoralShade.COMPASSIONATE
        assert MoralShade.RUTHLESS
        assert MoralShade.IDEALISTIC


class TestMoralDecision:
    """Tests for MoralDecision dataclass."""

    def test_decision_creation(self):
        """Should create a decision with effects."""
        decision = MoralDecision(
            id="test_decision",
            description="A test decision",
            shade_effects={MoralShade.PRAGMATIC: 2}
        )
        assert decision.id == "test_decision"
        assert decision.shade_effects[MoralShade.PRAGMATIC] == 2

    def test_decision_serialization(self):
        """Should serialize and deserialize correctly."""
        decision = MoralDecision(
            id="test",
            description="Test",
            shade_effects={MoralShade.CORRUPT: 3},
            timestamp=1.0,
            context="test_context"
        )

        data = decision.to_dict()
        restored = MoralDecision.from_dict(data)

        assert restored.id == decision.id
        assert restored.shade_effects[MoralShade.CORRUPT] == 3


class TestShadeProfile:
    """Tests for ShadeProfile."""

    def test_initial_scores_are_zero(self):
        """All initial shade scores should be zero."""
        profile = ShadeProfile()
        for shade in MoralShade:
            assert profile.scores[shade] == 0

    def test_apply_decision(self):
        """Applying decision should update scores."""
        profile = ShadeProfile()
        decision = MoralDecision(
            id="test",
            description="Test",
            shade_effects={MoralShade.RUTHLESS: 5}
        )

        profile.apply_decision(decision)

        assert profile.scores[MoralShade.RUTHLESS] == 5
        assert len(profile.decisions) == 1

    def test_get_dominant_shade(self):
        """Should return shade with highest score."""
        profile = ShadeProfile()
        profile.scores[MoralShade.COMPASSIONATE] = 10

        assert profile.get_dominant_shade() == MoralShade.COMPASSIONATE

    def test_get_dominant_shade_default(self):
        """Should return PRAGMATIC when no scores."""
        profile = ShadeProfile()
        assert profile.get_dominant_shade() == MoralShade.PRAGMATIC

    def test_get_shade_strength(self):
        """Should calculate relative shade strength."""
        profile = ShadeProfile()
        profile.scores[MoralShade.IDEALISTIC] = 10
        profile.scores[MoralShade.CORRUPT] = 10

        strength = profile.get_shade_strength(MoralShade.IDEALISTIC)
        assert strength == 0.5  # 10/(10+10)

    def test_is_conflicted(self):
        """Should detect when no clear dominant shade."""
        profile = ShadeProfile()
        profile.scores[MoralShade.PRAGMATIC] = 5
        profile.scores[MoralShade.RUTHLESS] = 5
        profile.scores[MoralShade.COMPASSIONATE] = 5
        profile.scores[MoralShade.CORRUPT] = 5
        profile.scores[MoralShade.IDEALISTIC] = 5

        assert profile.is_conflicted()

    def test_not_conflicted_with_clear_dominant(self):
        """Should not be conflicted with clear dominant shade."""
        profile = ShadeProfile()
        profile.scores[MoralShade.RUTHLESS] = 20

        assert not profile.is_conflicted()

    def test_serialization(self):
        """Should serialize and deserialize correctly."""
        profile = ShadeProfile()
        profile.scores[MoralShade.CORRUPT] = 15
        profile.apply_decision(MoralDecision(
            id="test",
            description="Test",
            shade_effects={MoralShade.CORRUPT: 5}
        ))

        data = profile.to_dict()
        restored = ShadeProfile.from_dict(data)

        # Score is 15 + 5 = 20 after applying the decision
        assert restored.scores[MoralShade.CORRUPT] == 20
        assert len(restored.decisions) == 1


class TestDecisionTemplates:
    """Tests for predefined decision templates."""

    def test_evidence_templates_exist(self):
        """Evidence-related templates should exist."""
        assert "planted_evidence" in DECISION_TEMPLATES
        assert "hid_evidence" in DECISION_TEMPLATES
        assert "reported_all_evidence" in DECISION_TEMPLATES

    def test_interrogation_templates_exist(self):
        """Interrogation-related templates should exist."""
        assert "used_threats" in DECISION_TEMPLATES
        assert "showed_empathy" in DECISION_TEMPLATES
        assert "made_deal" in DECISION_TEMPLATES

    def test_templates_have_shade_effects(self):
        """All templates should have shade effects."""
        for name, effects in DECISION_TEMPLATES.items():
            assert len(effects) > 0, f"{name} has no effects"


class TestNarrationStyle:
    """Tests for NarrationStyle."""

    def test_style_creation(self):
        """Should create narration style."""
        style = NarrationStyle(
            tone="test",
            vocabulary=["word1", "word2"],
            sentence_style="short",
            perspective_phrases=["phrase1"]
        )
        assert style.tone == "test"
        assert len(style.vocabulary) == 2


class TestShadeStyles:
    """Tests for shade-specific styles."""

    def test_all_shades_have_styles(self):
        """All shades should have narration styles."""
        for shade in MoralShade:
            assert shade in SHADE_STYLES

    def test_styles_have_content(self):
        """Styles should have vocabulary and phrases."""
        for shade, style in SHADE_STYLES.items():
            assert len(style.vocabulary) > 0
            assert len(style.perspective_phrases) > 0


class TestShadeNarrator:
    """Tests for ShadeNarrator."""

    def test_narrator_creation(self):
        """Should create narrator with profile."""
        profile = ShadeProfile()
        narrator = ShadeNarrator(profile)
        assert narrator.profile is profile

    def test_get_style(self):
        """Should return style for dominant shade."""
        profile = ShadeProfile()
        profile.scores[MoralShade.RUTHLESS] = 20
        narrator = ShadeNarrator(profile)

        style = narrator.get_style()
        assert style == SHADE_STYLES[MoralShade.RUTHLESS]

    def test_get_internal_thought(self):
        """Should return characteristic thought."""
        profile = ShadeProfile()
        profile.scores[MoralShade.IDEALISTIC] = 20
        narrator = ShadeNarrator(profile)

        thought = narrator.get_internal_thought()
        assert thought in SHADE_STYLES[MoralShade.IDEALISTIC].perspective_phrases

    def test_narrate_discovery(self):
        """Should generate shade-appropriate discovery text."""
        profile = ShadeProfile()
        profile.scores[MoralShade.CORRUPT] = 20
        narrator = ShadeNarrator(profile)

        text = narrator.narrate_discovery("the key")
        assert "key" in text
        assert "value" in text.lower()  # Corrupt cares about value

    def test_narrate_confrontation(self):
        """Should generate shade-appropriate confrontation text."""
        profile = ShadeProfile()
        profile.scores[MoralShade.COMPASSIONATE] = 20
        narrator = ShadeNarrator(profile)

        text = narrator.narrate_confrontation("John")
        assert "John" in text

    def test_narrate_accusation_correct(self):
        """Should generate correct accusation text."""
        profile = ShadeProfile()
        narrator = ShadeNarrator(profile)

        text = narrator.narrate_accusation("Jane", correct=True)
        assert "Jane" in text

    def test_narrate_accusation_wrong(self):
        """Should generate wrong accusation text."""
        profile = ShadeProfile()
        profile.scores[MoralShade.COMPASSIONATE] = 20
        narrator = ShadeNarrator(profile)

        text = narrator.narrate_accusation("Jane", correct=False)
        assert "Jane" in text
        assert "guilt" in text.lower()

    def test_narrate_scene_entry(self):
        """Should generate scene entry text."""
        narrator = ShadeNarrator()
        text = narrator.narrate_scene_entry("library")
        assert "library" in text


class TestEnding:
    """Tests for Ending dataclass."""

    def test_ending_creation(self):
        """Should create an ending."""
        ending = Ending(
            id="test",
            name="Test Ending",
            shade_requirement=MoralShade.RUTHLESS,
            description="A test ending"
        )
        assert ending.id == "test"
        assert ending.shade_requirement == MoralShade.RUTHLESS

    def test_check_requirements_met(self):
        """Should pass when requirements are met."""
        ending = Ending(
            id="test",
            name="Test",
            shade_requirement=MoralShade.PRAGMATIC,
            shade_strength_min=0.3,
            solved_requirement=True
        )

        profile = ShadeProfile()
        profile.scores[MoralShade.PRAGMATIC] = 20

        assert ending.check_requirements(profile, mystery_solved=True)

    def test_check_requirements_shade_not_met(self):
        """Should fail when shade requirement not met."""
        ending = Ending(
            id="test",
            name="Test",
            shade_requirement=MoralShade.CORRUPT
        )

        profile = ShadeProfile()
        profile.scores[MoralShade.IDEALISTIC] = 20

        assert not ending.check_requirements(profile, mystery_solved=True)

    def test_check_requirements_solved_not_met(self):
        """Should fail when solved requirement not met."""
        ending = Ending(
            id="test",
            name="Test",
            solved_requirement=True
        )

        assert not ending.check_requirements(ShadeProfile(), mystery_solved=False)


class TestPredefinedEndings:
    """Tests for predefined endings."""

    def test_endings_exist(self):
        """Should have multiple endings defined."""
        assert len(ENDINGS) >= 5  # At least one per shade

    def test_unsolved_ending_exists(self):
        """Should have an unsolved ending."""
        unsolved = [e for e in ENDINGS if not e.solved_requirement]
        assert len(unsolved) > 0


class TestEndingDeterminator:
    """Tests for EndingDeterminator."""

    def test_determinator_creation(self):
        """Should create determinator with endings."""
        determinator = EndingDeterminator()
        assert len(determinator.endings) > 0

    def test_determine_solved_ending(self):
        """Should determine appropriate solved ending."""
        determinator = EndingDeterminator()
        profile = ShadeProfile()
        profile.scores[MoralShade.RUTHLESS] = 30

        ending = determinator.determine_ending(profile, mystery_solved=True)
        assert ending.solved_requirement is True

    def test_determine_unsolved_ending(self):
        """Should return unsolved ending when not solved."""
        determinator = EndingDeterminator()

        ending = determinator.determine_ending(ShadeProfile(), mystery_solved=False)
        assert not ending.solved_requirement

    def test_get_possible_endings(self):
        """Should return all achievable endings."""
        determinator = EndingDeterminator()
        profile = ShadeProfile()
        profile.scores[MoralShade.COMPASSIONATE] = 30

        possible = determinator.get_possible_endings(profile, mystery_solved=True)
        assert len(possible) >= 1

    def test_fallback_ending(self):
        """Should return fallback when no endings match."""
        determinator = EndingDeterminator(endings=[])

        ending = determinator.determine_ending(ShadeProfile(), mystery_solved=True)
        assert ending.id == "default"
