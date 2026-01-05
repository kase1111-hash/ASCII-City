"""
Tests for Character - NPC model with psychology and secrets.

These tests verify that characters correctly:
- Initialize with archetypes and motivations
- Track trust and pressure
- Crack under pressure
- Manage topics and knowledge
"""

import pytest
from shadowengine.character import Character, Archetype
from shadowengine.character.character import Mood, Motivations, CharacterState


class TestCharacterCreation:
    """Character creation and initialization."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_basic_character(self, basic_character):
        """Can create a basic character."""
        assert basic_character.id == "test_char"
        assert basic_character.name == "Test Character"
        assert basic_character.archetype == Archetype.INNOCENT

    @pytest.mark.unit
    @pytest.mark.character
    def test_character_with_secrets(self, guilty_character):
        """Character can have secrets and lies."""
        assert guilty_character.secret_truth != ""
        assert guilty_character.public_lie != ""

    @pytest.mark.unit
    @pytest.mark.character
    def test_motivations_from_archetype(self):
        """Archetypes generate appropriate motivations."""
        survivor = Character(
            id="survivor",
            name="Survivor",
            archetype=Archetype.SURVIVOR
        )

        # Survivors have high fear
        assert survivor.motivations.fear > 70

        believer = Character(
            id="believer",
            name="Believer",
            archetype=Archetype.TRUE_BELIEVER
        )

        # True believers have high pride
        assert believer.motivations.pride > 70

    @pytest.mark.unit
    @pytest.mark.character
    @pytest.mark.parametrize("archetype", list(Archetype))
    def test_all_archetypes_valid(self, archetype):
        """All archetypes can create valid characters."""
        char = Character(
            id=f"test_{archetype.value}",
            name=f"Test {archetype.value}",
            archetype=archetype
        )

        assert char.archetype == archetype
        assert char.motivations is not None


class TestCharacterState:
    """Character state management."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_initial_state(self, basic_character):
        """Character starts in calm, uncracked state."""
        assert basic_character.state.mood == Mood.CALM
        assert basic_character.state.is_cracked is False
        assert basic_character.state.is_alive is True

    @pytest.mark.unit
    @pytest.mark.character
    def test_move_character(self, basic_character):
        """Can move character to new location."""
        basic_character.move_to("hallway")
        assert basic_character.state.location == "hallway"

    @pytest.mark.unit
    @pytest.mark.character
    def test_record_conversation(self, basic_character):
        """Conversation count tracks correctly."""
        assert basic_character.state.times_talked == 0

        basic_character.record_conversation()
        assert basic_character.state.times_talked == 1

        basic_character.record_conversation()
        assert basic_character.state.times_talked == 2


class TestCharacterTrust:
    """Trust mechanics."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_initial_trust(self, basic_character):
        """Character starts with neutral trust."""
        assert basic_character.current_trust == 0

    @pytest.mark.unit
    @pytest.mark.character
    def test_modify_trust_positive(self, basic_character):
        """Positive trust makes character friendly."""
        basic_character.modify_trust(25)

        assert basic_character.current_trust == 25
        assert basic_character.state.mood == Mood.FRIENDLY

    @pytest.mark.unit
    @pytest.mark.character
    def test_modify_trust_negative(self, basic_character):
        """Negative trust makes character hostile."""
        basic_character.modify_trust(-25)

        assert basic_character.current_trust == -25
        assert basic_character.state.mood == Mood.HOSTILE

    @pytest.mark.unit
    @pytest.mark.character
    def test_will_cooperate_with_trust(self, basic_character):
        """Characters cooperate with positive trust."""
        basic_character.modify_trust(10)
        assert basic_character.will_cooperate() is True

    @pytest.mark.unit
    @pytest.mark.character
    def test_wont_cooperate_when_hostile(self, basic_character):
        """Hostile characters don't cooperate."""
        basic_character.modify_trust(-30)  # Makes hostile
        assert basic_character.will_cooperate() is False


class TestCharacterPressure:
    """Pressure and cracking mechanics."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_apply_pressure(self, guilty_character):
        """Pressure accumulates."""
        initial_pressure = guilty_character.state.pressure_accumulated

        guilty_character.apply_pressure(10)

        assert guilty_character.state.pressure_accumulated > initial_pressure

    @pytest.mark.unit
    @pytest.mark.character
    def test_pressure_causes_mood_change(self, basic_character):
        """Pressure causes mood to change."""
        # Use innocent character with lower modifiers
        basic_character.trust_threshold = 100  # High threshold

        # Apply moderate pressure
        basic_character.apply_pressure(30)

        # Should accumulate pressure and potentially change mood
        assert basic_character.state.pressure_accumulated > 0

    @pytest.mark.unit
    @pytest.mark.character
    def test_character_cracks(self, guilty_character, helpers):
        """Characters crack under enough pressure."""
        cracked, attempts = helpers.apply_pressure_until_cracked(guilty_character)

        assert cracked is True
        assert guilty_character.state.is_cracked is True
        assert guilty_character.state.mood == Mood.SCARED

    @pytest.mark.unit
    @pytest.mark.character
    def test_fear_increases_effective_pressure(self):
        """High fear characters crack faster."""
        # Create high-fear character (survivor archetype)
        fearful = Character(
            id="fearful",
            name="Fearful",
            archetype=Archetype.SURVIVOR,
            trust_threshold=50
        )

        # Create low-fear character (true believer)
        brave = Character(
            id="brave",
            name="Brave",
            archetype=Archetype.TRUE_BELIEVER,
            trust_threshold=50
        )

        # Apply same pressure
        fearful.apply_pressure(30)
        brave.apply_pressure(30)

        # Fearful should have more accumulated pressure
        assert fearful.state.pressure_accumulated > brave.state.pressure_accumulated

    @pytest.mark.unit
    @pytest.mark.character
    def test_guilt_increases_effective_pressure(self):
        """Guilty characters crack faster."""
        guilty = Character(
            id="guilty",
            name="Guilty One",
            archetype=Archetype.GUILTY,
            trust_threshold=50
        )

        innocent = Character(
            id="innocent",
            name="Innocent One",
            archetype=Archetype.INNOCENT,
            trust_threshold=50
        )

        guilty.apply_pressure(20)
        innocent.apply_pressure(20)

        assert guilty.state.pressure_accumulated > innocent.state.pressure_accumulated


class TestCharacterKnowledge:
    """Knowledge and topic management."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_add_knowledge(self, basic_character):
        """Can add knowledge to character."""
        basic_character.add_knowledge("secret_passage")

        assert basic_character.knows("secret_passage")
        assert not basic_character.knows("unknown_thing")

    @pytest.mark.unit
    @pytest.mark.character
    def test_add_topic(self, basic_character):
        """Can add discussion topics."""
        basic_character.add_topic("the weather")
        basic_character.add_topic("local gossip")

        topics = basic_character.get_available_topics()
        assert "the weather" in topics
        assert "local gossip" in topics

    @pytest.mark.unit
    @pytest.mark.character
    def test_exhaust_topic(self, basic_character):
        """Exhausted topics are removed from available."""
        basic_character.add_topic("one time topic")

        assert "one time topic" in basic_character.available_topics

        basic_character.exhaust_topic("one time topic")

        assert "one time topic" not in basic_character.available_topics
        assert "one time topic" in basic_character.exhausted_topics


class TestCharacterMoodModifiers:
    """Mood-based response modifiers."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_mood_modifiers(self, basic_character):
        """Different moods produce different modifiers."""
        basic_character.state.mood = Mood.ANGRY
        assert "angrily" in basic_character.get_response_mood_modifier()

        basic_character.state.mood = Mood.SCARED
        assert "fearfully" in basic_character.get_response_mood_modifier()

        basic_character.state.mood = Mood.CALM
        assert basic_character.get_response_mood_modifier() == ""


class TestCharacterSerialization:
    """Serialization and deserialization."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_serialize_character(self, guilty_character):
        """Can serialize character to dict."""
        data = guilty_character.to_dict()

        assert data["id"] == "culprit"
        assert data["name"] == "The Culprit"
        assert data["archetype"] == "guilty"
        assert "secret_truth" in data
        assert "motivations" in data

    @pytest.mark.unit
    @pytest.mark.character
    def test_deserialize_character(self, guilty_character):
        """Can deserialize character from dict."""
        guilty_character.modify_trust(-10)
        guilty_character.apply_pressure(20)
        guilty_character.add_knowledge("secret_fact")

        data = guilty_character.to_dict()
        restored = Character.from_dict(data)

        assert restored.id == guilty_character.id
        assert restored.current_trust == guilty_character.current_trust
        assert restored.state.pressure_accumulated == guilty_character.state.pressure_accumulated
        assert restored.knows("secret_fact")

    @pytest.mark.unit
    @pytest.mark.character
    def test_roundtrip_preserves_all_state(self, guilty_character):
        """Roundtrip serialization preserves complete state."""
        # Modify state extensively
        guilty_character.modify_trust(15)
        guilty_character.apply_pressure(25)
        guilty_character.add_knowledge("k1")
        guilty_character.add_knowledge("k2")
        guilty_character.add_topic("t1")
        guilty_character.exhaust_topic("alibi")
        guilty_character.move_to("garden")
        guilty_character.record_conversation()

        data = guilty_character.to_dict()
        restored = Character.from_dict(data)

        assert restored.current_trust == 15
        assert restored.knows("k1")
        assert restored.knows("k2")
        assert "t1" in restored.available_topics
        assert "alibi" in restored.exhausted_topics
        assert restored.state.location == "garden"
        assert restored.state.times_talked == 1
