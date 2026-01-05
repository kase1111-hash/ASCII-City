"""Tests for specialized circuit types (Mechanical, Biological, Environmental)."""

import pytest

from src.shadowengine.circuits.types import (
    MechanicalCircuit,
    MechanicalProperties,
    BiologicalCircuit,
    BiologicalProperties,
    EnvironmentalCircuit,
    EnvironmentalProperties,
)
from src.shadowengine.circuits.circuit import CircuitType
from src.shadowengine.circuits.signals import (
    SignalType,
    InputSignal,
    OutputSignal,
)


class TestMechanicalProperties:
    """Test MechanicalProperties dataclass."""

    def test_default_properties(self):
        """Test default mechanical properties."""
        props = MechanicalProperties()
        assert props.material == "metal"
        assert props.lubrication == 1.0
        assert props.wear == 0.0
        assert props.powered is False
        assert props.jammed is False

    def test_custom_properties(self):
        """Test custom mechanical properties."""
        props = MechanicalProperties(
            material="wood",
            lubrication=0.5,
            wear=0.3,
            powered=True
        )
        assert props.material == "wood"
        assert props.lubrication == 0.5
        assert props.wear == 0.3
        assert props.powered is True

    def test_apply_wear(self):
        """Test applying wear."""
        props = MechanicalProperties(wear=0.5)
        props.apply_wear(0.2)
        assert props.wear == 0.7

    def test_lubricate(self):
        """Test lubrication."""
        props = MechanicalProperties(lubrication=0.5)
        props.lubricate(0.3)
        assert props.lubrication == 0.8

    def test_serialization(self):
        """Test mechanical properties serialization."""
        props = MechanicalProperties(material="brass", jammed=True)
        data = props.to_dict()
        assert data["material"] == "brass"
        assert data["jammed"] is True

    def test_deserialization(self):
        """Test mechanical properties deserialization."""
        data = {"material": "glass", "wear": 0.7}
        props = MechanicalProperties.from_dict(data)
        assert props.material == "glass"
        assert props.wear == 0.7


class TestMechanicalCircuit:
    """Test MechanicalCircuit class."""

    def test_creation(self):
        """Test creating a mechanical circuit."""
        circuit = MechanicalCircuit(
            id="lever_1",
            name="Rusty Lever"
        )
        assert circuit.circuit_type == CircuitType.MECHANICAL
        assert isinstance(circuit.mechanical, MechanicalProperties)

    def test_with_material(self):
        """Test mechanical circuit with custom material."""
        circuit = MechanicalCircuit(
            id="gear_1",
            name="Brass Gear",
            material="brass"
        )
        assert circuit.mechanical.material == "brass"

    def test_press_signal(self):
        """Test pressing the mechanism."""
        circuit = MechanicalCircuit(
            id="button",
            name="Button"
        )
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        # Should produce activation or sound
        assert len(outputs) >= 1

    def test_jammed_mechanism(self):
        """Test jammed mechanism produces stuck sound."""
        circuit = MechanicalCircuit(
            id="stuck_door",
            name="Stuck Door"
        )
        circuit.mechanical.jammed = True
        signal = InputSignal(
            type=SignalType.PUSH,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        # Jammed mechanism produces sound but no real action
        assert any(o.type == SignalType.SOUND for o in outputs)

    def test_strong_force_unjams(self):
        """Test strong force can unjam mechanism."""
        circuit = MechanicalCircuit(
            id="stuck_gear",
            name="Stuck Gear"
        )
        circuit.mechanical.jammed = True
        signal = InputSignal(
            type=SignalType.KICK,
            strength=0.95,  # Very strong
            source_id="player"
        )
        circuit.receive_signal(signal)
        # Strong kick may unjam
        assert circuit.mechanical.jammed is False

    def test_kick_causes_wear(self):
        """Test kicking causes wear."""
        circuit = MechanicalCircuit(
            id="door",
            name="Metal Door"
        )
        initial_wear = circuit.mechanical.wear
        signal = InputSignal(
            type=SignalType.KICK,
            strength=0.8,
            source_id="player"
        )
        circuit.receive_signal(signal)
        assert circuit.mechanical.wear > initial_wear

    def test_serialization(self):
        """Test mechanical circuit serialization."""
        circuit = MechanicalCircuit(
            id="test",
            name="Test",
            material="copper",
            powered=True
        )
        data = circuit.to_dict()
        assert data["mechanical"]["material"] == "copper"
        assert data["mechanical"]["powered"] is True


class TestBiologicalProperties:
    """Test BiologicalProperties dataclass."""

    def test_default_properties(self):
        """Test default biological properties."""
        props = BiologicalProperties()
        assert props.species == "unknown"
        assert props.fear == 0.5
        assert props.hunger == 0.5
        assert props.curiosity == 0.5
        assert props.aggression == 0.3
        assert props.loyalty == 0.0
        assert props.alert is False

    def test_predator_properties(self):
        """Test predator biological properties."""
        props = BiologicalProperties(
            species="wolf",
            fear=0.2,
            aggression=0.8,
            hunger=0.7
        )
        assert props.species == "wolf"
        assert props.aggression == 0.8

    def test_prey_properties(self):
        """Test prey biological properties."""
        props = BiologicalProperties(
            species="rabbit",
            fear=0.9,
            aggression=0.1,
            curiosity=0.3
        )
        assert props.fear == 0.9

    def test_get_dominant_drive(self):
        """Test getting dominant drive."""
        props = BiologicalProperties(fear=0.9, hunger=0.3)
        assert props.get_dominant_drive() == "fear"

    def test_serialization(self):
        """Test biological properties serialization."""
        props = BiologicalProperties(species="rat", alert=True)
        data = props.to_dict()
        assert data["species"] == "rat"
        assert data["alert"] is True


class TestBiologicalCircuit:
    """Test BiologicalCircuit class."""

    def test_creation(self):
        """Test creating a biological circuit."""
        circuit = BiologicalCircuit(
            id="rat_1",
            name="Sewer Rat"
        )
        assert circuit.circuit_type == CircuitType.BIOLOGICAL
        assert isinstance(circuit.biological, BiologicalProperties)

    def test_fear_response_to_proximity(self):
        """Test high fear causes flee response to proximity."""
        circuit = BiologicalCircuit(
            id="mouse",
            name="Mouse",
            species="mouse"
        )
        circuit.biological.fear = 0.9
        signal = InputSignal(
            type=SignalType.PROXIMITY,
            strength=0.6,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        # High fear + proximity should trigger flee
        assert any(o.type == SignalType.FLEE for o in outputs)

    def test_aggression_response_to_damage(self):
        """Test high aggression causes attack response."""
        circuit = BiologicalCircuit(
            id="guard_dog",
            name="Guard Dog",
            species="dog"
        )
        circuit.biological.aggression = 0.8
        circuit.biological.fear = 0.2
        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.3,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        # Aggressive creature attacks when damaged
        assert any(o.type == SignalType.ATTACK for o in outputs)

    def test_sound_triggers_alert(self):
        """Test loud sound triggers alert."""
        circuit = BiologicalCircuit(
            id="guard",
            name="Guard",
            species="human"
        )
        circuit.biological.alert = False
        signal = InputSignal(
            type=SignalType.SOUND,
            strength=0.7,
            source_id="unknown"
        )
        circuit.receive_signal(signal)
        # Loud sound should trigger alert
        assert circuit.biological.alert is True

    def test_say_response(self):
        """Test response to speech."""
        circuit = BiologicalCircuit(
            id="npc",
            name="Friendly NPC",
            species="human"
        )
        circuit.biological.loyalty = 0.7
        signal = InputSignal(
            type=SignalType.SAY,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        # Loyal creature responds to speech
        assert any(o.type == SignalType.SPEAK for o in outputs)


class TestEnvironmentalProperties:
    """Test EnvironmentalProperties dataclass."""

    def test_default_properties(self):
        """Test default environmental properties."""
        props = EnvironmentalProperties()
        assert props.terrain_type == "rock"
        assert props.fluid is False
        assert props.stability == 1.0
        assert props.temperature == 20.0
        assert props.moisture == 0.0

    def test_water_properties(self):
        """Test water environmental properties."""
        props = EnvironmentalProperties(
            terrain_type="water",
            fluid=True,
            stability=0.5,
            moisture=1.0
        )
        assert props.fluid is True
        assert props.moisture == 1.0

    def test_lava_properties(self):
        """Test lava environmental properties."""
        props = EnvironmentalProperties(
            terrain_type="lava",
            fluid=True,
            temperature=1200.0,
            stability=0.3
        )
        assert props.temperature == 1200.0

    def test_serialization(self):
        """Test environmental properties serialization."""
        props = EnvironmentalProperties(terrain_type="ice", temperature=-10.0)
        data = props.to_dict()
        assert data["terrain_type"] == "ice"
        assert data["temperature"] == -10.0


class TestEnvironmentalCircuit:
    """Test EnvironmentalCircuit class."""

    def test_creation(self):
        """Test creating an environmental circuit."""
        circuit = EnvironmentalCircuit(
            id="waterfall_1",
            name="Small Waterfall"
        )
        assert circuit.circuit_type == CircuitType.ENVIRONMENTAL
        assert isinstance(circuit.environmental, EnvironmentalProperties)

    def test_damage_reduces_stability(self):
        """Test damage reduces stability."""
        circuit = EnvironmentalCircuit(
            id="ledge",
            name="Crumbling Ledge"
        )
        circuit.environmental.stability = 0.5
        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.5,
            source_id="explosion"
        )
        circuit.receive_signal(signal)
        assert circuit.environmental.stability < 0.5

    def test_collapse_on_low_stability(self):
        """Test collapse when stability reaches zero."""
        circuit = EnvironmentalCircuit(
            id="ledge",
            name="Crumbling Ledge"
        )
        circuit.environmental.stability = 0.1
        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.9,
            source_id="explosion"
        )
        outputs = circuit.receive_signal(signal)
        # Should collapse
        assert any(o.type == SignalType.COLLAPSE for o in outputs)

    def test_heat_increases_temperature(self):
        """Test heat increases temperature."""
        circuit = EnvironmentalCircuit(
            id="rock",
            name="Rock"
        )
        initial_temp = circuit.environmental.temperature
        signal = InputSignal(
            type=SignalType.HEAT,
            strength=0.5,
            source_id="fire"
        )
        circuit.receive_signal(signal)
        assert circuit.environmental.temperature > initial_temp

    def test_cold_decreases_temperature(self):
        """Test cold decreases temperature."""
        circuit = EnvironmentalCircuit(
            id="water",
            name="Water",
            terrain_type="water"
        )
        circuit.environmental.temperature = 20.0
        signal = InputSignal(
            type=SignalType.COLD,
            strength=0.5,
            source_id="ice"
        )
        circuit.receive_signal(signal)
        assert circuit.environmental.temperature < 20.0

    def test_wet_increases_moisture(self):
        """Test wet signal increases moisture."""
        circuit = EnvironmentalCircuit(
            id="soil",
            name="Soil"
        )
        initial_moisture = circuit.environmental.moisture
        signal = InputSignal(
            type=SignalType.WET,
            strength=0.5,
            source_id="rain"
        )
        circuit.receive_signal(signal)
        assert circuit.environmental.moisture > initial_moisture

    def test_serialization(self):
        """Test environmental circuit serialization."""
        circuit = EnvironmentalCircuit(
            id="volcano",
            name="Volcanic Vent",
            terrain_type="rock"
        )
        circuit.environmental.temperature = 500.0
        data = circuit.to_dict()
        assert data["environmental"]["temperature"] == 500.0


class TestCircuitTypeInteractions:
    """Test interactions between different circuit types."""

    def test_biological_flees_from_damage(self):
        """Test biological circuits flee from damage if fearful."""
        rat = BiologicalCircuit(
            id="rat",
            name="Rat",
            species="rat"
        )
        rat.biological.fear = 0.8
        rat.biological.aggression = 0.2

        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.3,
            source_id="player"
        )
        outputs = rat.receive_signal(signal)
        # Fearful rat should flee from damage
        assert any(o.type == SignalType.FLEE for o in outputs)

    def test_mechanical_conducts_electricity(self):
        """Test metal mechanical circuits conduct electricity."""
        gear = MechanicalCircuit(
            id="gear",
            name="Metal Gear",
            material="metal"
        )

        signal = InputSignal(
            type=SignalType.ELECTRIC,
            strength=0.5,
            source_id="wire"
        )
        outputs = gear.receive_signal(signal)
        # Metal conducts and emits spark
        assert any(o.type == SignalType.EMIT for o in outputs)
