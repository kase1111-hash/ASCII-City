"""
Tests for Dialogue System - topic-based conversations.

These tests verify that dialogue correctly:
- Manages topics and responses
- Handles different response types
- Tracks topic availability
"""

import pytest
from shadowengine.character import DialogueManager, DialogueTopic, DialogueResponse
from shadowengine.character.dialogue import ResponseType


class TestDialogueTopic:
    """Dialogue topic functionality."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_topic(self):
        """Can create a dialogue topic."""
        topic = DialogueTopic(
            id="test_topic",
            name="Test Topic",
            description="A test topic",
            honest_response="This is the truth",
            lie_response="This is a lie"
        )

        assert topic.id == "test_topic"
        assert topic.honest_response == "This is the truth"

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_honest_response(self):
        """Character gives honest response when not lying."""
        topic = DialogueTopic(
            id="alibi",
            name="Alibi",
            description="Ask about their alibi",
            honest_response="I was at home all night",
            lie_response="I was at the bar"
        )

        response = topic.get_response(
            is_cracked=False,
            will_lie=False,
            will_refuse=False
        )

        assert response.response_type == ResponseType.HONEST
        assert response.text == "I was at home all night"

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_lie_response(self):
        """Character lies when appropriate."""
        topic = DialogueTopic(
            id="alibi",
            name="Alibi",
            description="Ask about their alibi",
            honest_response="I was at home all night",
            lie_response="I was at the bar"
        )

        response = topic.get_response(
            is_cracked=False,
            will_lie=True,
            will_refuse=False
        )

        assert response.response_type == ResponseType.LIE
        assert response.text == "I was at the bar"

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_cracked_response(self):
        """Cracked character reveals truth."""
        topic = DialogueTopic(
            id="secret",
            name="The Secret",
            description="Ask about the secret",
            honest_response="I don't know anything",
            cracked_response="Fine! I'll tell you everything!",
            reveals_on_cracked="secret_revealed"
        )

        response = topic.get_response(
            is_cracked=True,
            will_lie=True,  # Would lie, but is cracked
            will_refuse=False
        )

        assert response.response_type == ResponseType.REVEAL
        assert "tell you everything" in response.text
        assert response.reveals_fact == "secret_revealed"

    @pytest.mark.unit
    @pytest.mark.character
    def test_refuse_response(self):
        """Character can refuse to discuss topic."""
        topic = DialogueTopic(
            id="sensitive",
            name="Sensitive Topic",
            description="A sensitive subject",
            honest_response="This is what happened",
            refuse_response="I won't discuss that"
        )

        response = topic.get_response(
            is_cracked=False,
            will_lie=False,
            will_refuse=True
        )

        assert response.response_type == ResponseType.REFUSE
        assert response.text == "I won't discuss that"

    @pytest.mark.unit
    @pytest.mark.character
    def test_topic_with_requirements(self):
        """Topics can have requirements."""
        topic = DialogueTopic(
            id="advanced_topic",
            name="Advanced Topic",
            description="Requires prior discovery",
            requires_discovery="basic_clue",
            requires_trust=10,
            honest_response="Now I can tell you more"
        )

        assert topic.requires_discovery == "basic_clue"
        assert topic.requires_trust == 10

    @pytest.mark.unit
    @pytest.mark.character
    def test_accusation_topic(self):
        """Accusation topics apply pressure."""
        topic = DialogueTopic(
            id="accuse",
            name="Accusation",
            description="Accuse them",
            is_accusation=True,
            pressure_amount=30,
            honest_response="How dare you!",
            cracked_response="Alright, I did it!"
        )

        assert topic.is_accusation is True
        assert topic.pressure_amount == 30


class TestDialogueManager:
    """Dialogue manager functionality."""

    @pytest.fixture
    def manager(self):
        """Fresh dialogue manager."""
        return DialogueManager()

    @pytest.fixture
    def sample_topics(self):
        """Sample dialogue topics."""
        return [
            DialogueTopic(
                id="greeting",
                name="Greeting",
                description="Greet them",
                honest_response="Hello there"
            ),
            DialogueTopic(
                id="weather",
                name="The Weather",
                description="Discuss weather",
                honest_response="Nice day, isn't it?"
            ),
            DialogueTopic(
                id="secret",
                name="The Secret",
                description="Ask about the secret",
                requires_discovery="knows_secret_exists",
                honest_response="What secret?",
                cracked_response="The secret is..."
            )
        ]

    @pytest.mark.unit
    @pytest.mark.character
    def test_register_topic(self, manager, sample_topics):
        """Can register topics."""
        for topic in sample_topics:
            manager.register_topic(topic)

        assert len(manager.topics) == 3

    @pytest.mark.unit
    @pytest.mark.character
    def test_assign_topic_to_character(self, manager, sample_topics):
        """Can assign topics to characters."""
        for topic in sample_topics:
            manager.register_topic(topic)

        manager.assign_topic_to_character("alice", "greeting")
        manager.assign_topic_to_character("alice", "weather")

        alice_topics = manager.get_character_topics("alice")
        assert len(alice_topics) == 2

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_available_topics_basic(self, manager, sample_topics):
        """Get available topics filters correctly."""
        for topic in sample_topics:
            manager.register_topic(topic)

        manager.assign_topic_to_character("bob", "greeting")
        manager.assign_topic_to_character("bob", "weather")
        manager.assign_topic_to_character("bob", "secret")

        available = manager.get_available_topics(
            character_id="bob",
            player_discoveries=set(),  # No discoveries
            player_trust=0,
            exhausted=set()
        )

        # Secret requires discovery, so only 2 available
        assert len(available) == 2

    @pytest.mark.unit
    @pytest.mark.character
    def test_available_topics_with_discovery(self, manager, sample_topics):
        """Discovery unlocks topics."""
        for topic in sample_topics:
            manager.register_topic(topic)

        manager.assign_topic_to_character("bob", "secret")

        # Without discovery
        available = manager.get_available_topics(
            character_id="bob",
            player_discoveries=set(),
            player_trust=0,
            exhausted=set()
        )
        assert len(available) == 0

        # With discovery
        available = manager.get_available_topics(
            character_id="bob",
            player_discoveries={"knows_secret_exists"},
            player_trust=0,
            exhausted=set()
        )
        assert len(available) == 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_exhausted_topics_excluded(self, manager, sample_topics):
        """Exhausted topics are excluded."""
        for topic in sample_topics:
            manager.register_topic(topic)

        manager.assign_topic_to_character("bob", "greeting")
        manager.assign_topic_to_character("bob", "weather")

        available = manager.get_available_topics(
            character_id="bob",
            player_discoveries=set(),
            player_trust=0,
            exhausted={"greeting"}
        )

        assert len(available) == 1
        assert available[0].id == "weather"

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_greeting_topic(self, manager):
        """Can create standard greeting topic."""
        topic = manager.create_greeting_topic(
            character_name="Alice",
            greeting="Hello, how can I help you?"
        )

        assert topic.id == "greet_alice"
        assert "Hello" in topic.honest_response

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_accusation_topic(self, manager):
        """Can create accusation topic."""
        topic = manager.create_accusation_topic(
            character_name="Bob",
            crime="theft",
            denial="I didn't steal anything!",
            confession="Alright, I took it!"
        )

        assert topic.id == "accuse_bob"
        assert topic.is_accusation is True
        assert topic.pressure_amount > 0
        assert "confession" in topic.reveals_on_cracked


class TestDialogueResponse:
    """Dialogue response functionality."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_response_with_revelation(self):
        """Responses can reveal facts."""
        response = DialogueResponse(
            text="I saw him do it!",
            response_type=ResponseType.REVEAL,
            reveals_fact="witnessed_crime",
            is_evidence=True
        )

        assert response.reveals_fact == "witnessed_crime"
        assert response.is_evidence is True

    @pytest.mark.unit
    @pytest.mark.character
    def test_response_with_trust_change(self):
        """Responses can affect trust."""
        response = DialogueResponse(
            text="Thank you for understanding",
            response_type=ResponseType.HONEST,
            trust_change=5
        )

        assert response.trust_change == 5

    @pytest.mark.unit
    @pytest.mark.character
    def test_response_unlocks_topics(self):
        """Responses can unlock new topics."""
        response = DialogueResponse(
            text="Now that you know that, I can tell you more...",
            response_type=ResponseType.HONEST,
            unlocks_topics=["deeper_secret", "related_info"]
        )

        assert "deeper_secret" in response.unlocks_topics
        assert len(response.unlocks_topics) == 2
