"""
Tests for DynamicEntity system.
"""

import pytest
import time
from src.shadowengine.studio.entity import (
    DynamicEntity, EntityState, EntityStats, EntityMemory,
    ENTITY_TEMPLATES, create_entity_from_template
)
from src.shadowengine.studio.personality import ThreatResponse, Attitude
from src.shadowengine.studio.tags import ArtTags, ObjectType, InteractionType


class TestEntityState:
    """Tests for EntityState enum."""

    def test_states_exist(self):
        """All entity states exist."""
        expected = [
            "IDLE", "MOVING", "INTERACTING", "ATTACKING",
            "FLEEING", "HIDING", "SLEEPING", "DEAD", "CUSTOM"
        ]
        for name in expected:
            assert hasattr(EntityState, name)


class TestEntityStats:
    """Tests for EntityStats class."""

    def test_default_stats(self):
        """Default stats are initialized."""
        stats = EntityStats()
        assert stats.health == 100.0
        assert stats.max_health == 100.0
        assert stats.energy == 100.0
        assert stats.speed == 1.0

    def test_custom_stats(self):
        """Can set custom stats."""
        stats = EntityStats(
            health=50.0,
            max_health=50.0,
            speed=2.0,
            attack_power=20.0
        )
        assert stats.health == 50.0
        assert stats.speed == 2.0
        assert stats.attack_power == 20.0

    def test_is_alive(self):
        """Can check if alive."""
        stats = EntityStats(health=50.0)
        assert stats.is_alive() is True

        stats.health = 0
        assert stats.is_alive() is False

    def test_take_damage(self):
        """Damage is applied correctly."""
        stats = EntityStats(health=100.0, defense=10.0)
        damage = stats.take_damage(30.0)

        # Effective damage = 30 - (10 * 0.5) = 25
        assert damage == 25.0
        assert stats.health == 75.0

    def test_take_damage_minimum_zero(self):
        """Health doesn't go below zero."""
        stats = EntityStats(health=10.0, defense=0.0)
        stats.take_damage(100.0)
        assert stats.health == 0.0

    def test_heal(self):
        """Healing works correctly."""
        stats = EntityStats(health=50.0, max_health=100.0)
        healed = stats.heal(30.0)

        assert healed == 30.0
        assert stats.health == 80.0

    def test_heal_capped(self):
        """Healing is capped at max health."""
        stats = EntityStats(health=90.0, max_health=100.0)
        healed = stats.heal(50.0)

        assert healed == 10.0
        assert stats.health == 100.0

    def test_use_energy(self):
        """Energy can be used."""
        stats = EntityStats(energy=50.0)

        assert stats.use_energy(30.0) is True
        assert stats.energy == 20.0

        assert stats.use_energy(50.0) is False  # Not enough
        assert stats.energy == 20.0  # Unchanged

    def test_restore_energy(self):
        """Energy can be restored."""
        stats = EntityStats(energy=50.0, max_energy=100.0)
        restored = stats.restore_energy(30.0)

        assert restored == 30.0
        assert stats.energy == 80.0

    def test_serialization(self):
        """Stats can be serialized and deserialized."""
        stats = EntityStats(health=75.0, attack_power=15.0)
        data = stats.to_dict()
        restored = EntityStats.from_dict(data)

        assert restored.health == stats.health
        assert restored.attack_power == stats.attack_power


class TestEntityMemory:
    """Tests for EntityMemory class."""

    def test_create_memory(self):
        """Can create memory system."""
        memory = EntityMemory()
        assert len(memory.memories) == 0
        assert len(memory.grudges) == 0
        assert len(memory.friends) == 0

    def test_add_memory(self):
        """Can add memories."""
        memory = EntityMemory()
        memory.add_memory("attacked", {"source": "player1"}, time.time())

        assert len(memory.memories) == 1
        assert memory.memories[0]["type"] == "attacked"

    def test_memory_limit(self):
        """Memories are limited."""
        memory = EntityMemory(max_memories=5)
        for i in range(10):
            memory.add_memory("event", {"num": i}, time.time())

        assert len(memory.memories) == 5
        # Should keep latest memories
        assert memory.memories[0]["details"]["num"] == 5

    def test_add_grudge(self):
        """Can add grudges."""
        memory = EntityMemory()
        memory.add_grudge("player1", 0.3)
        assert memory.grudges["player1"] == 0.3

        memory.add_grudge("player1", 0.5)
        assert memory.grudges["player1"] == 0.8

    def test_grudge_capped(self):
        """Grudge is capped at 1.0."""
        memory = EntityMemory()
        memory.add_grudge("player1", 0.8)
        memory.add_grudge("player1", 0.5)
        assert memory.grudges["player1"] == 1.0

    def test_reduce_grudge(self):
        """Can reduce grudges."""
        memory = EntityMemory()
        memory.add_grudge("player1", 0.5)
        memory.reduce_grudge("player1", 0.3)
        assert memory.grudges["player1"] == 0.2

    def test_reduce_grudge_removes(self):
        """Grudge is removed when zero."""
        memory = EntityMemory()
        memory.add_grudge("player1", 0.3)
        memory.reduce_grudge("player1", 0.5)
        assert "player1" not in memory.grudges

    def test_add_friendship(self):
        """Can add friendship."""
        memory = EntityMemory()
        memory.add_friendship("player1", 0.4)
        assert memory.friends["player1"] == 0.4

    def test_get_attitude_toward(self):
        """Can get combined attitude."""
        memory = EntityMemory()
        memory.add_friendship("player1", 0.6)
        memory.add_grudge("player1", 0.2)

        attitude = memory.get_attitude_toward("player1")
        assert abs(attitude - 0.4) < 0.001  # 0.6 - 0.2, with floating point tolerance

    def test_has_memory_of(self):
        """Can check for recent memory."""
        memory = EntityMemory()
        now = time.time()
        memory.add_memory("attacked", {}, now - 10)

        assert memory.has_memory_of("attacked", now - 20) is True
        assert memory.has_memory_of("attacked", now - 5) is False
        assert memory.has_memory_of("healed", now - 20) is False

    def test_clear_old_memories(self):
        """Can clear old memories."""
        memory = EntityMemory()
        now = time.time()
        memory.add_memory("old", {}, now - 100)
        memory.add_memory("new", {}, now)

        cleared = memory.clear_old_memories(now - 50)
        assert cleared == 1
        assert len(memory.memories) == 1


class TestDynamicEntity:
    """Tests for DynamicEntity class."""

    def test_create_entity(self, basic_entity):
        """Can create dynamic entity."""
        assert basic_entity.name == "Test Entity"
        assert basic_entity.state == EntityState.IDLE
        assert basic_entity.personality is not None

    def test_entity_with_stats(self, creature_entity):
        """Entity can have custom stats."""
        assert creature_entity.stats.health == 50.0
        assert creature_entity.stats.speed == 1.5

    def test_entity_with_dialogue(self, npc_entity):
        """Entity can have dialogue."""
        dialogue = npc_entity.get_dialogue()
        assert dialogue in npc_entity.dialogue_pool

    def test_add_dialogue(self, basic_entity):
        """Can add dialogue to entity."""
        basic_entity.add_dialogue("Hello!")
        assert "Hello!" in basic_entity.dialogue_pool

        # Duplicate not added
        basic_entity.add_dialogue("Hello!")
        assert basic_entity.dialogue_pool.count("Hello!") == 1

    def test_set_state(self, basic_entity):
        """Can change entity state."""
        basic_entity.set_state(EntityState.MOVING)
        assert basic_entity.state == EntityState.MOVING

    def test_update(self, basic_entity):
        """Entity can update."""
        initial_energy = basic_entity.stats.energy
        basic_entity.stats.energy = 50.0

        basic_entity.update(1.0)
        # Energy should restore slightly
        assert basic_entity.stats.energy > 50.0

    def test_update_sleeping_restores_energy(self, basic_entity):
        """Sleeping restores energy faster."""
        basic_entity.stats.energy = 50.0
        basic_entity.set_state(EntityState.SLEEPING)

        basic_entity.update(1.0)
        # Sleeping restores 10x faster
        assert basic_entity.stats.energy >= 60.0

    def test_respond_to_threat_flee(self, creature_entity):
        """Timid entity flees from threat."""
        response = creature_entity.respond_to_threat(0.5)
        assert response in (ThreatResponse.FLEE, ThreatResponse.HIDE)
        assert creature_entity.state in (EntityState.FLEEING, EntityState.HIDING)

    def test_respond_to_threat_with_grudge(self, basic_entity):
        """Grudge increases effective threat."""
        basic_entity.memory.add_grudge("enemy1", 0.5)
        # Response should be more defensive with grudge
        basic_entity.respond_to_threat(0.3, "enemy1")

    def test_take_damage(self, basic_entity):
        """Entity can take damage."""
        initial_health = basic_entity.stats.health
        damage = basic_entity.take_damage(20.0, "attacker")

        assert basic_entity.stats.health < initial_health
        assert "attacker" in basic_entity.memory.grudges

    def test_take_damage_death(self, basic_entity):
        """Entity dies from enough damage."""
        basic_entity.stats.health = 10.0
        basic_entity.stats.defense = 0.0
        basic_entity.take_damage(100.0)

        assert basic_entity.state == EntityState.DEAD
        assert not basic_entity.stats.is_alive()

    def test_attack(self, basic_entity, creature_entity):
        """Entity can attack another."""
        initial_health = creature_entity.stats.health
        damage = basic_entity.attack(creature_entity)

        assert damage > 0
        assert creature_entity.stats.health < initial_health
        assert basic_entity.stats.energy < 100.0  # Used energy

    def test_attack_no_energy(self, basic_entity, creature_entity):
        """Attack fails without energy."""
        basic_entity.stats.energy = 0
        damage = basic_entity.attack(creature_entity)

        assert damage == 0
        assert creature_entity.stats.health == creature_entity.stats.max_health

    def test_interact_with_friendly(self, npc_entity):
        """Friendly interaction returns appropriate options."""
        result = npc_entity.interact_with("player1")

        assert "dialogue" in result
        assert "available_actions" in result

    def test_get_loot(self, creature_entity):
        """Can get loot from entity."""
        # Run multiple times to test probability
        all_loot = []
        for _ in range(100):
            loot = creature_entity.get_loot()
            all_loot.extend(loot)

        # Should have some fur and meat based on loot table
        assert "fur" in all_loot or "meat" in all_loot

    def test_can_spawn_in(self):
        """Entity checks spawn conditions."""
        from src.shadowengine.studio.entity import create_entity_from_template
        # Use forest_deer which has spawn_conditions set
        deer = create_entity_from_template("forest_deer")
        assert deer.can_spawn_in("forest") is True
        assert deer.can_spawn_in("desert") is False

    def test_add_animation(self, basic_entity, idle_animation):
        """Can add animation to entity."""
        basic_entity.add_animation(idle_animation)
        assert "idle" in basic_entity.animations

    def test_play_animation(self, basic_entity, idle_animation):
        """Can play animation."""
        basic_entity.add_animation(idle_animation)
        assert basic_entity.play_animation("idle") is True
        assert basic_entity._animation_player.current_animation == "idle"

    def test_serialization(self, creature_entity):
        """Entity can be serialized and deserialized."""
        data = creature_entity.to_dict()
        restored = DynamicEntity.from_dict(data)

        assert restored.id == creature_entity.id
        assert restored.name == creature_entity.name
        assert restored.stats.health == creature_entity.stats.health
        assert restored.personality.name == creature_entity.personality.name

    def test_copy(self, creature_entity):
        """Entity can be copied."""
        copy = creature_entity.copy()

        assert copy.id != creature_entity.id
        assert copy.name == "Forest Creature (copy)"
        assert copy.state == EntityState.IDLE  # Reset state
        assert len(copy.memory.memories) == 0  # Fresh memory


class TestEntityTemplates:
    """Tests for predefined entity templates."""

    def test_templates_exist(self):
        """Predefined templates exist."""
        expected = ["forest_deer", "cave_bat", "village_guard", "merchant"]
        for name in expected:
            assert name in ENTITY_TEMPLATES

    def test_create_from_template(self):
        """Can create entity from template."""
        deer = create_entity_from_template("forest_deer", "player1")

        assert deer is not None
        assert deer.name == "Forest Deer"
        assert deer.tags.object_type == ObjectType.CREATURE
        assert deer.player_id == "player1"

    def test_create_invalid_template(self):
        """Invalid template returns None."""
        result = create_entity_from_template("nonexistent")
        assert result is None

    def test_forest_deer(self):
        """Forest deer has correct properties."""
        deer = create_entity_from_template("forest_deer")

        assert deer.stats.health == 50.0
        assert deer.stats.speed == 1.5
        assert "forest" in deer.spawn_conditions.get("environments", [])

    def test_village_guard(self):
        """Village guard has correct properties."""
        guard = create_entity_from_template("village_guard")

        assert guard.tags.object_type == ObjectType.NPC
        assert guard.stats.attack_power == 15.0
        assert guard.stats.defense == 10.0
        assert len(guard.dialogue_pool) > 0

    def test_merchant_personality(self):
        """Merchant has paranoid personality."""
        merchant = create_entity_from_template("merchant")

        assert merchant.personality.player_attitude == Attitude.SUSPICIOUS
        assert merchant.personality.get_trait("greed") > 0.5
