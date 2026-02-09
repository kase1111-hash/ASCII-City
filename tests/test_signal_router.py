"""Tests for SignalRouter — routing circuit output signals to game effects."""

import pytest
from unittest.mock import MagicMock

from src.shadowengine.signal_router import SignalRouter
from src.shadowengine.game import GameState
from src.shadowengine.render import Location, Renderer
from src.shadowengine.interaction import Hotspot, HotspotType
from src.shadowengine.circuits import (
    BehaviorCircuit, CircuitType, SignalType, InputSignal, OutputSignal,
    ProcessingResult,
)
from src.shadowengine.character import Character, Archetype
from src.shadowengine.memory import EventType


@pytest.fixture
def mock_renderer():
    return MagicMock(spec=Renderer)


@pytest.fixture
def router(mock_renderer):
    return SignalRouter(renderer=mock_renderer)


@pytest.fixture
def state():
    s = GameState()
    loc = Location(id="bar", name="The Bar", description="A smoky bar.")
    s.locations["bar"] = loc
    s.current_location_id = "bar"
    s.environment.register_location("bar", is_indoor=True)
    return s


@pytest.fixture
def hotspot_with_circuit():
    circuit = BehaviorCircuit(
        id="crate_circuit",
        name="Wooden Crate",
        circuit_type=CircuitType.MECHANICAL,
        input_signals=[SignalType.LOOK, SignalType.KICK, SignalType.PRESS, SignalType.PULL],
        output_signals=[SignalType.SOUND, SignalType.COLLAPSE, SignalType.ACTIVATE],
    )
    hs = Hotspot(
        id="hs_crate", label="Wooden Crate", hotspot_type=HotspotType.OBJECT,
        position=(20, 10), description="A battered wooden crate.",
        examine_text="The crate is held together by rusty nails.",
    )
    hs.circuit = circuit
    return hs


def _make_result(circuit_id, outputs):
    """Helper to build a ProcessingResult with given outputs."""
    return ProcessingResult(
        circuit_id=circuit_id,
        input_signal=InputSignal(type=SignalType.KICK, strength=0.7, source_id="player"),
        output_signals=outputs,
    )


class TestSoundRouting:
    """Test SOUND signal routing."""

    def test_sound_renders_narration(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.SOUND, strength=0.5, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        router.renderer.render_narration.assert_called()

    def test_quiet_sound_no_narration(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.SOUND, strength=0.1, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        router.renderer.render_narration.assert_not_called()

    def test_sound_creates_witness_beliefs(self, router, state, hotspot_with_circuit):
        # Add an NPC at the location
        char = Character(
            id="bartender", name="Joe", archetype=Archetype.INNOCENT,
            description="The bartender.",
        )
        state.characters["bartender"] = char
        state.memory.register_character("bartender")
        npc_hs = Hotspot.create_person(
            id="hs_bartender", name="Joe", position=(30, 10),
            character_id="bartender", description="The bartender.",
        )
        state.locations["bar"].add_hotspot(npc_hs)

        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.SOUND, strength=0.6, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.beliefs) >= 1
        assert any("sound" in b.content.lower() for b in char_mem.beliefs)

    def test_sound_custom_description(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(
                type=SignalType.SOUND, strength=0.8, source_id="crate_circuit",
                data={"description": "The crate groans under the impact."},
            ),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        router.renderer.render_narration.assert_called_with("The crate groans under the impact.")


class TestCollapseRouting:
    """Test COLLAPSE signal routing."""

    def test_collapse_deactivates_hotspot(self, router, state, hotspot_with_circuit):
        state.locations["bar"].add_hotspot(hotspot_with_circuit)

        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.COLLAPSE, strength=1.0, source_id="crate_circuit"),
        ])

        assert hotspot_with_circuit.active
        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])
        assert not hotspot_with_circuit.active

    def test_collapse_renders_narration(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.COLLAPSE, strength=1.0, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        router.renderer.render_narration.assert_called()
        args = router.renderer.render_narration.call_args[0]
        assert "break" in args[0].lower() or "crate" in args[0].lower()

    def test_collapse_reveals_fact(self, router, state, hotspot_with_circuit):
        hotspot_with_circuit.reveals_fact = "hidden_stash"
        hotspot_with_circuit.examine_text = "Inside the crate: a bundle of cash."

        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.COLLAPSE, strength=1.0, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        assert "hidden_stash" in state.memory.player.discoveries
        router.renderer.render_discovery.assert_called()

    def test_collapse_notifies_npcs(self, router, state, hotspot_with_circuit):
        char = Character(
            id="witness", name="Witness", archetype=Archetype.SURVIVOR,
            description="A witness.",
        )
        state.characters["witness"] = char
        state.memory.register_character("witness")
        npc_hs = Hotspot.create_person(
            id="hs_witness", name="Witness", position=(30, 10),
            character_id="witness", description="A witness.",
        )
        state.locations["bar"].add_hotspot(npc_hs)

        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.COLLAPSE, strength=1.0, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        char_mem = state.memory.get_character_memory("witness")
        assert len(char_mem.beliefs) >= 1
        assert any("destroyed" in b.content.lower() for b in char_mem.beliefs)


class TestActivateRouting:
    """Test ACTIVATE signal routing."""

    def test_activate_triggers_connected_circuit(self, router, state):
        # Create two hotspots with circuits, one connecting to the other
        button_circuit = BehaviorCircuit(
            id="button_circuit",
            name="Button",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.ACTIVATE],
        )
        button_hs = Hotspot(
            id="hs_button", label="Red Button", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="A red button.",
        )
        button_hs.circuit = button_circuit

        door_circuit = BehaviorCircuit(
            id="door_circuit",
            name="Heavy Door",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.MOVE],
        )
        door_hs = Hotspot(
            id="hs_door_target", label="Heavy Door", hotspot_type=HotspotType.OBJECT,
            position=(20, 10), description="A heavy metal door.",
        )
        door_hs.circuit = door_circuit

        state.locations["bar"].add_hotspot(button_hs)
        state.locations["bar"].add_hotspot(door_hs)

        # Button emits ACTIVATE targeting the door
        result = _make_result("button_circuit", [
            OutputSignal(
                type=SignalType.ACTIVATE, strength=0.8,
                source_id="button_circuit", target_id="hs_door_target",
            ),
        ])

        initial_history_len = len(door_circuit.history)
        router.route_outputs(result, button_hs, state, state.locations["bar"])

        # Door circuit should have received a signal
        assert len(door_circuit.history) > initial_history_len


class TestTriggerRouting:
    """Test TRIGGER signal routing."""

    def test_trigger_creates_discovery(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(
                type=SignalType.TRIGGER, strength=0.5, source_id="crate_circuit",
                data={"fact_id": "secret_compartment", "description": "A hidden compartment opens."},
            ),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        assert "secret_compartment" in state.memory.player.discoveries
        router.renderer.render_discovery.assert_called_with("A hidden compartment opens.")

    def test_trigger_reveals_hidden_hotspot(self, router, state, hotspot_with_circuit):
        hidden_hs = Hotspot(
            id="hs_secret", label="Secret Note", hotspot_type=HotspotType.EVIDENCE,
            position=(15, 10), description="A hidden note.",
        )
        hidden_hs.hide()
        state.locations["bar"].add_hotspot(hidden_hs)

        result = _make_result("crate_circuit", [
            OutputSignal(
                type=SignalType.TRIGGER, strength=0.5, source_id="crate_circuit",
                data={
                    "reveal_hotspot": "hs_secret",
                    "reveal_text": "A hidden note falls from the crate.",
                },
            ),
        ])

        assert not hidden_hs.visible
        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])
        assert hidden_hs.visible
        router.renderer.render_narration.assert_called_with("A hidden note falls from the crate.")


class TestAlertRouting:
    """Test ALERT signal routing."""

    def test_alert_notifies_npcs(self, router, state, hotspot_with_circuit):
        char = Character(
            id="witness", name="Witness", archetype=Archetype.SURVIVOR,
            description="A witness.",
        )
        state.characters["witness"] = char
        state.memory.register_character("witness")
        npc_hs = Hotspot.create_person(
            id="hs_witness", name="Witness", position=(30, 10),
            character_id="witness", description="A witness.",
        )
        state.locations["bar"].add_hotspot(npc_hs)

        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.ALERT, strength=0.8, source_id="crate_circuit"),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        char_mem = state.memory.get_character_memory("witness")
        assert len(char_mem.beliefs) >= 1


class TestEmitRouting:
    """Test EMIT signal routing."""

    def test_emit_renders_narration(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(
                type=SignalType.EMIT, strength=0.5, source_id="crate_circuit",
                data={"description": "Dust and splinters fly from the crate."},
            ),
        ])

        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])

        router.renderer.render_narration.assert_called_with("Dust and splinters fly from the crate.")


class TestEmptyAndFailed:
    """Edge cases for the router."""

    def test_no_outputs_noop(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [])
        router.route_outputs(result, hotspot_with_circuit, state)
        router.renderer.render_narration.assert_not_called()

    def test_failed_result_noop(self, router, state, hotspot_with_circuit):
        result = ProcessingResult(
            circuit_id="crate_circuit",
            input_signal=InputSignal(type=SignalType.KICK, strength=0.7),
            success=False,
            error="test error",
        )
        router.route_outputs(result, hotspot_with_circuit, state)
        router.renderer.render_narration.assert_not_called()

    def test_unknown_signal_type_ignored(self, router, state, hotspot_with_circuit):
        result = _make_result("crate_circuit", [
            OutputSignal(type=SignalType.FLEE, strength=0.5, source_id="crate_circuit"),
        ])
        # Should not crash — just silently ignored
        router.route_outputs(result, hotspot_with_circuit, state, state.locations["bar"])
