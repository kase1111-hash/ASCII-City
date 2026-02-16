"""
Specialized circuit types: Mechanical, Biological, Environmental.

Each type has unique properties and default behaviors.
"""

from dataclasses import dataclass
import random

from .circuit import BehaviorCircuit, CircuitType, CircuitState
from .signals import SignalType, InputSignal, OutputSignal


@dataclass
class MechanicalProperties:
    """Properties specific to mechanical circuits."""
    material: str = "metal"        # metal, wood, plastic, stone
    lubrication: float = 1.0       # Affects friction/jamming (0-1)
    wear: float = 0.0              # Degradation (0-1)
    powered: bool = False          # Requires power to function
    jammed: bool = False           # Currently stuck

    def apply_wear(self, amount: float) -> None:
        """Apply wear to the mechanism."""
        self.wear = min(1.0, self.wear + amount)
        # High wear increases jam chance
        if self.wear > 0.7 and random.random() < self.wear * 0.1:
            self.jammed = True

    def lubricate(self, amount: float = 0.3) -> None:
        """Apply lubrication."""
        self.lubrication = min(1.0, self.lubrication + amount)
        # Good lubrication can unjam
        if self.lubrication > 0.7:
            self.jammed = False

    def to_dict(self) -> dict:
        return {
            "material": self.material,
            "lubrication": self.lubrication,
            "wear": self.wear,
            "powered": self.powered,
            "jammed": self.jammed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MechanicalProperties':
        return cls(
            material=data.get("material", "metal"),
            lubrication=data.get("lubrication", 1.0),
            wear=data.get("wear", 0.0),
            powered=data.get("powered", False),
            jammed=data.get("jammed", False)
        )


class MechanicalCircuit(BehaviorCircuit):
    """
    Circuit for mechanical objects (buttons, doors, gears, etc.)

    Responds predictably with wear/degradation over time.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        material: str = "metal",
        powered: bool = False,
        **kwargs
    ):
        super().__init__(
            id=id,
            name=name,
            circuit_type=CircuitType.MECHANICAL,
            description=description,
            input_signals=[
                SignalType.PRESS,
                SignalType.KICK,
                SignalType.PUSH,
                SignalType.PULL,
                SignalType.DAMAGE,
                SignalType.ELECTRIC,
            ],
            output_signals=[
                SignalType.ACTIVATE,
                SignalType.DEACTIVATE,
                SignalType.SOUND,
                SignalType.MOVE,
                SignalType.COLLAPSE,
            ],
            affordances=["pressable", "breakable", "repairable"],
            **kwargs
        )
        self.mechanical = MechanicalProperties(
            material=material,
            powered=powered
        )
        self.set_processor(self._mechanical_process)

    def _mechanical_process(
        self,
        circuit: BehaviorCircuit,
        signal: InputSignal
    ) -> list[OutputSignal]:
        """Process signals for mechanical behavior."""
        outputs = []

        # Check if jammed
        if self.mechanical.jammed:
            # Only very strong signals can unjam
            if signal.strength > 0.9:
                self.mechanical.jammed = False
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.8,
                    source_id=self.id,
                    data={"sound": "grinding_unjam"}
                ))
            else:
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.3,
                    source_id=self.id,
                    data={"sound": "stuck_rattle"}
                ))
                return outputs

        # Check power requirement
        if self.mechanical.powered and self.state.power <= 0:
            return outputs  # No power, no response

        # Process based on signal type
        if signal.type == SignalType.PRESS:
            # Activation attempt
            success_chance = 1.0 - self.mechanical.wear * 0.5
            if random.random() < success_chance:
                outputs.append(OutputSignal(
                    type=SignalType.ACTIVATE,
                    strength=signal.strength,
                    source_id=self.id
                ))
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.3,
                    source_id=self.id,
                    data={"sound": "click"}
                ))
            else:
                # Failed, increase wear
                self.mechanical.apply_wear(0.05)
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.2,
                    source_id=self.id,
                    data={"sound": "grinding"}
                ))

        elif signal.type == SignalType.KICK:
            # Forceful impact
            self.mechanical.apply_wear(signal.strength * 0.1)
            self.state.apply_damage(signal.strength * 0.15)
            outputs.append(OutputSignal(
                type=SignalType.SOUND,
                strength=signal.strength * 0.7,
                source_id=self.id,
                data={"sound": "impact_metal" if self.mechanical.material == "metal" else "impact"}
            ))

            # Might trigger if hit hard enough
            if signal.strength > 0.6:
                outputs.append(OutputSignal(
                    type=SignalType.ACTIVATE,
                    strength=signal.strength * 0.5,
                    source_id=self.id
                ))

        elif signal.type == SignalType.ELECTRIC:
            if self.mechanical.material == "metal":
                # Conduct electricity
                if self.mechanical.powered:
                    self.state.power = min(1.0, self.state.power + signal.strength)
                outputs.append(OutputSignal(
                    type=SignalType.EMIT,
                    strength=signal.strength * 0.8,
                    source_id=self.id,
                    data={"type": "spark"}
                ))

        elif signal.type == SignalType.DAMAGE:
            destroyed = self.state.apply_damage(signal.strength)
            if destroyed:
                outputs.append(OutputSignal(
                    type=SignalType.COLLAPSE,
                    strength=1.0,
                    source_id=self.id
                ))
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.9,
                    source_id=self.id,
                    data={"sound": "destruction"}
                ))

        return outputs

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["mechanical"] = self.mechanical.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'MechanicalCircuit':
        mech_data = data.get("mechanical", {})
        circuit = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            material=mech_data.get("material", "metal"),
            powered=mech_data.get("powered", False),
        )
        circuit.state = CircuitState.from_dict(data.get("state", {}))
        circuit.mechanical = MechanicalProperties.from_dict(mech_data)
        circuit.affordances = data.get("affordances", [])
        circuit.history = data.get("history", [])
        return circuit


@dataclass
class BiologicalProperties:
    """Properties specific to biological circuits."""
    species: str = "unknown"
    fear: float = 0.5              # 0-1 fear level
    hunger: float = 0.5            # 0-1 hunger level
    curiosity: float = 0.5         # 0-1 curiosity level
    aggression: float = 0.3        # 0-1 base aggression
    loyalty: float = 0.0           # 0-1 loyalty to player
    alert: bool = False            # Currently alert/aware

    def get_dominant_drive(self) -> str:
        """Get the current dominant behavioral drive."""
        drives = {
            "fear": self.fear,
            "hunger": self.hunger,
            "curiosity": self.curiosity,
            "aggression": self.aggression
        }
        return max(drives, key=drives.get)

    def update_from_signal(self, signal_type: SignalType, strength: float) -> None:
        """Update emotional state based on signal."""
        if signal_type in (SignalType.DAMAGE, SignalType.KICK, SignalType.SHOUT):
            self.fear = min(1.0, self.fear + strength * 0.3)
            self.aggression = min(1.0, self.aggression + strength * 0.1)
            self.alert = True
        elif signal_type == SignalType.PROXIMITY:
            if strength > 0.5:
                self.alert = True
        elif signal_type == SignalType.SAY:
            # Talking can calm or agitate
            self.fear = max(0.0, self.fear - 0.1)
            self.curiosity = min(1.0, self.curiosity + 0.1)

    def to_dict(self) -> dict:
        return {
            "species": self.species,
            "fear": self.fear,
            "hunger": self.hunger,
            "curiosity": self.curiosity,
            "aggression": self.aggression,
            "loyalty": self.loyalty,
            "alert": self.alert
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BiologicalProperties':
        return cls(
            species=data.get("species", "unknown"),
            fear=data.get("fear", 0.5),
            hunger=data.get("hunger", 0.5),
            curiosity=data.get("curiosity", 0.5),
            aggression=data.get("aggression", 0.3),
            loyalty=data.get("loyalty", 0.0),
            alert=data.get("alert", False)
        )


class BiologicalCircuit(BehaviorCircuit):
    """
    Circuit for living entities (creatures, NPCs).

    Has emotional states and responds based on personality.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        species: str = "unknown",
        **kwargs
    ):
        super().__init__(
            id=id,
            name=name,
            circuit_type=CircuitType.BIOLOGICAL,
            description=description,
            input_signals=[
                SignalType.PROXIMITY,
                SignalType.SOUND,
                SignalType.SAY,
                SignalType.SHOUT,
                SignalType.DAMAGE,
                SignalType.KICK,
                SignalType.LOOK,
            ],
            output_signals=[
                SignalType.MOVE,
                SignalType.FLEE,
                SignalType.ATTACK,
                SignalType.SPEAK,
                SignalType.SOUND,
                SignalType.ALERT,
                SignalType.COLLAPSE,
            ],
            affordances=["talkable", "observable"],
            **kwargs
        )
        self.biological = BiologicalProperties(species=species)
        self.set_processor(self._biological_process)

    def _biological_process(
        self,
        circuit: BehaviorCircuit,
        signal: InputSignal
    ) -> list[OutputSignal]:
        """Process signals for biological behavior."""
        outputs = []

        # Update emotional state
        self.biological.update_from_signal(signal.type, signal.strength)

        # React based on drive and signal
        if signal.type == SignalType.PROXIMITY:
            if self.biological.fear > 0.7:
                # Flee response
                outputs.append(OutputSignal(
                    type=SignalType.FLEE,
                    strength=self.biological.fear,
                    source_id=self.id,
                    data={"direction": "away_from_source"}
                ))
            elif self.biological.aggression > 0.6 and self.biological.fear < 0.4:
                # Attack response
                outputs.append(OutputSignal(
                    type=SignalType.ATTACK,
                    strength=self.biological.aggression,
                    source_id=self.id
                ))
            elif self.biological.curiosity > 0.5:
                # Investigate
                outputs.append(OutputSignal(
                    type=SignalType.MOVE,
                    strength=0.3,
                    source_id=self.id,
                    data={"direction": "toward_source"}
                ))

        elif signal.type == SignalType.SOUND:
            if signal.strength > 0.5:
                self.biological.alert = True
                outputs.append(OutputSignal(
                    type=SignalType.ALERT,
                    strength=signal.strength,
                    source_id=self.id
                ))
                # Look toward sound
                if self.biological.curiosity > self.biological.fear:
                    outputs.append(OutputSignal(
                        type=SignalType.MOVE,
                        strength=0.2,
                        source_id=self.id,
                        data={"direction": signal.direction}
                    ))

        elif signal.type == SignalType.DAMAGE:
            # Pain response
            destroyed = self.state.apply_damage(signal.strength)
            if destroyed:
                outputs.append(OutputSignal(
                    type=SignalType.COLLAPSE,
                    strength=1.0,
                    source_id=self.id
                ))
            else:
                # Cry out
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.8,
                    source_id=self.id,
                    data={"sound": "pain_cry"}
                ))
                # Fight or flight
                if self.biological.aggression > self.biological.fear:
                    outputs.append(OutputSignal(
                        type=SignalType.ATTACK,
                        strength=min(1.0, self.biological.aggression + 0.2),
                        source_id=self.id
                    ))
                else:
                    outputs.append(OutputSignal(
                        type=SignalType.FLEE,
                        strength=min(1.0, self.biological.fear + 0.3),
                        source_id=self.id
                    ))

        elif signal.type == SignalType.SAY:
            # Communication response
            if self.biological.loyalty > 0.5:
                outputs.append(OutputSignal(
                    type=SignalType.SPEAK,
                    strength=0.5,
                    source_id=self.id,
                    data={"response": "friendly"}
                ))
            elif self.biological.fear > 0.5:
                outputs.append(OutputSignal(
                    type=SignalType.SPEAK,
                    strength=0.3,
                    source_id=self.id,
                    data={"response": "nervous"}
                ))

        return outputs

    def update(self, delta_time: float) -> list[OutputSignal]:
        """Update biological state over time."""
        outputs = super().update(delta_time)

        # Gradually calm down
        if self.biological.fear > 0.0:
            self.biological.fear = max(0.0, self.biological.fear - delta_time * 0.01)
        if self.biological.alert and random.random() < delta_time * 0.1:
            self.biological.alert = False

        # Hunger increases over time
        self.biological.hunger = min(1.0, self.biological.hunger + delta_time * 0.001)

        return outputs

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["biological"] = self.biological.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'BiologicalCircuit':
        bio_data = data.get("biological", {})
        circuit = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            species=bio_data.get("species", "unknown"),
        )
        circuit.state = CircuitState.from_dict(data.get("state", {}))
        circuit.biological = BiologicalProperties.from_dict(bio_data)
        circuit.affordances = data.get("affordances", [])
        circuit.history = data.get("history", [])
        return circuit


@dataclass
class EnvironmentalProperties:
    """Properties specific to environmental circuits."""
    terrain_type: str = "rock"
    fluid: bool = False            # Contains fluid
    stability: float = 1.0         # Structural stability (0-1)
    temperature: float = 20.0      # Celsius
    moisture: float = 0.0          # 0-1 moisture level
    emitting: bool = False         # Currently emitting something

    def to_dict(self) -> dict:
        return {
            "terrain_type": self.terrain_type,
            "fluid": self.fluid,
            "stability": self.stability,
            "temperature": self.temperature,
            "moisture": self.moisture,
            "emitting": self.emitting
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EnvironmentalProperties':
        return cls(
            terrain_type=data.get("terrain_type", "rock"),
            fluid=data.get("fluid", False),
            stability=data.get("stability", 1.0),
            temperature=data.get("temperature", 20.0),
            moisture=data.get("moisture", 0.0),
            emitting=data.get("emitting", False)
        )


class EnvironmentalCircuit(BehaviorCircuit):
    """
    Circuit for environmental features (waterfalls, cliffs, hazards).

    Responds to physics and propagates effects.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        terrain_type: str = "rock",
        **kwargs
    ):
        super().__init__(
            id=id,
            name=name,
            circuit_type=CircuitType.ENVIRONMENTAL,
            description=description,
            input_signals=[
                SignalType.DAMAGE,
                SignalType.PUSH,
                SignalType.HEAT,
                SignalType.COLD,
                SignalType.WET,
                SignalType.PROXIMITY,
            ],
            output_signals=[
                SignalType.COLLAPSE,
                SignalType.SOUND,
                SignalType.EMIT,
                SignalType.DAMAGE,
                SignalType.TRIGGER,
            ],
            affordances=["observable"],
            **kwargs
        )
        self.environmental = EnvironmentalProperties(terrain_type=terrain_type)
        self.set_processor(self._environmental_process)

        # Add terrain-specific affordances
        from .affordances import get_default_affordances
        self.affordances.extend(get_default_affordances(terrain_type))

    def _environmental_process(
        self,
        circuit: BehaviorCircuit,
        signal: InputSignal
    ) -> list[OutputSignal]:
        """Process signals for environmental behavior."""
        outputs = []

        if signal.type == SignalType.DAMAGE:
            # Structural damage
            damage = signal.strength * 0.2
            self.environmental.stability = max(0.0, self.environmental.stability - damage)

            if self.environmental.stability <= 0:
                # Collapse
                outputs.append(OutputSignal(
                    type=SignalType.COLLAPSE,
                    strength=1.0,
                    source_id=self.id,
                    radius=3.0
                ))
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=1.0,
                    source_id=self.id,
                    data={"sound": "collapse"}
                ))
                # May reveal hidden things
                outputs.append(OutputSignal(
                    type=SignalType.TRIGGER,
                    strength=1.0,
                    source_id=self.id,
                    data={"trigger": "reveal_hidden"}
                ))
            else:
                # Cracking sound
                outputs.append(OutputSignal(
                    type=SignalType.SOUND,
                    strength=signal.strength * 0.5,
                    source_id=self.id,
                    data={"sound": "cracking"}
                ))

        elif signal.type == SignalType.PUSH:
            if self.environmental.stability < 0.5:
                # Weak structures can be pushed over
                outputs.append(OutputSignal(
                    type=SignalType.MOVE,
                    strength=signal.strength,
                    source_id=self.id
                ))

        elif signal.type == SignalType.HEAT:
            self.environmental.temperature += signal.strength * 50
            # Water evaporates
            if self.environmental.fluid and self.environmental.temperature > 100:
                self.environmental.moisture = max(0, self.environmental.moisture - 0.1)
                outputs.append(OutputSignal(
                    type=SignalType.EMIT,
                    strength=0.5,
                    source_id=self.id,
                    data={"type": "steam"}
                ))

        elif signal.type == SignalType.COLD:
            self.environmental.temperature -= signal.strength * 30
            # Water freezes
            if self.environmental.fluid and self.environmental.temperature < 0:
                self.environmental.fluid = False
                # Now walkable
                if "swimmable" in self.affordances:
                    self.affordances.remove("swimmable")
                    self.affordances.append("walkable")
                    self.affordances.append("slippery")

        elif signal.type == SignalType.WET:
            self.environmental.moisture = min(1.0, self.environmental.moisture + signal.strength)
            if self.environmental.moisture > 0.7:
                if "slippery" not in self.affordances:
                    self.affordances.append("slippery")

        elif signal.type == SignalType.PROXIMITY:
            # Proximity to environmental hazards
            if self.environmental.terrain_type == "void":
                # Near edge - danger!
                if signal.strength > 0.8:
                    outputs.append(OutputSignal(
                        type=SignalType.DAMAGE,
                        strength=0.3,
                        source_id=self.id,
                        data={"type": "fall_damage"}
                    ))

        return outputs

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["environmental"] = self.environmental.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'EnvironmentalCircuit':
        env_data = data.get("environmental", {})
        circuit = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            terrain_type=env_data.get("terrain_type", "rock"),
        )
        circuit.state = CircuitState.from_dict(data.get("state", {}))
        circuit.environmental = EnvironmentalProperties.from_dict(env_data)
        circuit.affordances = data.get("affordances", [])
        circuit.history = data.get("history", [])
        return circuit
