"""
Tests for PersonalityTemplate system.
"""

import pytest
from src.shadowengine.studio.personality import (
    PersonalityTemplate, IdleBehavior, ThreatResponse, Attitude,
    PERSONALITY_TEMPLATES, get_template, list_templates
)


class TestIdleBehavior:
    """Tests for IdleBehavior enum."""

    def test_behaviors_exist(self):
        """All idle behaviors exist."""
        expected = [
            "STILL", "WANDER", "PATROL", "FORAGE",
            "GUARD", "SEARCH", "SLEEP", "SOCIALIZE"
        ]
        for name in expected:
            assert hasattr(IdleBehavior, name)


class TestThreatResponse:
    """Tests for ThreatResponse enum."""

    def test_responses_exist(self):
        """All threat responses exist."""
        expected = [
            "IGNORE", "FLEE", "HIDE", "ATTACK", "CHALLENGE",
            "ALERT_OTHERS", "OBSERVE", "PROTECT", "PROTECT_HOARD", "BRIBE"
        ]
        for name in expected:
            assert hasattr(ThreatResponse, name)


class TestAttitude:
    """Tests for Attitude enum."""

    def test_attitudes_exist(self):
        """All attitudes exist."""
        expected = ["FRIENDLY", "NEUTRAL", "SUSPICIOUS", "HOSTILE", "AFRAID", "CURIOUS"]
        for name in expected:
            assert hasattr(Attitude, name)


class TestPersonalityTemplate:
    """Tests for PersonalityTemplate class."""

    def test_create_basic(self, basic_personality):
        """Can create basic personality."""
        assert basic_personality.name == "Basic"
        assert basic_personality.idle_behavior == IdleBehavior.WANDER  # Default
        assert basic_personality.threat_response == ThreatResponse.FLEE  # Default
        assert basic_personality.player_attitude == Attitude.NEUTRAL  # Default

    def test_default_traits(self, basic_personality):
        """Default traits are initialized."""
        assert basic_personality.get_trait("aggression") == 0.5
        assert basic_personality.get_trait("fear") == 0.5
        assert basic_personality.get_trait("curiosity") == 0.5
        assert basic_personality.get_trait("loyalty") == 0.5
        assert basic_personality.get_trait("greed") == 0.5
        assert basic_personality.get_trait("social") == 0.5

    def test_custom_traits(self, aggressive_personality):
        """Custom traits override defaults."""
        assert aggressive_personality.get_trait("aggression") == 0.9
        assert aggressive_personality.get_trait("fear") == 0.1
        assert aggressive_personality.get_trait("curiosity") == 0.4
        # Unset traits still get defaults
        assert aggressive_personality.get_trait("loyalty") == 0.5

    def test_trait_validation(self):
        """Invalid trait values raise error."""
        with pytest.raises(ValueError):
            PersonalityTemplate(
                name="Invalid",
                traits={"aggression": 1.5}  # Over 1.0
            )

        with pytest.raises(ValueError):
            PersonalityTemplate(
                name="Invalid",
                traits={"fear": -0.5}  # Under 0.0
            )

    def test_get_unknown_trait(self, basic_personality):
        """Unknown traits return 0.5."""
        assert basic_personality.get_trait("unknown_trait") == 0.5

    def test_set_trait(self, basic_personality):
        """Can set trait values."""
        basic_personality.set_trait("aggression", 0.8)
        assert basic_personality.get_trait("aggression") == 0.8

    def test_set_trait_validation(self, basic_personality):
        """Invalid set_trait raises error."""
        with pytest.raises(ValueError):
            basic_personality.set_trait("aggression", 2.0)

    def test_modify_trait(self, basic_personality):
        """Can modify traits by delta."""
        result = basic_personality.modify_trait("aggression", 0.3)
        assert result == 0.8

        # Clamping at 1.0
        result = basic_personality.modify_trait("aggression", 0.5)
        assert result == 1.0

        # Clamping at 0.0
        result = basic_personality.modify_trait("fear", -1.0)
        assert result == 0.0

    def test_is_aggressive(self, basic_personality, aggressive_personality):
        """Can check if aggressive."""
        assert not basic_personality.is_aggressive()
        assert aggressive_personality.is_aggressive()

    def test_is_fearful(self, basic_personality, timid_personality):
        """Can check if fearful."""
        assert not basic_personality.is_fearful()
        assert timid_personality.is_fearful()

    def test_is_curious(self, basic_personality):
        """Can check if curious."""
        basic_personality.set_trait("curiosity", 0.3)
        assert not basic_personality.is_curious()

        basic_personality.set_trait("curiosity", 0.6)
        assert basic_personality.is_curious()

    def test_is_social(self, basic_personality):
        """Can check if social."""
        basic_personality.set_trait("social", 0.4)
        assert not basic_personality.is_social()

        basic_personality.set_trait("social", 0.6)
        assert basic_personality.is_social()

    def test_calculate_response_high_threat(self, aggressive_personality, timid_personality):
        """High threat overrides normal behavior."""
        # Aggressive entity attacks even at high threat
        response = aggressive_personality.calculate_response(0.9)
        assert response == ThreatResponse.ATTACK

        # Fearful entity flees at high threat
        response = timid_personality.calculate_response(0.9)
        assert response == ThreatResponse.FLEE

    def test_calculate_response_loyal(self):
        """Loyal entities protect."""
        personality = PersonalityTemplate(
            name="Guard",
            traits={"loyalty": 0.9, "aggression": 0.3}
        )
        response = personality.calculate_response(0.5)
        assert response == ThreatResponse.PROTECT

    def test_calculate_response_challenge(self, aggressive_personality):
        """Aggressive entities challenge at low threat."""
        response = aggressive_personality.calculate_response(0.3)
        assert response == ThreatResponse.CHALLENGE

    def test_calculate_idle_action_curious(self, basic_personality):
        """Curious entities search when target exists."""
        basic_personality.set_trait("curiosity", 0.8)
        action = basic_personality.calculate_idle_action(has_target=True)
        assert action == IdleBehavior.SEARCH

    def test_calculate_idle_action_social(self, basic_personality):
        """Social entities socialize."""
        basic_personality.set_trait("social", 0.9)
        action = basic_personality.calculate_idle_action()
        assert action == IdleBehavior.SOCIALIZE

    def test_calculate_idle_action_greedy(self, basic_personality):
        """Greedy entities forage."""
        basic_personality.set_trait("greed", 0.9)
        basic_personality.set_trait("social", 0.3)
        action = basic_personality.calculate_idle_action()
        assert action == IdleBehavior.FORAGE

    def test_calculate_idle_action_aggressive(self, basic_personality):
        """Aggressive entities patrol."""
        basic_personality.set_trait("aggression", 0.8)
        basic_personality.set_trait("social", 0.3)
        basic_personality.set_trait("greed", 0.3)
        action = basic_personality.calculate_idle_action()
        assert action == IdleBehavior.PATROL

    def test_calculate_idle_action_default(self, basic_personality):
        """Falls back to default idle behavior."""
        # All traits at default 0.5
        action = basic_personality.calculate_idle_action()
        assert action == IdleBehavior.WANDER

    def test_copy(self, aggressive_personality):
        """Personality can be copied."""
        copy = aggressive_personality.copy()

        assert copy.name == "Aggressive (copy)"
        assert copy.get_trait("aggression") == aggressive_personality.get_trait("aggression")
        assert copy.idle_behavior == aggressive_personality.idle_behavior
        assert copy.threat_response == aggressive_personality.threat_response

        # Modifying copy doesn't affect original
        copy.set_trait("aggression", 0.1)
        assert aggressive_personality.get_trait("aggression") == 0.9

    def test_serialization(self, aggressive_personality):
        """Personality can be serialized and deserialized."""
        data = aggressive_personality.to_dict()
        restored = PersonalityTemplate.from_dict(data)

        assert restored.name == aggressive_personality.name
        assert restored.traits == aggressive_personality.traits
        assert restored.idle_behavior == aggressive_personality.idle_behavior
        assert restored.threat_response == aggressive_personality.threat_response
        assert restored.player_attitude == aggressive_personality.player_attitude

    def test_memory_and_grudge(self, basic_personality):
        """Memory and grudge settings work."""
        assert basic_personality.memory_duration == 24.0  # Default
        assert basic_personality.grudge_factor == 0.5  # Default

        personality = PersonalityTemplate(
            name="Grudge Holder",
            memory_duration=168.0,
            grudge_factor=0.9
        )
        assert personality.memory_duration == 168.0
        assert personality.grudge_factor == 0.9


class TestPredefinedTemplates:
    """Tests for predefined personality templates."""

    def test_templates_exist(self):
        """All predefined templates exist."""
        expected = [
            "timid_prey", "territorial_predator", "curious_neutral",
            "loyal_guardian", "greedy_collector", "friendly_helper",
            "paranoid_merchant", "sleepy_creature"
        ]
        for name in expected:
            assert name in PERSONALITY_TEMPLATES

    def test_get_template(self):
        """Can get template by name."""
        template = get_template("timid_prey")
        assert template is not None
        assert template.name == "Timid Prey"

        template = get_template("nonexistent")
        assert template is None

    def test_list_templates(self):
        """Can list all template names."""
        names = list_templates()
        assert "timid_prey" in names
        assert "territorial_predator" in names
        assert len(names) == 8

    def test_timid_prey_traits(self):
        """Timid prey has correct traits."""
        template = get_template("timid_prey")
        assert template.get_trait("fear") == 0.9
        assert template.get_trait("aggression") == 0.1
        assert template.idle_behavior == IdleBehavior.FORAGE
        assert template.threat_response == ThreatResponse.FLEE
        assert template.player_attitude == Attitude.AFRAID

    def test_territorial_predator_traits(self):
        """Territorial predator has correct traits."""
        template = get_template("territorial_predator")
        assert template.get_trait("aggression") == 0.8
        assert template.get_trait("fear") == 0.2
        assert template.idle_behavior == IdleBehavior.PATROL
        assert template.threat_response == ThreatResponse.CHALLENGE
        assert template.player_attitude == Attitude.HOSTILE

    def test_paranoid_merchant_traits(self):
        """Paranoid merchant has unique settings."""
        template = get_template("paranoid_merchant")
        assert template.get_trait("greed") == 0.9
        assert template.get_trait("fear") == 0.8
        assert template.threat_response == ThreatResponse.BRIBE
        assert template.memory_duration == 168.0  # One week
        assert template.grudge_factor == 0.9

    def test_friendly_helper_traits(self):
        """Friendly helper has correct traits."""
        template = get_template("friendly_helper")
        assert template.get_trait("social") == 0.9
        assert template.get_trait("aggression") == 0.1
        assert template.idle_behavior == IdleBehavior.SOCIALIZE
        assert template.player_attitude == Attitude.FRIENDLY
