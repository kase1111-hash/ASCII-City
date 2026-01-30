# Claude.md - ShadowEngine (ASCII-City)

## Project Overview

ShadowEngine is an AI-driven ASCII game engine that creates a fully reactive, LLM-powered game universe. Every object, creature, and environmental element functions as an interactive "behavioral circuit" with emergent properties. The engine enables natural language game interaction and emergent storytelling through AI simulation.

**Key Philosophy**: Memory-first architecture - player input never follows rigid scripts. The world reacts dynamically based on player actions, NPC memory, and systemic simulations.

## Tech Stack

- **Language**: Python 3.10+
- **Interface**: Terminal/CMD/Shell (cross-platform)
- **LLM Backend**: Ollama (default) or OpenAI API
- **Testing**: pytest 7.0+, pytest-cov 4.0+
- **Audio** (optional): pyttsx3, coqui-tts, sounddevice
- **Speech-to-Text** (optional): openai-whisper, vosk

The core game runs on Python stdlib alone. Optional features have dependencies in `requirements.txt`.

## Quick Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Run game
python main.py

# Run tests
pytest                    # All 2631 tests
pytest -v                 # Verbose output
pytest -m unit            # Only unit tests
pytest -m integration     # Only integration tests
pytest --cov=shadowengine # With coverage

# Windows shortcuts
build.bat                 # Setup environment
run.bat                   # Run game
run.bat --test            # Run tests
```

## Project Structure

```
src/shadowengine/           # Main source (116 Python files)
├── game.py                 # Main game engine
├── world_state.py          # State consistency for LLM
├── config.py               # Game & theme configuration
├── circuits/               # Universal behavior model (BehaviorCircuit)
├── grid/                   # Tile-based world system
├── memory/                 # Three-layer memory system
├── character/              # NPC simulation
├── narrative/              # Story generation (spine, shades, twists)
├── interaction/            # Command parsing & hotspots
├── render/                 # ASCII rendering
├── environment/            # Weather, time systems
├── inventory/              # Item management
├── llm/                    # LLM integration (Ollama/OpenAI)
├── modding/                # Extensibility (themes, archetypes)
├── studio/                 # ASCII Art Studio
├── voice/                  # Speech-to-text
├── audio/                  # Audio & TTS
├── npc_intelligence/       # Rumor networks, social dynamics
├── inspection/             # Zoom inspection system
├── moral/                  # Moral consequence tracking
├── replay/                 # Deterministic replay & seeds
└── scenarios/              # Built-in game scenarios

tests/                      # 107 test files mirroring src/ structure
docs/                       # Architecture, design, roadmap docs
docs/modules/               # 12 detailed module specifications
```

## Key Patterns and Conventions

### Behavioral Circuits (Universal Entity Model)

Every interactive entity uses this structure:

```python
BehaviorCircuit {
    id: str
    type: CircuitType  # MECHANICAL, BIOLOGICAL, ENVIRONMENTAL
    input_signals: list[InputSignal]   # What triggers it
    process: dict                       # LLM evaluation context
    output_signals: list[OutputSignal]  # What it produces
    state: CircuitState                 # Health, power, fatigue, trust
    affordances: list[str]              # Possible interactions
}
```

### Three-Layer Memory System

```python
MemoryBank:
    world: WorldMemory           # Objective truth (facts, events)
    player: PlayerMemory         # Player's discoveries and inventory
    character: dict[str, CharacterMemory]  # Per-NPC personal memories
```

### Code Conventions

- **Dataclasses**: Use `@dataclass` for data structures
- **Enums**: Use for type safety (e.g., `Archetype`, `CircuitType`)
- **Type hints**: Full annotations throughout codebase
- **Docstrings**: Every module, class, and function documented
- **Serialization**: `to_dict()`/`from_dict()` methods for JSON save/load
- **Deterministic seeding**: All randomness uses seeded PRNG for replay

### LLM Integration

```python
# Pluggable backends with fallback when unavailable
LLMBackend: OLLAMA | OPENAI | MOCK
```

### Command Parser (Fail-Soft)

- Extensive verb mappings (examine, talk, take, use, go)
- Typo tolerance and helpful error messages
- Supports natural language intent parsing

## Testing

Test markers available in `pytest.ini`:
- `unit` - Unit tests
- `integration` - Integration tests
- `slow` - Slow-running tests
- `procedural`, `memory`, `character`, `narrative`, `interaction`, `render`, `environment`, `inventory`

Fixtures defined in `tests/conftest.py` provide reusable test objects.

## Architecture Overview

```
INPUT (STT/Text) → LLM Brain (Intent parsing)
  → Behavioral Circuits (Process signals)
  → Simulation Layer (Update world state)
  → Memory System (Record events)
  → ASCII Renderer (Generate scene)
  → Audio Engine (Generate sound)
  → OUTPUT (Terminal + Audio)
```

### Design Principles

1. **Memory First** - Nothing meaningful happens without being remembered
2. **Systems Over Scripts** - Characters obey rules, not dialogue trees
3. **Behavioral Circuits** - Unified interaction model for all entities
4. **Procedural ≠ Random** - All randomness constrained by logic
5. **Atmosphere Is Mechanics** - Visuals communicate game state
6. **Player Is Creator** - User art becomes world content

## Important Files

- `main.py` - Entry point
- `src/shadowengine/game.py` - Main game engine (largest module)
- `src/shadowengine/world_state.py` - LLM state consistency
- `src/shadowengine/circuits/circuit.py` - Core BehaviorCircuit class
- `src/shadowengine/memory/memory_bank.py` - Main memory manager
- `tests/conftest.py` - Shared test fixtures

## Documentation

- `README.md` - Project overview
- `docs/ARCHITECTURE.md` - System design & data flow
- `docs/DESIGN.md` - Complete design vision
- `docs/ROADMAP.md` - Development plan
- `docs/modules/` - 12 detailed module specifications
- `SPEC_*.md` - Technical specifications (10 files)
