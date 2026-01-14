"""
Theme Pack System for ShadowEngine.

Theme packs allow customization of the game's genre, vocabulary,
atmosphere, and visual style. A theme pack can transform the
noir detective game into cyberpunk, fantasy, horror, or any
other genre.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json


@dataclass
class VocabularyConfig:
    """
    Vocabulary customization for a theme.

    Allows themes to replace standard verbs with genre-appropriate
    alternatives (e.g., "examine" -> "scan" for cyberpunk).
    """

    # Action verbs
    examine_verbs: List[str] = field(default_factory=lambda: ["examine", "look", "inspect"])
    talk_verbs: List[str] = field(default_factory=lambda: ["talk", "speak", "ask"])
    take_verbs: List[str] = field(default_factory=lambda: ["take", "grab", "pick up"])
    use_verbs: List[str] = field(default_factory=lambda: ["use", "apply", "employ"])
    go_verbs: List[str] = field(default_factory=lambda: ["go", "walk", "move"])
    attack_verbs: List[str] = field(default_factory=lambda: ["attack", "hit", "strike"])

    # Descriptor vocabulary
    dark_words: List[str] = field(default_factory=lambda: ["dark", "shadowy", "gloomy"])
    light_words: List[str] = field(default_factory=lambda: ["bright", "lit", "illuminated"])
    danger_words: List[str] = field(default_factory=lambda: ["dangerous", "threatening", "hostile"])
    safe_words: List[str] = field(default_factory=lambda: ["safe", "secure", "protected"])

    # Character descriptions
    suspicious_words: List[str] = field(default_factory=lambda: ["suspicious", "shifty", "nervous"])
    trustworthy_words: List[str] = field(default_factory=lambda: ["trustworthy", "reliable", "honest"])

    # Custom vocabulary (genre-specific)
    custom_terms: Dict[str, List[str]] = field(default_factory=dict)

    def get_verb(self, verb_type: str, index: int = 0) -> str:
        """Get a verb by type and index."""
        verbs = getattr(self, f"{verb_type}_verbs", None)
        if verbs and index < len(verbs):
            return verbs[index]
        return verb_type

    def get_random_verb(self, verb_type: str, rng=None) -> str:
        """Get a random verb of the given type."""
        import random
        rng = rng or random
        verbs = getattr(self, f"{verb_type}_verbs", [verb_type])
        return rng.choice(verbs) if verbs else verb_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "examine_verbs": self.examine_verbs,
            "talk_verbs": self.talk_verbs,
            "take_verbs": self.take_verbs,
            "use_verbs": self.use_verbs,
            "go_verbs": self.go_verbs,
            "attack_verbs": self.attack_verbs,
            "dark_words": self.dark_words,
            "light_words": self.light_words,
            "danger_words": self.danger_words,
            "safe_words": self.safe_words,
            "suspicious_words": self.suspicious_words,
            "trustworthy_words": self.trustworthy_words,
            "custom_terms": self.custom_terms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VocabularyConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WeatherConfig:
    """
    Weather system configuration for a theme.

    Defines available weather types and their probabilities.
    """

    # Weather type weights (probability distribution)
    weather_weights: Dict[str, float] = field(default_factory=lambda: {
        "clear": 0.4,
        "cloudy": 0.2,
        "rain": 0.2,
        "fog": 0.1,
        "storm": 0.1,
    })

    # Custom weather types for the theme
    custom_weather: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Weather effect descriptions
    weather_descriptions: Dict[str, str] = field(default_factory=lambda: {
        "clear": "The sky is clear.",
        "cloudy": "Clouds hang overhead.",
        "rain": "Rain falls steadily.",
        "fog": "Thick fog obscures your vision.",
        "storm": "Thunder rumbles as lightning flashes.",
    })

    # Weather effects on gameplay
    weather_visibility_modifiers: Dict[str, float] = field(default_factory=lambda: {
        "clear": 1.0,
        "cloudy": 0.9,
        "rain": 0.7,
        "fog": 0.4,
        "storm": 0.5,
    })

    def get_weather_probability(self, weather_type: str) -> float:
        """Get probability of a weather type."""
        return self.weather_weights.get(weather_type, 0.0)

    def get_description(self, weather_type: str) -> str:
        """Get description for a weather type."""
        return self.weather_descriptions.get(weather_type, f"The weather is {weather_type}.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "weather_weights": self.weather_weights,
            "custom_weather": self.custom_weather,
            "weather_descriptions": self.weather_descriptions,
            "weather_visibility_modifiers": self.weather_visibility_modifiers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AtmosphereConfig:
    """
    Atmosphere and visual style configuration.

    Controls colors, tension levels, and visual effects.
    """

    # Color palette (ANSI color names or hex codes)
    primary_color: str = "white"
    secondary_color: str = "cyan"
    danger_color: str = "red"
    safe_color: str = "green"
    highlight_color: str = "yellow"
    background_color: str = "black"

    # Tension-based color mapping
    tension_colors: Dict[str, str] = field(default_factory=lambda: {
        "low": "cyan",
        "medium": "yellow",
        "high": "red",
    })

    # Particle effects
    particle_effects: Dict[str, bool] = field(default_factory=lambda: {
        "rain": True,
        "snow": False,
        "fog": True,
        "sparks": False,
    })

    # Sound atmosphere (for audio module integration)
    ambient_sounds: List[str] = field(default_factory=lambda: [
        "city_night",
        "rain_light",
        "traffic_distant",
    ])

    # Musical themes
    musical_key: str = "C_minor"  # Noir default
    tempo_base: int = 80

    # Visual effects intensity
    effect_intensity: float = 0.7

    def get_tension_color(self, tension: float) -> str:
        """Get color for tension level (0.0-1.0)."""
        if tension < 0.33:
            return self.tension_colors.get("low", self.primary_color)
        elif tension < 0.66:
            return self.tension_colors.get("medium", self.secondary_color)
        else:
            return self.tension_colors.get("high", self.danger_color)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "danger_color": self.danger_color,
            "safe_color": self.safe_color,
            "highlight_color": self.highlight_color,
            "background_color": self.background_color,
            "tension_colors": self.tension_colors,
            "particle_effects": self.particle_effects,
            "ambient_sounds": self.ambient_sounds,
            "musical_key": self.musical_key,
            "tempo_base": self.tempo_base,
            "effect_intensity": self.effect_intensity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AtmosphereConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ThemeConfig:
    """
    Core theme configuration combining all aspects.
    """

    # Time periods for the theme
    time_periods: Dict[str, tuple] = field(default_factory=lambda: {
        "dawn": (5, 7),
        "morning": (7, 12),
        "afternoon": (12, 17),
        "evening": (17, 20),
        "night": (20, 5),
    })

    # Location types for the theme
    location_types: List[str] = field(default_factory=lambda: [
        "office", "street", "bar", "alley", "warehouse", "apartment",
    ])

    # Default character names pool
    character_names: Dict[str, List[str]] = field(default_factory=lambda: {
        "male": ["Jack", "Sam", "Mike", "Frank", "Tony"],
        "female": ["Mary", "Jane", "Rose", "Vera", "Lila"],
        "neutral": ["Alex", "Jordan", "Riley", "Morgan", "Casey"],
    })

    # Item/evidence types
    item_types: List[str] = field(default_factory=lambda: [
        "document", "weapon", "key", "photograph", "letter",
    ])

    # Conflict types available in theme
    conflict_types: List[str] = field(default_factory=lambda: [
        "murder", "theft", "betrayal", "conspiracy", "disappearance",
    ])

    # Narration style
    narration_style: str = "noir"  # noir, pulp, procedural, gothic

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "time_periods": {k: list(v) for k, v in self.time_periods.items()},
            "location_types": self.location_types,
            "character_names": self.character_names,
            "item_types": self.item_types,
            "conflict_types": self.conflict_types,
            "narration_style": self.narration_style,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeConfig':
        """Create from dictionary."""
        data = data.copy()
        if "time_periods" in data:
            data["time_periods"] = {
                k: tuple(v) for k, v in data["time_periods"].items()
            }
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ThemePack:
    """
    Complete theme pack for genre customization.

    A theme pack bundles together all the configuration needed
    to transform the game into a specific genre (e.g., cyberpunk,
    fantasy, horror).
    """

    # Identity
    id: str
    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""

    # Configuration components
    vocabulary: VocabularyConfig = field(default_factory=VocabularyConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    atmosphere: AtmosphereConfig = field(default_factory=AtmosphereConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)

    # Custom archetypes for this theme
    archetypes: List[str] = field(default_factory=list)

    # Custom conflict types
    conflicts: List[str] = field(default_factory=list)

    # ASCII art templates
    art_templates: Dict[str, List[str]] = field(default_factory=dict)

    # Custom dialogue responses
    dialogue_templates: Dict[str, List[str]] = field(default_factory=dict)

    # Location templates
    location_templates: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    preview_art: Optional[List[str]] = None
    credits: List[str] = field(default_factory=list)

    def get_vocabulary(self) -> VocabularyConfig:
        """Get vocabulary configuration."""
        return self.vocabulary

    def get_weather(self) -> WeatherConfig:
        """Get weather configuration."""
        return self.weather

    def get_atmosphere(self) -> AtmosphereConfig:
        """Get atmosphere configuration."""
        return self.atmosphere

    def get_theme(self) -> ThemeConfig:
        """Get theme configuration."""
        return self.theme

    def has_custom_archetypes(self) -> bool:
        """Check if theme has custom archetypes."""
        return len(self.archetypes) > 0

    def has_custom_conflicts(self) -> bool:
        """Check if theme has custom conflicts."""
        return len(self.conflicts) > 0

    def get_location_template(self, location_type: str) -> Optional[Dict[str, Any]]:
        """Get a location template by type."""
        return self.location_templates.get(location_type)

    def get_art_template(self, template_id: str) -> Optional[List[str]]:
        """Get an ASCII art template by ID."""
        return self.art_templates.get(template_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "vocabulary": self.vocabulary.to_dict(),
            "weather": self.weather.to_dict(),
            "atmosphere": self.atmosphere.to_dict(),
            "theme": self.theme.to_dict(),
            "archetypes": self.archetypes,
            "conflicts": self.conflicts,
            "art_templates": self.art_templates,
            "dialogue_templates": self.dialogue_templates,
            "location_templates": self.location_templates,
            "tags": self.tags,
            "preview_art": self.preview_art,
            "credits": self.credits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemePack':
        """Create from dictionary."""
        data = data.copy()

        # Convert nested configs
        if "vocabulary" in data and isinstance(data["vocabulary"], dict):
            data["vocabulary"] = VocabularyConfig.from_dict(data["vocabulary"])
        if "weather" in data and isinstance(data["weather"], dict):
            data["weather"] = WeatherConfig.from_dict(data["weather"])
        if "atmosphere" in data and isinstance(data["atmosphere"], dict):
            data["atmosphere"] = AtmosphereConfig.from_dict(data["atmosphere"])
        if "theme" in data and isinstance(data["theme"], dict):
            data["theme"] = ThemeConfig.from_dict(data["theme"])

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def load_theme_pack(file_path: str) -> ThemePack:
    """
    Load a theme pack from a JSON file.

    Args:
        file_path: Path to the theme pack file

    Returns:
        Loaded ThemePack

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Theme pack file not found: {file_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    return ThemePack.from_dict(data)


def save_theme_pack(pack: ThemePack, file_path: str) -> None:
    """
    Save a theme pack to a JSON file.

    Args:
        pack: ThemePack to save
        file_path: Path to save to
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(pack.to_dict(), f, indent=2)


def create_theme_pack(
    id: str,
    name: str,
    author: str = "Unknown",
    description: str = "",
    **kwargs
) -> ThemePack:
    """
    Create a new theme pack with defaults.

    Args:
        id: Unique identifier
        name: Display name
        author: Author name
        description: Theme description
        **kwargs: Additional configuration

    Returns:
        New ThemePack
    """
    return ThemePack(
        id=id,
        name=name,
        author=author,
        description=description,
        **kwargs
    )


# Predefined theme packs

NOIR_THEME = ThemePack(
    id="noir",
    name="Classic Noir",
    author="ShadowEngine",
    description="The default noir detective theme - dark alleys, mysterious dames, and dangerous secrets.",
    tags=["noir", "detective", "1940s"],
)

CYBERPUNK_THEME = ThemePack(
    id="cyberpunk",
    name="Neon Shadows",
    author="ShadowEngine",
    description="Cyberpunk noir - neon lights, corporate intrigue, and digital mysteries.",
    vocabulary=VocabularyConfig(
        examine_verbs=["scan", "analyze", "inspect", "probe"],
        talk_verbs=["ping", "message", "query", "contact"],
        take_verbs=["grab", "download", "acquire", "jack"],
        use_verbs=["execute", "run", "activate", "engage"],
        go_verbs=["jack in", "navigate", "route", "transit"],
        dark_words=["dim", "shadowed", "blackout", "dead"],
        light_words=["neon", "holographic", "glowing", "lit"],
        custom_terms={
            "money": ["credits", "creds", "eddies", "nuyen"],
            "computer": ["deck", "terminal", "console", "rig"],
            "gun": ["piece", "heater", "iron", "burner"],
        }
    ),
    atmosphere=AtmosphereConfig(
        primary_color="cyan",
        secondary_color="magenta",
        danger_color="red",
        highlight_color="yellow",
        tension_colors={
            "low": "cyan",
            "medium": "magenta",
            "high": "red",
        },
        ambient_sounds=["city_rain", "neon_hum", "synth_ambient"],
        musical_key="D_minor",
    ),
    theme=ThemeConfig(
        location_types=["megacorp_lobby", "neon_alley", "club", "black_clinic", "server_farm"],
        conflict_types=["data_theft", "murder", "corporate_espionage", "identity_theft"],
        narration_style="cyberpunk",
    ),
    tags=["cyberpunk", "sci-fi", "neon"],
)

GOTHIC_HORROR_THEME = ThemePack(
    id="gothic_horror",
    name="Gothic Horror",
    author="ShadowEngine",
    description="Victorian gothic horror - haunted manors, dark secrets, and supernatural terrors.",
    vocabulary=VocabularyConfig(
        examine_verbs=["scrutinize", "study", "observe", "peer at"],
        talk_verbs=["converse", "inquire", "address", "speak"],
        take_verbs=["acquire", "claim", "seize", "collect"],
        dark_words=["tenebrous", "stygian", "umbral", "lightless"],
        light_words=["luminous", "radiant", "brilliant", "gleaming"],
        danger_words=["perilous", "malevolent", "ominous", "dread"],
    ),
    atmosphere=AtmosphereConfig(
        primary_color="white",
        secondary_color="magenta",
        danger_color="red",
        tension_colors={
            "low": "blue",
            "medium": "magenta",
            "high": "red",
        },
        particle_effects={
            "fog": True,
            "rain": True,
            "snow": True,
        },
        ambient_sounds=["wind_howl", "creaking_wood", "distant_thunder"],
        musical_key="B_minor",
        tempo_base=60,
    ),
    theme=ThemeConfig(
        location_types=["manor_hall", "crypt", "garden", "library", "tower", "dungeon"],
        conflict_types=["murder", "haunting", "curse", "possession", "disappearance"],
        narration_style="gothic",
    ),
    tags=["gothic", "horror", "victorian", "supernatural"],
)

# Registry of built-in themes
BUILTIN_THEMES: Dict[str, ThemePack] = {
    "noir": NOIR_THEME,
    "cyberpunk": CYBERPUNK_THEME,
    "gothic_horror": GOTHIC_HORROR_THEME,
}


def get_builtin_theme(theme_id: str) -> Optional[ThemePack]:
    """Get a built-in theme by ID."""
    return BUILTIN_THEMES.get(theme_id)


def list_builtin_themes() -> List[str]:
    """List all built-in theme IDs."""
    return list(BUILTIN_THEMES.keys())
