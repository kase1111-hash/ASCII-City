"""
SocialNetwork - NPC relationships and emergent social dynamics.

Tracks relationships between NPCs, how they evolve over time,
and enables emergent social storylines based on shared memories
and rumors.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid



class RelationType(Enum):
    """Types of NPC-to-NPC relationships."""
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    RIVAL = "rival"
    ENEMY = "enemy"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    SUPERIOR = "superior"
    SUBORDINATE = "subordinate"
    ROMANTIC = "romantic"
    ALLY = "ally"
    INFORMANT = "informant"


@dataclass
class SocialRelation:
    """
    A relationship between two NPCs.

    Relationships are directional - A's feelings toward B may differ
    from B's feelings toward A.
    """

    relation_id: str = ""
    from_npc: str = ""              # The NPC who holds this relationship
    to_npc: str = ""                # The target of the relationship

    # Relationship type
    relation_type: RelationType = RelationType.STRANGER

    # Metrics (-100 to 100)
    affinity: int = 0               # Like/dislike
    trust: int = 0                  # Trust level
    respect: int = 0                # Respect level
    fear: int = 0                   # Fear of target

    # Dynamic state
    tension: int = 0                # Current conflict/tension (0-100)
    last_interaction: float = 0.0   # Timestamp of last interaction

    # Shared information
    shared_secrets: list[str] = field(default_factory=list)
    shared_memories: list[str] = field(default_factory=list)  # Memory IDs
    shared_rumors: list[str] = field(default_factory=list)    # Rumor IDs

    # History
    interaction_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.relation_id:
            self.relation_id = f"rel_{uuid.uuid4().hex[:12]}"
        # Only auto-derive type for new STRANGER relations; preserve
        # explicitly set types (ALLY, ROMANTIC, INFORMANT, etc.)
        if self.relation_type == RelationType.STRANGER:
            self._update_type()

    def _update_type(self) -> None:
        """Update relationship type based on metrics."""
        if self.relation_type in [RelationType.FAMILY, RelationType.SUPERIOR,
                                   RelationType.SUBORDINATE]:
            return  # These don't change based on metrics

        # Type based on affinity
        if self.affinity >= 80 and self.trust >= 60:
            self.relation_type = RelationType.CLOSE_FRIEND
        elif self.affinity >= 50:
            self.relation_type = RelationType.FRIEND
        elif self.affinity >= 20:
            self.relation_type = RelationType.ACQUAINTANCE
        elif self.affinity <= -60:
            self.relation_type = RelationType.ENEMY
        elif self.affinity <= -30:
            self.relation_type = RelationType.RIVAL
        else:
            self.relation_type = RelationType.ACQUAINTANCE

    def modify_affinity(self, amount: int) -> None:
        """Modify affinity toward target."""
        self.affinity = max(-100, min(100, self.affinity + amount))
        self._update_type()

    def modify_trust(self, amount: int) -> None:
        """Modify trust toward target."""
        self.trust = max(-100, min(100, self.trust + amount))
        self._update_type()

    def modify_respect(self, amount: int) -> None:
        """Modify respect toward target."""
        self.respect = max(-100, min(100, self.respect + amount))

    def modify_fear(self, amount: int) -> None:
        """Modify fear of target."""
        self.fear = max(0, min(100, self.fear + amount))

    def modify_tension(self, amount: int) -> None:
        """Modify current tension."""
        self.tension = max(0, min(100, self.tension + amount))

    def add_shared_secret(self, secret: str) -> None:
        """Add a shared secret."""
        if secret not in self.shared_secrets:
            self.shared_secrets.append(secret)
            self.modify_trust(5)  # Sharing secrets increases trust

    def add_shared_memory(self, memory_id: str) -> None:
        """Record a shared memory."""
        if memory_id not in self.shared_memories:
            self.shared_memories.append(memory_id)

    def add_shared_rumor(self, rumor_id: str) -> None:
        """Record a shared rumor."""
        if rumor_id not in self.shared_rumors:
            self.shared_rumors.append(rumor_id)

    def record_interaction(
        self,
        interaction_type: str,
        timestamp: float,
        outcome: str,
        details: dict = None
    ) -> None:
        """Record an interaction."""
        self.interaction_history.append({
            "type": interaction_type,
            "timestamp": timestamp,
            "outcome": outcome,
            "details": details or {}
        })
        self.last_interaction = timestamp

    def will_share_with(self) -> bool:
        """Check if will share information with target."""
        return self.trust > 0 and self.affinity > -20

    def will_protect(self) -> bool:
        """Check if will protect target."""
        return (self.affinity > 50 or
                self.relation_type in [RelationType.FAMILY, RelationType.CLOSE_FRIEND])

    def will_betray(self) -> bool:
        """Check if might betray target."""
        return self.affinity < -30 and self.tension > 50

    def to_dict(self) -> dict:
        """Serialize relationship."""
        return {
            "relation_id": self.relation_id,
            "from_npc": self.from_npc,
            "to_npc": self.to_npc,
            "relation_type": self.relation_type.value,
            "affinity": self.affinity,
            "trust": self.trust,
            "respect": self.respect,
            "fear": self.fear,
            "tension": self.tension,
            "last_interaction": self.last_interaction,
            "shared_secrets": self.shared_secrets,
            "shared_memories": self.shared_memories,
            "shared_rumors": self.shared_rumors,
            "interaction_history": self.interaction_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SocialRelation':
        """Deserialize relationship."""
        data = dict(data)  # Don't mutate the input dictionary
        data["relation_type"] = RelationType(data["relation_type"])
        return cls(**data)


@dataclass
class SocialEvent:
    """An event in the social network."""
    event_id: str = ""
    event_type: str = ""            # betrayal, alliance, conflict, reconciliation
    participants: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    description: str = ""
    consequences: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"soc_{uuid.uuid4().hex[:12]}"


class RelationshipDynamics:
    """
    Simulates how relationships change over time and through events.
    """

    # How different event types affect relationships
    EVENT_EFFECTS = {
        "helped": {"affinity": 15, "trust": 10},
        "saved": {"affinity": 30, "trust": 25, "respect": 20},
        "betrayed": {"affinity": -40, "trust": -50, "tension": 30},
        "lied_to": {"trust": -20, "tension": 10},
        "confided_in": {"trust": 15, "affinity": 10},
        "threatened": {"fear": 25, "affinity": -20, "tension": 20},
        "insulted": {"affinity": -15, "respect": -10, "tension": 15},
        "praised": {"affinity": 10, "respect": 5},
        "ignored": {"affinity": -5, "respect": -5},
        "competed": {"tension": 10},
        "cooperated": {"trust": 5, "affinity": 5},
        "shared_rumor": {"trust": 5, "affinity": 3},
        "witnessed_crime": {"fear": 10, "tension": 15},
        # Reverse effects for bidirectional interactions
        "was_helped": {"affinity": 15, "trust": 10},
        "was_saved": {"affinity": 30, "trust": 25, "respect": 20},
        "was_betrayed": {"affinity": -40, "trust": -50, "tension": 30},
        "was_lied_to": {"trust": -20, "tension": 10},
        "was_confided_in": {"trust": 15, "affinity": 10},
        "was_threatened": {"fear": 25, "affinity": -20, "tension": 20},
        "was_insulted": {"affinity": -15, "respect": -10, "tension": 15},
        "was_praised": {"affinity": 10, "respect": 5},
        "was_ignored": {"affinity": -5, "respect": -5},
    }

    def apply_event(
        self,
        relation: SocialRelation,
        event_type: str,
        magnitude: float = 1.0
    ) -> None:
        """Apply an event's effects to a relationship."""
        effects = self.EVENT_EFFECTS.get(event_type, {})

        for attr, amount in effects.items():
            scaled = int(amount * magnitude)
            if attr == "affinity":
                relation.modify_affinity(scaled)
            elif attr == "trust":
                relation.modify_trust(scaled)
            elif attr == "respect":
                relation.modify_respect(scaled)
            elif attr == "fear":
                relation.modify_fear(scaled)
            elif attr == "tension":
                relation.modify_tension(scaled)

    def decay_tension(self, relation: SocialRelation, dt: float) -> None:
        """Tension naturally decreases over time."""
        decay = int(dt * 0.1)  # Slow decay
        relation.tension = max(0, relation.tension - decay)

    def check_for_conflict(self, relation: SocialRelation) -> bool:
        """Check if relationship is at breaking point."""
        return relation.tension > 80 and relation.affinity < 0

    def check_for_reconciliation(self, relation: SocialRelation) -> bool:
        """Check if enemies might reconcile."""
        return (relation.relation_type == RelationType.ENEMY and
                relation.tension < 20 and
                relation.affinity > -70)


class SocialNetwork:
    """
    Manages the entire social network of NPCs.

    Tracks all relationships and enables querying for social dynamics
    and emergent storylines.
    """

    def __init__(self):
        # relation_id -> SocialRelation
        self.relations: dict[str, SocialRelation] = {}
        # (from_npc, to_npc) -> relation_id
        self.relation_index: dict[tuple[str, str], str] = {}
        # Social events history
        self.social_events: list[SocialEvent] = []
        # Dynamics engine
        self.dynamics = RelationshipDynamics()
        self.current_time: float = 0.0

    def get_or_create_relation(
        self,
        from_npc: str,
        to_npc: str,
        initial_type: RelationType = RelationType.STRANGER
    ) -> SocialRelation:
        """Get or create a relationship between two NPCs."""
        key = (from_npc, to_npc)

        if key in self.relation_index:
            return self.relations[self.relation_index[key]]

        # Create new relationship
        relation = SocialRelation(
            from_npc=from_npc,
            to_npc=to_npc,
            relation_type=initial_type
        )

        self.relations[relation.relation_id] = relation
        self.relation_index[key] = relation.relation_id

        return relation

    def get_relation(
        self,
        from_npc: str,
        to_npc: str
    ) -> Optional[SocialRelation]:
        """Get existing relationship or None."""
        key = (from_npc, to_npc)
        if key in self.relation_index:
            return self.relations[self.relation_index[key]]
        return None

    def get_all_relations_for(self, npc_id: str) -> list[SocialRelation]:
        """Get all relationships an NPC has (both directions)."""
        result = []
        for relation in self.relations.values():
            if relation.from_npc == npc_id or relation.to_npc == npc_id:
                result.append(relation)
        return result

    def get_outgoing_relations(self, npc_id: str) -> list[SocialRelation]:
        """Get relationships FROM this NPC."""
        return [
            r for r in self.relations.values()
            if r.from_npc == npc_id
        ]

    def get_incoming_relations(self, npc_id: str) -> list[SocialRelation]:
        """Get relationships TO this NPC."""
        return [
            r for r in self.relations.values()
            if r.to_npc == npc_id
        ]

    def get_friends(self, npc_id: str) -> list[str]:
        """Get NPCs who are friends with this one."""
        friends = []
        for relation in self.get_outgoing_relations(npc_id):
            if relation.relation_type in [RelationType.FRIEND,
                                          RelationType.CLOSE_FRIEND,
                                          RelationType.ALLY]:
                friends.append(relation.to_npc)
        return friends

    def get_enemies(self, npc_id: str) -> list[str]:
        """Get NPCs who are enemies of this one."""
        enemies = []
        for relation in self.get_outgoing_relations(npc_id):
            if relation.relation_type in [RelationType.ENEMY, RelationType.RIVAL]:
                enemies.append(relation.to_npc)
        return enemies

    def get_trusted_npcs(self, npc_id: str, threshold: int = 30) -> list[str]:
        """Get NPCs this one trusts above threshold."""
        trusted = []
        for relation in self.get_outgoing_relations(npc_id):
            if relation.trust >= threshold:
                trusted.append(relation.to_npc)
        return trusted

    def record_interaction(
        self,
        from_npc: str,
        to_npc: str,
        interaction_type: str,
        timestamp: float,
        outcome: str = "neutral",
        bidirectional: bool = True
    ) -> None:
        """Record an interaction between NPCs."""
        # Update A -> B relationship
        relation_ab = self.get_or_create_relation(from_npc, to_npc)
        relation_ab.record_interaction(interaction_type, timestamp, outcome)
        self.dynamics.apply_event(relation_ab, interaction_type)

        # Update B -> A relationship if bidirectional
        if bidirectional:
            relation_ba = self.get_or_create_relation(to_npc, from_npc)
            relation_ba.record_interaction(
                f"received_{interaction_type}",
                timestamp,
                outcome
            )
            # Receiving end has different effects
            reverse_type = f"was_{interaction_type}"
            if reverse_type in self.dynamics.EVENT_EFFECTS:
                self.dynamics.apply_event(relation_ba, reverse_type)

    def share_rumor_between(
        self,
        from_npc: str,
        to_npc: str,
        rumor_id: str,
        timestamp: float
    ) -> None:
        """Record rumor sharing between NPCs."""
        relation = self.get_or_create_relation(from_npc, to_npc)
        relation.add_shared_rumor(rumor_id)
        relation.record_interaction("shared_rumor", timestamp, "completed")
        self.dynamics.apply_event(relation, "shared_rumor")

    def share_memory_between(
        self,
        from_npc: str,
        to_npc: str,
        memory_id: str,
        timestamp: float
    ) -> None:
        """Record memory sharing between NPCs."""
        relation = self.get_or_create_relation(from_npc, to_npc)
        relation.add_shared_memory(memory_id)

    def update(self, dt: float) -> list[SocialEvent]:
        """
        Update social network over time.

        Returns any emergent social events.
        """
        self.current_time += dt
        events = []

        for relation in self.relations.values():
            # Decay tension
            self.dynamics.decay_tension(relation, dt)

            # Check for emergent events
            if self.dynamics.check_for_conflict(relation):
                event = self._create_conflict_event(relation)
                events.append(event)

            if self.dynamics.check_for_reconciliation(relation):
                event = self._create_reconciliation_event(relation)
                events.append(event)

        self.social_events.extend(events)
        return events

    def _create_conflict_event(
        self,
        relation: SocialRelation
    ) -> SocialEvent:
        """Create a conflict event between NPCs."""
        event = SocialEvent(
            event_type="conflict",
            participants=[relation.from_npc, relation.to_npc],
            timestamp=self.current_time,
            description=f"Tension reached breaking point between "
                       f"{relation.from_npc} and {relation.to_npc}",
            consequences=["increased_hostility", "potential_violence"]
        )

        # Conflict affects the relationship
        relation.modify_affinity(-10)
        relation.tension = 50  # Reset but high

        return event

    def _create_reconciliation_event(
        self,
        relation: SocialRelation
    ) -> SocialEvent:
        """Create a reconciliation event."""
        event = SocialEvent(
            event_type="reconciliation",
            participants=[relation.from_npc, relation.to_npc],
            timestamp=self.current_time,
            description=f"Former enemies {relation.from_npc} and "
                       f"{relation.to_npc} may be reconciling",
            consequences=["reduced_hostility"]
        )

        # Reconciliation improves relationship
        relation.modify_affinity(20)
        relation.relation_type = RelationType.RIVAL  # No longer enemies

        return event

    def get_emergent_storylines(self) -> list[dict]:
        """
        Identify emergent storylines from social dynamics.

        Returns narratively interesting situations.
        """
        storylines = []

        # Find love triangles / rivalries
        for npc_id in self._get_all_npcs():
            friends = self.get_friends(npc_id)
            enemies = self.get_enemies(npc_id)

            # Friend of my enemy
            for friend in friends:
                friend_friends = self.get_friends(friend)
                for enemy in enemies:
                    if enemy in friend_friends:
                        storylines.append({
                            "type": "friend_of_enemy",
                            "npcs": [npc_id, friend, enemy],
                            "description": f"{friend} is caught between "
                                         f"{npc_id} and {enemy}"
                        })

        # Find high-tension relationships
        for relation in self.relations.values():
            if relation.tension > 70:
                storylines.append({
                    "type": "high_tension",
                    "npcs": [relation.from_npc, relation.to_npc],
                    "tension": relation.tension,
                    "description": f"Explosive tension between "
                                 f"{relation.from_npc} and {relation.to_npc}"
                })

        # Find secret alliances (enemies who trust each other)
        for relation in self.relations.values():
            if relation.affinity < -20 and relation.trust > 30:
                storylines.append({
                    "type": "secret_alliance",
                    "npcs": [relation.from_npc, relation.to_npc],
                    "description": f"{relation.from_npc} trusts enemy "
                                 f"{relation.to_npc} despite animosity"
                })

        return storylines

    def _get_all_npcs(self) -> set[str]:
        """Get all NPCs in the network."""
        npcs = set()
        for relation in self.relations.values():
            npcs.add(relation.from_npc)
            npcs.add(relation.to_npc)
        return npcs

    def to_dict(self) -> dict:
        """Serialize social network."""
        return {
            "relations": {k: v.to_dict() for k, v in self.relations.items()},
            "relation_index": {
                f"{k[0]}|{k[1]}": v
                for k, v in self.relation_index.items()
            },
            "social_events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "participants": e.participants,
                    "timestamp": e.timestamp,
                    "description": e.description,
                    "consequences": e.consequences
                }
                for e in self.social_events
            ],
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SocialNetwork':
        """Deserialize social network."""
        network = cls()
        network.relations = {
            k: SocialRelation.from_dict(v)
            for k, v in data.get("relations", {}).items()
        }
        network.relation_index = {
            tuple(k.split("|")): v
            for k, v in data.get("relation_index", {}).items()
        }
        network.social_events = [
            SocialEvent(**e) for e in data.get("social_events", [])
        ]
        network.current_time = data.get("current_time", 0.0)
        return network
