"""
Sound Effect Library - Predefined sound effects.

Provides a categorized library of sound effects for
various game events and situations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

from .sound import (
    SoundEffect,
    SoundCategory,
    SoundTrigger,
    SoundProperties,
    SoundGenerator
)
from .tts_engine import AudioData


class SoundID(Enum):
    """Identifiers for predefined sounds."""
    # Footsteps
    FOOTSTEP_WOOD = "footstep_wood"
    FOOTSTEP_CONCRETE = "footstep_concrete"
    FOOTSTEP_GRAVEL = "footstep_gravel"
    FOOTSTEP_WATER = "footstep_water"
    FOOTSTEP_CARPET = "footstep_carpet"
    FOOTSTEP_METAL = "footstep_metal"

    # Doors
    DOOR_OPEN = "door_open"
    DOOR_CLOSE = "door_close"
    DOOR_CREAK = "door_creak"
    DOOR_KNOCK = "door_knock"
    DOOR_LOCK = "door_lock"
    DOOR_UNLOCK = "door_unlock"

    # Impacts
    IMPACT_SOFT = "impact_soft"
    IMPACT_HARD = "impact_hard"
    IMPACT_GLASS = "impact_glass"
    IMPACT_METAL = "impact_metal"

    # Weather
    RAIN_LIGHT = "rain_light"
    RAIN_HEAVY = "rain_heavy"
    THUNDER_DISTANT = "thunder_distant"
    THUNDER_CLOSE = "thunder_close"
    WIND_LIGHT = "wind_light"
    WIND_STRONG = "wind_strong"

    # Ambience
    CITY_TRAFFIC = "city_traffic"
    CROWD_MURMUR = "crowd_murmur"
    ROOM_TONE = "room_tone"
    CLOCK_TICK = "clock_tick"

    # Actions
    GUNSHOT = "gunshot"
    PHONE_RING = "phone_ring"
    GLASS_CLINK = "glass_clink"
    PAPER_RUSTLE = "paper_rustle"
    TYPEWRITER = "typewriter"
    LIGHTER_FLICK = "lighter_flick"
    MATCH_STRIKE = "match_strike"
    CASH_REGISTER = "cash_register"

    # Horror
    HEARTBEAT = "heartbeat"
    BREATH_HEAVY = "breath_heavy"
    WHISPER = "whisper"
    SCREAM = "scream"
    CREAK_FLOOR = "creak_floor"
    DRIP_WATER = "drip_water"

    # UI
    UI_CLICK = "ui_click"
    UI_SELECT = "ui_select"
    UI_ERROR = "ui_error"
    UI_SUCCESS = "ui_success"

    # Music Stings
    STING_TENSION = "sting_tension"
    STING_REVEAL = "sting_reveal"
    STING_DANGER = "sting_danger"
    STING_MYSTERY = "sting_mystery"


@dataclass
class SoundDefinition:
    """Definition of a sound in the library."""
    id: SoundID
    name: str
    category: SoundCategory
    generator_type: str  # Type for SoundGenerator
    duration_ms: int
    properties: SoundProperties
    tags: List[str]
    variants: int = 1  # Number of variations


# Master sound library definition
SOUND_LIBRARY: Dict[SoundID, SoundDefinition] = {
    # Footsteps
    SoundID.FOOTSTEP_WOOD: SoundDefinition(
        id=SoundID.FOOTSTEP_WOOD,
        name="Footstep (Wood)",
        category=SoundCategory.FOOTSTEPS,
        generator_type="footstep",
        duration_ms=200,
        properties=SoundProperties(
            volume=0.6,
            pitch=1.0,
            pitch_variation=0.1,
            volume_variation=0.1
        ),
        tags=["footstep", "wood", "indoor"],
        variants=4
    ),
    SoundID.FOOTSTEP_CONCRETE: SoundDefinition(
        id=SoundID.FOOTSTEP_CONCRETE,
        name="Footstep (Concrete)",
        category=SoundCategory.FOOTSTEPS,
        generator_type="footstep",
        duration_ms=150,
        properties=SoundProperties(
            volume=0.7,
            pitch=0.9,
            pitch_variation=0.1,
            volume_variation=0.1
        ),
        tags=["footstep", "concrete", "outdoor"],
        variants=4
    ),
    SoundID.FOOTSTEP_GRAVEL: SoundDefinition(
        id=SoundID.FOOTSTEP_GRAVEL,
        name="Footstep (Gravel)",
        category=SoundCategory.FOOTSTEPS,
        generator_type="footstep",
        duration_ms=250,
        properties=SoundProperties(
            volume=0.8,
            pitch=1.2,
            pitch_variation=0.15,
            volume_variation=0.1
        ),
        tags=["footstep", "gravel", "outdoor"],
        variants=4
    ),
    SoundID.FOOTSTEP_WATER: SoundDefinition(
        id=SoundID.FOOTSTEP_WATER,
        name="Footstep (Water)",
        category=SoundCategory.FOOTSTEPS,
        generator_type="drip",
        duration_ms=300,
        properties=SoundProperties(
            volume=0.7,
            pitch=0.8,
            pitch_variation=0.2
        ),
        tags=["footstep", "water", "wet"],
        variants=3
    ),

    # Doors
    SoundID.DOOR_OPEN: SoundDefinition(
        id=SoundID.DOOR_OPEN,
        name="Door Open",
        category=SoundCategory.MECHANICAL,
        generator_type="door",
        duration_ms=500,
        properties=SoundProperties(volume=0.6),
        tags=["door", "open", "mechanical"],
        variants=2
    ),
    SoundID.DOOR_CLOSE: SoundDefinition(
        id=SoundID.DOOR_CLOSE,
        name="Door Close",
        category=SoundCategory.MECHANICAL,
        generator_type="click",
        duration_ms=200,
        properties=SoundProperties(volume=0.7, pitch=0.7),
        tags=["door", "close", "mechanical"],
        variants=2
    ),
    SoundID.DOOR_CREAK: SoundDefinition(
        id=SoundID.DOOR_CREAK,
        name="Door Creak",
        category=SoundCategory.HORROR,
        generator_type="creak",
        duration_ms=800,
        properties=SoundProperties(volume=0.5),
        tags=["door", "creak", "horror"],
        variants=3
    ),
    SoundID.DOOR_KNOCK: SoundDefinition(
        id=SoundID.DOOR_KNOCK,
        name="Door Knock",
        category=SoundCategory.MECHANICAL,
        generator_type="click",
        duration_ms=100,
        properties=SoundProperties(volume=0.8, pitch=0.6),
        tags=["door", "knock"],
        variants=2
    ),

    # Impacts
    SoundID.IMPACT_SOFT: SoundDefinition(
        id=SoundID.IMPACT_SOFT,
        name="Soft Impact",
        category=SoundCategory.IMPACTS,
        generator_type="footstep",
        duration_ms=150,
        properties=SoundProperties(volume=0.5, pitch=0.6),
        tags=["impact", "soft"],
        variants=3
    ),
    SoundID.IMPACT_HARD: SoundDefinition(
        id=SoundID.IMPACT_HARD,
        name="Hard Impact",
        category=SoundCategory.IMPACTS,
        generator_type="click",
        duration_ms=100,
        properties=SoundProperties(volume=0.9, pitch=0.5),
        tags=["impact", "hard"],
        variants=3
    ),
    SoundID.IMPACT_GLASS: SoundDefinition(
        id=SoundID.IMPACT_GLASS,
        name="Glass Impact",
        category=SoundCategory.IMPACTS,
        generator_type="click",
        duration_ms=300,
        properties=SoundProperties(volume=0.8, pitch=1.5),
        tags=["impact", "glass", "break"],
        variants=2
    ),

    # Weather
    SoundID.RAIN_LIGHT: SoundDefinition(
        id=SoundID.RAIN_LIGHT,
        name="Light Rain",
        category=SoundCategory.WEATHER,
        generator_type="rain",
        duration_ms=5000,
        properties=SoundProperties(volume=0.4),
        tags=["rain", "weather", "ambient"],
        variants=1
    ),
    SoundID.RAIN_HEAVY: SoundDefinition(
        id=SoundID.RAIN_HEAVY,
        name="Heavy Rain",
        category=SoundCategory.WEATHER,
        generator_type="rain",
        duration_ms=5000,
        properties=SoundProperties(volume=0.8),
        tags=["rain", "weather", "ambient", "storm"],
        variants=1
    ),
    SoundID.THUNDER_DISTANT: SoundDefinition(
        id=SoundID.THUNDER_DISTANT,
        name="Distant Thunder",
        category=SoundCategory.WEATHER,
        generator_type="thunder",
        duration_ms=3000,
        properties=SoundProperties(volume=0.5),
        tags=["thunder", "weather", "storm"],
        variants=3
    ),
    SoundID.THUNDER_CLOSE: SoundDefinition(
        id=SoundID.THUNDER_CLOSE,
        name="Close Thunder",
        category=SoundCategory.WEATHER,
        generator_type="thunder",
        duration_ms=2000,
        properties=SoundProperties(volume=1.0),
        tags=["thunder", "weather", "storm", "loud"],
        variants=3
    ),
    SoundID.WIND_LIGHT: SoundDefinition(
        id=SoundID.WIND_LIGHT,
        name="Light Wind",
        category=SoundCategory.WEATHER,
        generator_type="wind",
        duration_ms=5000,
        properties=SoundProperties(volume=0.3),
        tags=["wind", "weather", "ambient"],
        variants=1
    ),
    SoundID.WIND_STRONG: SoundDefinition(
        id=SoundID.WIND_STRONG,
        name="Strong Wind",
        category=SoundCategory.WEATHER,
        generator_type="wind",
        duration_ms=5000,
        properties=SoundProperties(volume=0.7),
        tags=["wind", "weather", "storm"],
        variants=1
    ),

    # Actions
    SoundID.GUNSHOT: SoundDefinition(
        id=SoundID.GUNSHOT,
        name="Gunshot",
        category=SoundCategory.IMPACTS,
        generator_type="gunshot",
        duration_ms=500,
        properties=SoundProperties(volume=1.0),
        tags=["gun", "weapon", "loud", "action"],
        variants=3
    ),
    SoundID.PHONE_RING: SoundDefinition(
        id=SoundID.PHONE_RING,
        name="Phone Ring",
        category=SoundCategory.MECHANICAL,
        generator_type="tone",
        duration_ms=1000,
        properties=SoundProperties(volume=0.7, pitch=1.2),
        tags=["phone", "ring", "alert"],
        variants=2
    ),
    SoundID.TYPEWRITER: SoundDefinition(
        id=SoundID.TYPEWRITER,
        name="Typewriter",
        category=SoundCategory.MECHANICAL,
        generator_type="click",
        duration_ms=80,
        properties=SoundProperties(
            volume=0.5,
            pitch=1.1,
            pitch_variation=0.1
        ),
        tags=["typewriter", "office", "mechanical"],
        variants=4
    ),

    # Horror
    SoundID.HEARTBEAT: SoundDefinition(
        id=SoundID.HEARTBEAT,
        name="Heartbeat",
        category=SoundCategory.HORROR,
        generator_type="heartbeat",
        duration_ms=1000,
        properties=SoundProperties(volume=0.6),
        tags=["heartbeat", "tension", "horror"],
        variants=1
    ),
    SoundID.WHISPER: SoundDefinition(
        id=SoundID.WHISPER,
        name="Whisper",
        category=SoundCategory.HORROR,
        generator_type="whisper",
        duration_ms=1500,
        properties=SoundProperties(volume=0.4),
        tags=["whisper", "voice", "horror", "mystery"],
        variants=3
    ),
    SoundID.CREAK_FLOOR: SoundDefinition(
        id=SoundID.CREAK_FLOOR,
        name="Floor Creak",
        category=SoundCategory.HORROR,
        generator_type="creak",
        duration_ms=600,
        properties=SoundProperties(volume=0.5, pitch=0.8),
        tags=["creak", "floor", "horror"],
        variants=4
    ),
    SoundID.DRIP_WATER: SoundDefinition(
        id=SoundID.DRIP_WATER,
        name="Water Drip",
        category=SoundCategory.AMBIENCE,
        generator_type="drip",
        duration_ms=300,
        properties=SoundProperties(volume=0.4),
        tags=["drip", "water", "ambient"],
        variants=5
    ),

    # UI
    SoundID.UI_CLICK: SoundDefinition(
        id=SoundID.UI_CLICK,
        name="UI Click",
        category=SoundCategory.UI,
        generator_type="click",
        duration_ms=50,
        properties=SoundProperties(volume=0.5, pitch=1.5),
        tags=["ui", "click", "interface"],
        variants=1
    ),
    SoundID.UI_SELECT: SoundDefinition(
        id=SoundID.UI_SELECT,
        name="UI Select",
        category=SoundCategory.UI,
        generator_type="tone",
        duration_ms=100,
        properties=SoundProperties(volume=0.4, pitch=1.2),
        tags=["ui", "select", "interface"],
        variants=1
    ),
    SoundID.UI_ERROR: SoundDefinition(
        id=SoundID.UI_ERROR,
        name="UI Error",
        category=SoundCategory.UI,
        generator_type="tone",
        duration_ms=200,
        properties=SoundProperties(volume=0.6, pitch=0.5),
        tags=["ui", "error", "interface"],
        variants=1
    ),

    # Stings
    SoundID.STING_TENSION: SoundDefinition(
        id=SoundID.STING_TENSION,
        name="Tension Sting",
        category=SoundCategory.MUSIC,
        generator_type="tone",
        duration_ms=2000,
        properties=SoundProperties(volume=0.7),
        tags=["sting", "music", "tension"],
        variants=2
    ),
    SoundID.STING_DANGER: SoundDefinition(
        id=SoundID.STING_DANGER,
        name="Danger Sting",
        category=SoundCategory.MUSIC,
        generator_type="tone",
        duration_ms=500,
        properties=SoundProperties(volume=0.8),
        tags=["sting", "music", "danger"],
        variants=2
    ),
}


class SoundLibrary:
    """
    Manager for the sound effect library.

    Provides access to predefined sounds with caching
    and variant generation.
    """

    def __init__(self):
        self.generator = SoundGenerator()
        self._cache: Dict[str, AudioData] = {}
        self._definitions = SOUND_LIBRARY.copy()
        self._max_cache_size = 50

    def get_sound(
        self,
        sound_id: SoundID,
        variant: int = 0,
        seed: Optional[int] = None
    ) -> SoundEffect:
        """
        Get a sound effect by ID.

        Args:
            sound_id: Sound identifier
            variant: Variant number (0 to variants-1)
            seed: Random seed for generation

        Returns:
            SoundEffect instance
        """
        definition = self._definitions.get(sound_id)
        if not definition:
            raise ValueError(f"Unknown sound ID: {sound_id}")

        # Clamp variant
        variant = variant % definition.variants

        # Create effect
        effect = SoundEffect(
            id=f"{sound_id.value}_{variant}",
            name=definition.name,
            category=definition.category,
            trigger=SoundTrigger.ONESHOT,
            properties=definition.properties,
            tags=definition.tags.copy()
        )

        return effect

    def get_audio(
        self,
        sound_id: SoundID,
        variant: int = 0,
        seed: Optional[int] = None
    ) -> AudioData:
        """
        Get generated audio for a sound.

        Uses caching to avoid regenerating the same sounds.
        """
        definition = self._definitions.get(sound_id)
        if not definition:
            raise ValueError(f"Unknown sound ID: {sound_id}")

        variant = variant % definition.variants
        cache_key = f"{sound_id.value}_{variant}_{seed}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate with variant-specific seed
        gen_seed = (seed or 0) + variant * 1000
        audio = self.generator.generate(
            definition.generator_type,
            definition.duration_ms,
            gen_seed
        )

        # Cache result
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        self._cache[cache_key] = audio
        return audio

    def get_random_variant(
        self,
        sound_id: SoundID,
        seed: Optional[int] = None
    ) -> AudioData:
        """Get a random variant of a sound."""
        import random
        if seed is not None:
            random.seed(seed)

        definition = self._definitions.get(sound_id)
        if not definition:
            raise ValueError(f"Unknown sound ID: {sound_id}")

        variant = random.randint(0, definition.variants - 1)
        return self.get_audio(sound_id, variant, seed)

    def get_by_category(self, category: SoundCategory) -> List[SoundID]:
        """Get all sound IDs in a category."""
        return [
            sid for sid, defn in self._definitions.items()
            if defn.category == category
        ]

    def get_by_tag(self, tag: str) -> List[SoundID]:
        """Get all sound IDs with a specific tag."""
        return [
            sid for sid, defn in self._definitions.items()
            if tag in defn.tags
        ]

    def search(
        self,
        query: str,
        category: Optional[SoundCategory] = None
    ) -> List[SoundID]:
        """
        Search for sounds by name or tag.

        Args:
            query: Search query (matches name or tags)
            category: Optional category filter

        Returns:
            List of matching sound IDs
        """
        query_lower = query.lower()
        results = []

        for sid, defn in self._definitions.items():
            # Category filter
            if category and defn.category != category:
                continue

            # Name match
            if query_lower in defn.name.lower():
                results.append(sid)
                continue

            # Tag match
            if any(query_lower in tag for tag in defn.tags):
                results.append(sid)

        return results

    def clear_cache(self) -> None:
        """Clear the audio cache."""
        self._cache.clear()

    def add_definition(self, definition: SoundDefinition) -> None:
        """Add a custom sound definition."""
        self._definitions[definition.id] = definition

    def get_all_ids(self) -> List[SoundID]:
        """Get all available sound IDs."""
        return list(self._definitions.keys())

    def get_definition(self, sound_id: SoundID) -> Optional[SoundDefinition]:
        """Get a sound definition by ID."""
        return self._definitions.get(sound_id)
