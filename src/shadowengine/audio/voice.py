"""
Voice Personality System for ShadowEngine.

Provides character voice customization, emotional states,
and voice modulation for distinct character voices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any
import random
import math


class EmotionalState(Enum):
    """Emotional states that affect voice."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    CONTEMPTUOUS = "contemptuous"
    NERVOUS = "nervous"
    CONFIDENT = "confident"
    TIRED = "tired"
    EXCITED = "excited"


@dataclass
class VoiceParameter:
    """A single voice parameter with range and current value."""

    name: str
    value: float
    min_value: float = -1.0
    max_value: float = 1.0
    default: float = 0.0

    def __post_init__(self):
        """Clamp value to valid range."""
        self.value = max(self.min_value, min(self.max_value, self.value))

    def normalize(self) -> float:
        """Get normalized value (0.0 to 1.0)."""
        range_size = self.max_value - self.min_value
        if range_size == 0:
            return 0.5
        return (self.value - self.min_value) / range_size

    def apply_modifier(self, modifier: float) -> float:
        """Apply a modifier and return new value."""
        new_value = self.value + modifier
        return max(self.min_value, min(self.max_value, new_value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "default": self.default,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceParameter':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class VoiceProfile:
    """Voice profile defining character's vocal characteristics."""

    # Identity
    voice_id: str
    base_voice: str = "default"
    name: str = ""

    # Core parameters (-1.0 to 1.0)
    pitch: float = 0.0          # Low to high
    speed: float = 0.0          # Slow to fast
    breathiness: float = 0.0    # Clear to breathy
    roughness: float = 0.0      # Smooth to rough
    resonance: float = 0.0      # Thin to full

    # Age modifier (-1.0 young to 1.0 old)
    age_modifier: float = 0.0

    # Optional accent/dialect
    accent: Optional[str] = None

    # Emotional baseline
    baseline_emotion: EmotionalState = EmotionalState.NEUTRAL
    emotional_range: float = 0.5  # How much emotions affect voice

    # Quirks
    stutter_frequency: float = 0.0
    pause_frequency: float = 0.0
    filler_frequency: float = 0.0  # "um", "uh", etc.

    def get_pitch_multiplier(self) -> float:
        """Get pitch multiplier (0.5 to 2.0)."""
        return 1.0 + (self.pitch * 0.5)

    def get_speed_multiplier(self) -> float:
        """Get speed multiplier (0.5 to 2.0)."""
        return 1.0 + (self.speed * 0.5)

    def get_parameters(self) -> Dict[str, VoiceParameter]:
        """Get all voice parameters."""
        return {
            "pitch": VoiceParameter("pitch", self.pitch),
            "speed": VoiceParameter("speed", self.speed),
            "breathiness": VoiceParameter("breathiness", self.breathiness, 0.0, 1.0, 0.0),
            "roughness": VoiceParameter("roughness", self.roughness, 0.0, 1.0, 0.0),
            "resonance": VoiceParameter("resonance", self.resonance),
            "age_modifier": VoiceParameter("age_modifier", self.age_modifier),
        }

    def apply_emotion(self, emotion: EmotionalState) -> 'VoiceProfile':
        """Create a modified profile based on emotional state."""
        # Create a copy with emotional modifications
        modifiers = EMOTION_MODIFIERS.get(emotion, {})
        return VoiceProfile(
            voice_id=self.voice_id,
            base_voice=self.base_voice,
            name=self.name,
            pitch=self._apply_range(self.pitch + modifiers.get("pitch", 0) * self.emotional_range),
            speed=self._apply_range(self.speed + modifiers.get("speed", 0) * self.emotional_range),
            breathiness=max(0, min(1, self.breathiness + modifiers.get("breathiness", 0) * self.emotional_range)),
            roughness=max(0, min(1, self.roughness + modifiers.get("roughness", 0) * self.emotional_range)),
            resonance=self._apply_range(self.resonance + modifiers.get("resonance", 0) * self.emotional_range),
            age_modifier=self.age_modifier,
            accent=self.accent,
            baseline_emotion=emotion,
            emotional_range=self.emotional_range,
        )

    def _apply_range(self, value: float) -> float:
        """Clamp value to -1.0 to 1.0."""
        return max(-1.0, min(1.0, value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "voice_id": self.voice_id,
            "base_voice": self.base_voice,
            "name": self.name,
            "pitch": self.pitch,
            "speed": self.speed,
            "breathiness": self.breathiness,
            "roughness": self.roughness,
            "resonance": self.resonance,
            "age_modifier": self.age_modifier,
            "accent": self.accent,
            "baseline_emotion": self.baseline_emotion.value,
            "emotional_range": self.emotional_range,
            "stutter_frequency": self.stutter_frequency,
            "pause_frequency": self.pause_frequency,
            "filler_frequency": self.filler_frequency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceProfile':
        """Create from dictionary."""
        data = data.copy()
        if "baseline_emotion" in data:
            data["baseline_emotion"] = EmotionalState(data["baseline_emotion"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Emotion modifiers for voice parameters
EMOTION_MODIFIERS = {
    EmotionalState.HAPPY: {"pitch": 0.2, "speed": 0.15, "breathiness": -0.1},
    EmotionalState.SAD: {"pitch": -0.2, "speed": -0.2, "breathiness": 0.2},
    EmotionalState.ANGRY: {"pitch": 0.1, "speed": 0.2, "roughness": 0.3, "resonance": 0.2},
    EmotionalState.FEARFUL: {"pitch": 0.3, "speed": 0.3, "breathiness": 0.3},
    EmotionalState.SURPRISED: {"pitch": 0.4, "speed": 0.1},
    EmotionalState.DISGUSTED: {"pitch": -0.1, "speed": -0.1, "roughness": 0.2},
    EmotionalState.CONTEMPTUOUS: {"pitch": -0.15, "speed": -0.15},
    EmotionalState.NERVOUS: {"pitch": 0.15, "speed": 0.25, "breathiness": 0.2},
    EmotionalState.CONFIDENT: {"pitch": -0.1, "speed": -0.05, "resonance": 0.2},
    EmotionalState.TIRED: {"pitch": -0.15, "speed": -0.25, "breathiness": 0.3},
    EmotionalState.EXCITED: {"pitch": 0.3, "speed": 0.35},
    EmotionalState.NEUTRAL: {},
}


@dataclass
class CharacterVoice:
    """Complete voice configuration for a character."""

    character_id: str
    profile: VoiceProfile
    current_emotion: EmotionalState = EmotionalState.NEUTRAL

    # Speech patterns
    vocabulary_complexity: float = 0.5  # 0=simple, 1=complex
    formality: float = 0.5              # 0=casual, 1=formal
    verbosity: float = 0.5              # 0=terse, 1=verbose

    # Dynamic state
    stress_level: float = 0.0
    fatigue_level: float = 0.0

    def get_effective_profile(self) -> VoiceProfile:
        """Get voice profile with current emotional state applied."""
        profile = self.profile.apply_emotion(self.current_emotion)

        # Apply stress and fatigue
        if self.stress_level > 0:
            profile.pitch += 0.2 * self.stress_level
            profile.speed += 0.15 * self.stress_level

        if self.fatigue_level > 0:
            profile.speed -= 0.2 * self.fatigue_level
            profile.breathiness += 0.2 * self.fatigue_level

        return profile

    def set_emotion(self, emotion: EmotionalState) -> None:
        """Set current emotional state."""
        self.current_emotion = emotion

    def apply_stress(self, amount: float) -> None:
        """Apply stress to character voice."""
        self.stress_level = max(0.0, min(1.0, self.stress_level + amount))

    def apply_fatigue(self, amount: float) -> None:
        """Apply fatigue to character voice."""
        self.fatigue_level = max(0.0, min(1.0, self.fatigue_level + amount))

    def recover(self, amount: float = 0.1) -> None:
        """Recover from stress and fatigue."""
        self.stress_level = max(0.0, self.stress_level - amount)
        self.fatigue_level = max(0.0, self.fatigue_level - amount)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character_id": self.character_id,
            "profile": self.profile.to_dict(),
            "current_emotion": self.current_emotion.value,
            "vocabulary_complexity": self.vocabulary_complexity,
            "formality": self.formality,
            "verbosity": self.verbosity,
            "stress_level": self.stress_level,
            "fatigue_level": self.fatigue_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterVoice':
        """Create from dictionary."""
        data = data.copy()
        data["profile"] = VoiceProfile.from_dict(data["profile"])
        data["current_emotion"] = EmotionalState(data["current_emotion"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class VoiceModulator:
    """Modulates voice parameters based on context."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def add_natural_variation(self, profile: VoiceProfile, amount: float = 0.1) -> VoiceProfile:
        """Add natural micro-variations to voice."""
        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch + self._rng.uniform(-amount, amount),
            speed=profile.speed + self._rng.uniform(-amount, amount),
            breathiness=max(0, profile.breathiness + self._rng.uniform(-amount/2, amount/2)),
            roughness=max(0, profile.roughness + self._rng.uniform(-amount/2, amount/2)),
            resonance=profile.resonance + self._rng.uniform(-amount, amount),
            age_modifier=profile.age_modifier,
            accent=profile.accent,
            baseline_emotion=profile.baseline_emotion,
            emotional_range=profile.emotional_range,
        )

    def apply_whisper(self, profile: VoiceProfile) -> VoiceProfile:
        """Apply whisper effect to voice."""
        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch + 0.2,
            speed=profile.speed - 0.1,
            breathiness=1.0,  # Maximum breathiness for whisper
            roughness=0.0,
            resonance=profile.resonance - 0.3,
            age_modifier=profile.age_modifier,
            accent=profile.accent,
            baseline_emotion=profile.baseline_emotion,
            emotional_range=profile.emotional_range,
        )

    def apply_shout(self, profile: VoiceProfile) -> VoiceProfile:
        """Apply shout effect to voice."""
        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch + 0.3,
            speed=profile.speed + 0.1,
            breathiness=0.0,
            roughness=min(1.0, profile.roughness + 0.4),
            resonance=profile.resonance + 0.3,
            age_modifier=profile.age_modifier,
            accent=profile.accent,
            baseline_emotion=profile.baseline_emotion,
            emotional_range=profile.emotional_range,
        )

    def age_voice(self, profile: VoiceProfile, years: int) -> VoiceProfile:
        """Age or de-age a voice by years."""
        age_factor = years / 50.0  # Normalize to -1 to 1 range
        age_factor = max(-1.0, min(1.0, age_factor))

        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch - age_factor * 0.3,  # Lower with age
            speed=profile.speed - age_factor * 0.2,  # Slower with age
            breathiness=max(0, profile.breathiness + age_factor * 0.2),
            roughness=max(0, profile.roughness + age_factor * 0.15),
            resonance=profile.resonance + age_factor * 0.1,
            age_modifier=profile.age_modifier + age_factor,
            accent=profile.accent,
            baseline_emotion=profile.baseline_emotion,
            emotional_range=max(0.2, profile.emotional_range - abs(age_factor) * 0.2),
        )


class VoiceLibrary:
    """Library of voice profiles for characters."""

    def __init__(self):
        self._profiles: Dict[str, VoiceProfile] = {}
        self._character_voices: Dict[str, CharacterVoice] = {}
        self._presets: Dict[str, VoiceProfile] = self._create_presets()

    def _create_presets(self) -> Dict[str, VoiceProfile]:
        """Create preset voice profiles."""
        return {
            "gruff_male": VoiceProfile(
                voice_id="gruff_male",
                base_voice="male_1",
                name="Gruff Male",
                pitch=-0.3,
                speed=-0.1,
                roughness=0.5,
                resonance=0.3,
                age_modifier=0.3,
            ),
            "young_female": VoiceProfile(
                voice_id="young_female",
                base_voice="female_1",
                name="Young Female",
                pitch=0.3,
                speed=0.15,
                breathiness=0.2,
                age_modifier=-0.4,
            ),
            "elderly_male": VoiceProfile(
                voice_id="elderly_male",
                base_voice="male_2",
                name="Elderly Male",
                pitch=-0.4,
                speed=-0.3,
                roughness=0.3,
                breathiness=0.25,
                age_modifier=0.7,
            ),
            "nervous_female": VoiceProfile(
                voice_id="nervous_female",
                base_voice="female_2",
                name="Nervous Female",
                pitch=0.2,
                speed=0.2,
                breathiness=0.3,
                baseline_emotion=EmotionalState.NERVOUS,
            ),
            "confident_male": VoiceProfile(
                voice_id="confident_male",
                base_voice="male_1",
                name="Confident Male",
                pitch=-0.15,
                speed=0.0,
                resonance=0.4,
                baseline_emotion=EmotionalState.CONFIDENT,
            ),
            "child": VoiceProfile(
                voice_id="child",
                base_voice="child",
                name="Child",
                pitch=0.5,
                speed=0.2,
                resonance=-0.2,
                age_modifier=-0.8,
            ),
            "raspy_elder": VoiceProfile(
                voice_id="raspy_elder",
                base_voice="elder",
                name="Raspy Elder",
                pitch=-0.5,
                speed=-0.4,
                roughness=0.7,
                breathiness=0.4,
                age_modifier=0.9,
            ),
            "femme_fatale": VoiceProfile(
                voice_id="femme_fatale",
                base_voice="female_1",
                name="Femme Fatale",
                pitch=0.0,
                speed=-0.15,
                breathiness=0.35,
                resonance=0.2,
            ),
        }

    def get_preset(self, preset_name: str) -> Optional[VoiceProfile]:
        """Get a preset voice profile."""
        return self._presets.get(preset_name)

    def get_preset_names(self) -> List[str]:
        """Get all preset names."""
        return list(self._presets.keys())

    def register_profile(self, profile: VoiceProfile) -> None:
        """Register a custom voice profile."""
        self._profiles[profile.voice_id] = profile

    def get_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get a voice profile by ID."""
        return self._profiles.get(voice_id) or self._presets.get(voice_id)

    def create_character_voice(self, character_id: str, profile: VoiceProfile) -> CharacterVoice:
        """Create a character voice from a profile."""
        voice = CharacterVoice(
            character_id=character_id,
            profile=profile,
        )
        self._character_voices[character_id] = voice
        return voice

    def get_character_voice(self, character_id: str) -> Optional[CharacterVoice]:
        """Get a character's voice."""
        return self._character_voices.get(character_id)

    def generate_random_profile(self, seed: Optional[int] = None,
                                gender: Optional[str] = None) -> VoiceProfile:
        """Generate a random voice profile."""
        rng = random.Random(seed)

        base_voices = {
            "male": ["male_1", "male_2"],
            "female": ["female_1", "female_2"],
            None: ["male_1", "male_2", "female_1", "female_2"],
        }

        return VoiceProfile(
            voice_id=f"random_{seed or rng.randint(0, 10000)}",
            base_voice=rng.choice(base_voices.get(gender, base_voices[None])),
            name=f"Random Voice {seed}",
            pitch=rng.uniform(-0.5, 0.5),
            speed=rng.uniform(-0.3, 0.3),
            breathiness=rng.uniform(0, 0.4),
            roughness=rng.uniform(0, 0.4),
            resonance=rng.uniform(-0.3, 0.3),
            age_modifier=rng.uniform(-0.5, 0.5),
            emotional_range=rng.uniform(0.3, 0.8),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert library to dictionary."""
        return {
            "profiles": {k: v.to_dict() for k, v in self._profiles.items()},
            "character_voices": {k: v.to_dict() for k, v in self._character_voices.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceLibrary':
        """Create library from dictionary."""
        library = cls()
        for voice_id, profile_data in data.get("profiles", {}).items():
            library.register_profile(VoiceProfile.from_dict(profile_data))
        for char_id, voice_data in data.get("character_voices", {}).items():
            library._character_voices[char_id] = CharacterVoice.from_dict(voice_data)
        return library
