"""
Character Voice System - TTS parameters and voice personalities.

Each character has distinct voice characteristics that persist
across all their dialogue, creating recognizable audio identities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import random


class VoiceGender(Enum):
    """Voice gender classification."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceAge(Enum):
    """Voice age range classification."""
    CHILD = "child"
    YOUNG = "young"
    ADULT = "adult"
    MIDDLE = "middle"
    ELDERLY = "elderly"


class Accent(Enum):
    """Available accent types."""
    NEUTRAL = "neutral"
    SOUTHERN = "southern"
    BRITISH = "british"
    EASTERN_EUROPEAN = "eastern_european"
    BROOKLYN = "brooklyn"
    CAJUN = "cajun"
    IRISH = "irish"
    SCOTTISH = "scottish"
    TEXAN = "texan"
    MIDWEST = "midwest"


class EmotionalState(Enum):
    """Current emotional state affecting voice."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SUSPICIOUS = "suspicious"
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    TIRED = "tired"
    EXCITED = "excited"
    SURPRISED = "surprised"


@dataclass
class VoiceParameters:
    """
    Core voice synthesis parameters.

    All values normalized to 0.0-1.0 range for portability
    across different TTS engines.
    """
    # Fundamental parameters
    pitch: float = 0.5  # 0.0 = very low, 1.0 = very high
    speed: float = 0.5  # 0.0 = very slow, 1.0 = very fast
    volume: float = 0.8  # 0.0 = silent, 1.0 = maximum

    # Texture parameters
    breathiness: float = 0.2  # 0.0 = clear, 1.0 = whisper-like
    roughness: float = 0.1  # 0.0 = smooth, 1.0 = gravelly
    nasality: float = 0.2  # 0.0 = none, 1.0 = very nasal

    # Prosody parameters
    pitch_variation: float = 0.3  # How much pitch varies during speech
    rhythm_variation: float = 0.2  # How much timing varies
    emphasis_strength: float = 0.5  # How strong word emphasis is

    # Pausing
    pause_frequency: float = 0.3  # How often pauses occur
    pause_duration: float = 0.3  # How long pauses are

    def __post_init__(self):
        """Clamp all values to valid range."""
        for attr in ['pitch', 'speed', 'volume', 'breathiness', 'roughness',
                     'nasality', 'pitch_variation', 'rhythm_variation',
                     'emphasis_strength', 'pause_frequency', 'pause_duration']:
            value = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, value)))

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'pitch': self.pitch,
            'speed': self.speed,
            'volume': self.volume,
            'breathiness': self.breathiness,
            'roughness': self.roughness,
            'nasality': self.nasality,
            'pitch_variation': self.pitch_variation,
            'rhythm_variation': self.rhythm_variation,
            'emphasis_strength': self.emphasis_strength,
            'pause_frequency': self.pause_frequency,
            'pause_duration': self.pause_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'VoiceParameters':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})

    def blend(self, other: 'VoiceParameters', factor: float) -> 'VoiceParameters':
        """
        Blend with another voice parameters set.

        Args:
            other: Parameters to blend with
            factor: 0.0 = all self, 1.0 = all other
        """
        factor = max(0.0, min(1.0, factor))
        result = {}
        for attr in ['pitch', 'speed', 'volume', 'breathiness', 'roughness',
                     'nasality', 'pitch_variation', 'rhythm_variation',
                     'emphasis_strength', 'pause_frequency', 'pause_duration']:
            self_val = getattr(self, attr)
            other_val = getattr(other, attr)
            result[attr] = self_val * (1 - factor) + other_val * factor
        return VoiceParameters(**result)


@dataclass
class CharacterVoice:
    """
    Complete voice profile for a character.

    Combines base parameters with identity traits and
    supports emotional modulation.
    """
    # Identity
    character_id: str
    name: str

    # Classification
    gender: VoiceGender = VoiceGender.NEUTRAL
    age: VoiceAge = VoiceAge.ADULT
    accent: Accent = Accent.NEUTRAL

    # Base parameters (neutral emotional state)
    base_params: VoiceParameters = field(default_factory=VoiceParameters)

    # Current emotional state
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    emotion_intensity: float = 0.5  # How strongly emotion affects voice

    # Character-specific quirks
    speech_quirks: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)

    def get_effective_params(self) -> VoiceParameters:
        """
        Get voice parameters with emotional modulation applied.

        Returns parameters adjusted for current emotional state.
        """
        # Start with base
        params = VoiceParameters(**self.base_params.to_dict())

        # Apply emotional modulation
        modulation = EMOTION_MODULATIONS.get(self.emotional_state, {})
        intensity = self.emotion_intensity

        for attr, modifier in modulation.items():
            if hasattr(params, attr):
                base_val = getattr(params, attr)
                # Apply modifier scaled by intensity
                new_val = base_val + (modifier * intensity)
                setattr(params, attr, max(0.0, min(1.0, new_val)))

        return params

    def set_emotion(self, state: EmotionalState, intensity: float = 0.5) -> None:
        """Update emotional state."""
        self.emotional_state = state
        self.emotion_intensity = max(0.0, min(1.0, intensity))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'character_id': self.character_id,
            'name': self.name,
            'gender': self.gender.value,
            'age': self.age.value,
            'accent': self.accent.value,
            'base_params': self.base_params.to_dict(),
            'emotional_state': self.emotional_state.value,
            'emotion_intensity': self.emotion_intensity,
            'speech_quirks': self.speech_quirks,
            'catchphrases': self.catchphrases
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterVoice':
        """Deserialize from dictionary."""
        return cls(
            character_id=data['character_id'],
            name=data['name'],
            gender=VoiceGender(data.get('gender', 'neutral')),
            age=VoiceAge(data.get('age', 'adult')),
            accent=Accent(data.get('accent', 'neutral')),
            base_params=VoiceParameters.from_dict(data.get('base_params', {})),
            emotional_state=EmotionalState(data.get('emotional_state', 'neutral')),
            emotion_intensity=data.get('emotion_intensity', 0.5),
            speech_quirks=data.get('speech_quirks', []),
            catchphrases=data.get('catchphrases', [])
        )


# Emotional modulation values (additive adjustments)
EMOTION_MODULATIONS: Dict[EmotionalState, Dict[str, float]] = {
    EmotionalState.NEUTRAL: {},
    EmotionalState.HAPPY: {
        'pitch': 0.1,
        'speed': 0.1,
        'pitch_variation': 0.15,
        'emphasis_strength': 0.1
    },
    EmotionalState.SAD: {
        'pitch': -0.1,
        'speed': -0.15,
        'breathiness': 0.15,
        'pitch_variation': -0.1,
        'pause_frequency': 0.2,
        'pause_duration': 0.2
    },
    EmotionalState.ANGRY: {
        'pitch': 0.05,
        'speed': 0.15,
        'roughness': 0.2,
        'emphasis_strength': 0.3,
        'pitch_variation': 0.2
    },
    EmotionalState.FEARFUL: {
        'pitch': 0.15,
        'speed': 0.2,
        'breathiness': 0.2,
        'pitch_variation': 0.25,
        'rhythm_variation': 0.2
    },
    EmotionalState.SUSPICIOUS: {
        'speed': -0.1,
        'pitch_variation': -0.1,
        'pause_frequency': 0.15,
        'emphasis_strength': 0.1
    },
    EmotionalState.CONFIDENT: {
        'pitch': -0.05,
        'speed': 0.05,
        'roughness': 0.05,
        'emphasis_strength': 0.2,
        'pitch_variation': 0.1
    },
    EmotionalState.NERVOUS: {
        'pitch': 0.1,
        'speed': 0.15,
        'breathiness': 0.15,
        'rhythm_variation': 0.25,
        'pitch_variation': 0.2
    },
    EmotionalState.TIRED: {
        'pitch': -0.1,
        'speed': -0.2,
        'breathiness': 0.2,
        'emphasis_strength': -0.2,
        'pause_frequency': 0.25,
        'pause_duration': 0.15
    },
    EmotionalState.EXCITED: {
        'pitch': 0.15,
        'speed': 0.2,
        'pitch_variation': 0.3,
        'emphasis_strength': 0.2,
        'rhythm_variation': 0.15
    }
}


class VoiceFactory:
    """Factory for generating character voices."""

    @staticmethod
    def create_from_archetype(
        character_id: str,
        name: str,
        archetype: str,
        seed: Optional[int] = None
    ) -> CharacterVoice:
        """
        Generate a voice profile from character archetype.

        Args:
            character_id: Unique character identifier
            name: Character display name
            archetype: Character archetype (detective, femme_fatale, etc.)
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        # Get archetype template
        template = ARCHETYPE_VOICE_TEMPLATES.get(
            archetype.lower(),
            ARCHETYPE_VOICE_TEMPLATES['default']
        )

        # Create base parameters with variation
        base = VoiceParameters(
            pitch=template['pitch'] + random.uniform(-0.1, 0.1),
            speed=template['speed'] + random.uniform(-0.1, 0.1),
            breathiness=template['breathiness'] + random.uniform(-0.05, 0.05),
            roughness=template['roughness'] + random.uniform(-0.05, 0.05),
            nasality=template.get('nasality', 0.2) + random.uniform(-0.05, 0.05),
            pitch_variation=template.get('pitch_variation', 0.3) + random.uniform(-0.1, 0.1),
            rhythm_variation=template.get('rhythm_variation', 0.2) + random.uniform(-0.1, 0.1),
            emphasis_strength=template.get('emphasis_strength', 0.5) + random.uniform(-0.1, 0.1)
        )

        return CharacterVoice(
            character_id=character_id,
            name=name,
            gender=VoiceGender(template.get('gender', 'neutral')),
            age=VoiceAge(template.get('age', 'adult')),
            accent=Accent(template.get('accent', 'neutral')),
            base_params=base,
            speech_quirks=template.get('quirks', []).copy(),
            catchphrases=template.get('catchphrases', []).copy()
        )

    @staticmethod
    def create_random(
        character_id: str,
        name: str,
        seed: Optional[int] = None
    ) -> CharacterVoice:
        """Generate a completely random voice profile."""
        if seed is not None:
            random.seed(seed)

        return CharacterVoice(
            character_id=character_id,
            name=name,
            gender=random.choice(list(VoiceGender)),
            age=random.choice(list(VoiceAge)),
            accent=random.choice(list(Accent)),
            base_params=VoiceParameters(
                pitch=random.uniform(0.2, 0.8),
                speed=random.uniform(0.3, 0.7),
                breathiness=random.uniform(0.0, 0.4),
                roughness=random.uniform(0.0, 0.4),
                nasality=random.uniform(0.1, 0.4),
                pitch_variation=random.uniform(0.1, 0.5),
                rhythm_variation=random.uniform(0.1, 0.4),
                emphasis_strength=random.uniform(0.3, 0.7)
            )
        )


# Archetype voice templates
ARCHETYPE_VOICE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    'default': {
        'gender': 'neutral',
        'age': 'adult',
        'accent': 'neutral',
        'pitch': 0.5,
        'speed': 0.5,
        'breathiness': 0.2,
        'roughness': 0.1
    },
    'detective': {
        'gender': 'male',
        'age': 'middle',
        'accent': 'neutral',
        'pitch': 0.35,
        'speed': 0.45,
        'breathiness': 0.15,
        'roughness': 0.25,
        'emphasis_strength': 0.6,
        'quirks': ['occasional_sigh', 'thoughtful_pause'],
        'catchphrases': ["Something doesn't add up...", "Let me think about this."]
    },
    'femme_fatale': {
        'gender': 'female',
        'age': 'young',
        'accent': 'neutral',
        'pitch': 0.55,
        'speed': 0.4,
        'breathiness': 0.35,
        'roughness': 0.05,
        'pitch_variation': 0.35,
        'quirks': ['seductive_pause', 'lowered_voice'],
        'catchphrases': ["Darling...", "How... interesting."]
    },
    'gangster': {
        'gender': 'male',
        'age': 'adult',
        'accent': 'brooklyn',
        'pitch': 0.3,
        'speed': 0.5,
        'breathiness': 0.1,
        'roughness': 0.35,
        'emphasis_strength': 0.7,
        'quirks': ['threatening_tone', 'abrupt_pauses'],
        'catchphrases': ["You understand me?", "We got a problem here."]
    },
    'informant': {
        'gender': 'male',
        'age': 'adult',
        'accent': 'neutral',
        'pitch': 0.5,
        'speed': 0.65,
        'breathiness': 0.25,
        'roughness': 0.1,
        'rhythm_variation': 0.35,
        'quirks': ['nervous_stutter', 'looking_around'],
        'catchphrases': ["Look, I shouldn't be telling you this...", "You didn't hear this from me."]
    },
    'bartender': {
        'gender': 'male',
        'age': 'middle',
        'accent': 'irish',
        'pitch': 0.4,
        'speed': 0.45,
        'breathiness': 0.15,
        'roughness': 0.2,
        'pitch_variation': 0.4,
        'quirks': ['friendly_tone', 'knowing_chuckle'],
        'catchphrases': ["What'll it be?", "I've seen a lot in my time..."]
    },
    'politician': {
        'gender': 'male',
        'age': 'middle',
        'accent': 'neutral',
        'pitch': 0.45,
        'speed': 0.4,
        'breathiness': 0.1,
        'roughness': 0.05,
        'emphasis_strength': 0.65,
        'pitch_variation': 0.35,
        'quirks': ['measured_speech', 'diplomatic_pause'],
        'catchphrases': ["Let me be clear...", "The people of this city..."]
    },
    'elderly_witness': {
        'gender': 'female',
        'age': 'elderly',
        'accent': 'neutral',
        'pitch': 0.6,
        'speed': 0.35,
        'breathiness': 0.3,
        'roughness': 0.15,
        'pause_frequency': 0.45,
        'pause_duration': 0.4,
        'quirks': ['rambling', 'memory_gaps'],
        'catchphrases': ["In my day...", "Now let me think..."]
    },
    'street_kid': {
        'gender': 'neutral',
        'age': 'young',
        'accent': 'brooklyn',
        'pitch': 0.6,
        'speed': 0.7,
        'breathiness': 0.15,
        'roughness': 0.1,
        'rhythm_variation': 0.4,
        'quirks': ['slang', 'defiant_tone'],
        'catchphrases': ["Whatever, man.", "You ain't from around here."]
    },
    'corrupt_cop': {
        'gender': 'male',
        'age': 'adult',
        'accent': 'neutral',
        'pitch': 0.35,
        'speed': 0.5,
        'breathiness': 0.1,
        'roughness': 0.25,
        'emphasis_strength': 0.55,
        'quirks': ['authoritative', 'dismissive'],
        'catchphrases': ["Move along.", "This doesn't concern you."]
    },
    'nightclub_singer': {
        'gender': 'female',
        'age': 'young',
        'accent': 'neutral',
        'pitch': 0.5,
        'speed': 0.4,
        'breathiness': 0.4,
        'roughness': 0.05,
        'pitch_variation': 0.45,
        'emphasis_strength': 0.6,
        'quirks': ['melodic_speech', 'dramatic_pause'],
        'catchphrases': ["Honey...", "You should have seen this place in its heyday."]
    }
}


# =============================================================================
# Voice Profile System (for TTS integration)
# =============================================================================

@dataclass
class VoiceProfile:
    """
    Voice profile for TTS synthesis.

    Contains parameters that define how a character's voice sounds
    when synthesized by a TTS engine.
    """
    voice_id: str
    base_voice: str = "default"
    name: str = "Unnamed Voice"

    # Pitch and speed modifiers (-1.0 to 1.0)
    pitch: float = 0.0
    speed: float = 0.0

    # Voice texture modifiers (0.0 to 1.0)
    roughness: float = 0.0
    breathiness: float = 0.0
    resonance: float = 0.5

    # Age modifier (-1.0 = younger, 1.0 = older)
    age_modifier: float = 0.0

    # Emotion modulation strength
    emotion_strength: float = 0.5

    def get_pitch_multiplier(self) -> float:
        """Get pitch multiplier for TTS (0.5 to 2.0 range)."""
        # Convert -1.0 to 1.0 range to 0.5 to 2.0 multiplier
        return 1.0 + (self.pitch * 0.5)

    def get_speed_multiplier(self) -> float:
        """Get speed multiplier for TTS (0.5 to 2.0 range)."""
        # Convert -1.0 to 1.0 range to 0.5 to 2.0 multiplier
        return 1.0 + (self.speed * 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'voice_id': self.voice_id,
            'base_voice': self.base_voice,
            'name': self.name,
            'pitch': self.pitch,
            'speed': self.speed,
            'roughness': self.roughness,
            'breathiness': self.breathiness,
            'resonance': self.resonance,
            'age_modifier': self.age_modifier,
            'emotion_strength': self.emotion_strength,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceProfile':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Aliases for backwards compatibility
VoiceParameter = VoiceParameters
EMOTION_MODIFIERS = EMOTION_MODULATIONS


class VoiceModulator:
    """
    Modulates voice parameters based on emotional state and context.

    Provides dynamic voice variation for more natural-sounding speech.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize modulator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self._seed = seed
        self._variation_amount = 0.1

    def modulate(self, profile: VoiceProfile, emotion: EmotionalState,
                 intensity: float = 0.5) -> VoiceProfile:
        """
        Apply emotional modulation to a voice profile.

        Args:
            profile: Base voice profile
            emotion: Emotional state to apply
            intensity: How strongly to apply the emotion (0.0 to 1.0)

        Returns:
            New VoiceProfile with modulation applied
        """
        modulation = EMOTION_MODULATIONS.get(emotion, {})

        new_pitch = profile.pitch
        new_speed = profile.speed

        if 'pitch' in modulation:
            new_pitch += modulation['pitch'] * intensity * profile.emotion_strength
        if 'speed' in modulation:
            new_speed += modulation['speed'] * intensity * profile.emotion_strength

        # Add small random variation for naturalness
        new_pitch += random.uniform(-self._variation_amount, self._variation_amount) * 0.5
        new_speed += random.uniform(-self._variation_amount, self._variation_amount) * 0.5

        # Clamp values
        new_pitch = max(-1.0, min(1.0, new_pitch))
        new_speed = max(-1.0, min(1.0, new_speed))

        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=new_pitch,
            speed=new_speed,
            roughness=profile.roughness + modulation.get('roughness', 0.0) * intensity,
            breathiness=profile.breathiness + modulation.get('breathiness', 0.0) * intensity,
            resonance=profile.resonance,
            age_modifier=profile.age_modifier,
            emotion_strength=profile.emotion_strength,
        )

    def add_variation(self, profile: VoiceProfile, amount: float = 0.1) -> VoiceProfile:
        """Add random variation to a voice profile."""
        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch + random.uniform(-amount, amount),
            speed=profile.speed + random.uniform(-amount, amount),
            roughness=max(0.0, min(1.0, profile.roughness + random.uniform(-amount, amount))),
            breathiness=max(0.0, min(1.0, profile.breathiness + random.uniform(-amount, amount))),
            resonance=profile.resonance,
            age_modifier=profile.age_modifier,
            emotion_strength=profile.emotion_strength,
        )

    def apply_whisper(self, profile: VoiceProfile, intensity: float = 0.5) -> VoiceProfile:
        """Apply whisper effect to a voice profile.

        Args:
            profile: Voice profile to modify
            intensity: How strongly to apply the whisper effect (0.0 to 1.0)

        Returns:
            New VoiceProfile with whisper characteristics
        """
        intensity = max(0.0, min(1.0, intensity))

        return VoiceProfile(
            voice_id=profile.voice_id,
            base_voice=profile.base_voice,
            name=profile.name,
            pitch=profile.pitch + (0.1 * intensity),  # Slightly higher pitch
            speed=profile.speed - (0.2 * intensity),  # Slower
            roughness=max(0.0, profile.roughness - (0.3 * intensity)),  # Less rough
            breathiness=min(1.0, profile.breathiness + (0.6 * intensity)),  # Much more breathy
            resonance=profile.resonance - (0.2 * intensity),  # Less resonant
            age_modifier=profile.age_modifier,
            emotion_strength=profile.emotion_strength * (1.0 - 0.3 * intensity),  # Reduced emotion
        )


class VoiceLibrary:
    """
    Library of voice profiles and character voice assignments.

    Manages voice presets and character-specific voice configurations.
    """

    # Built-in voice presets
    PRESETS: Dict[str, Dict[str, Any]] = {
        'detective': {
            'base_voice': 'male_1',
            'pitch': -0.2,
            'speed': -0.1,
            'roughness': 0.3,
            'breathiness': 0.1,
            'resonance': 0.4,
            'age_modifier': 0.2,
        },
        'femme_fatale': {
            'base_voice': 'female_1',
            'pitch': 0.1,
            'speed': -0.15,
            'roughness': 0.0,
            'breathiness': 0.4,
            'resonance': 0.6,
            'age_modifier': -0.1,
        },
        'gangster': {
            'base_voice': 'male_2',
            'pitch': -0.3,
            'speed': 0.1,
            'roughness': 0.5,
            'breathiness': 0.0,
            'resonance': 0.3,
            'age_modifier': 0.1,
        },
        'informant': {
            'base_voice': 'male_1',
            'pitch': 0.1,
            'speed': 0.2,
            'roughness': 0.1,
            'breathiness': 0.2,
            'resonance': 0.5,
            'age_modifier': 0.0,
        },
        'elderly': {
            'base_voice': 'female_2',
            'pitch': 0.2,
            'speed': -0.3,
            'roughness': 0.2,
            'breathiness': 0.3,
            'resonance': 0.4,
            'age_modifier': 0.5,
        },
        'default': {
            'base_voice': 'default',
            'pitch': 0.0,
            'speed': 0.0,
            'roughness': 0.0,
            'breathiness': 0.0,
            'resonance': 0.5,
            'age_modifier': 0.0,
        },
    }

    def __init__(self):
        """Initialize voice library."""
        self._profiles: Dict[str, VoiceProfile] = {}
        self._character_voices: Dict[str, 'CharacterVoiceTTS'] = {}
        self._modulator = VoiceModulator()

    def get_preset(self, preset_name: str) -> Optional[VoiceProfile]:
        """Get a voice profile from presets."""
        preset = self.PRESETS.get(preset_name.lower())
        if preset is None:
            return None

        return VoiceProfile(
            voice_id=preset_name,
            name=preset_name.replace('_', ' ').title(),
            **preset
        )

    def register_profile(self, profile: VoiceProfile) -> None:
        """Register a custom voice profile."""
        self._profiles[profile.voice_id] = profile

    def get_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get a voice profile by ID."""
        return self._profiles.get(voice_id) or self.get_preset(voice_id)

    def generate_random_profile(self, voice_id: Optional[str] = None, seed: Optional[int] = None) -> VoiceProfile:
        """Generate a random voice profile.

        Args:
            voice_id: Optional ID for the voice profile
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        vid = voice_id or f"random_{random.randint(1000, 9999)}"

        base_voices = ['male_1', 'male_2', 'female_1', 'female_2', 'default']

        return VoiceProfile(
            voice_id=vid,
            base_voice=random.choice(base_voices),
            name=f"Voice {vid}",
            pitch=random.uniform(-0.5, 0.5),
            speed=random.uniform(-0.3, 0.3),
            roughness=random.uniform(0.0, 0.5),
            breathiness=random.uniform(0.0, 0.4),
            resonance=random.uniform(0.3, 0.7),
            age_modifier=random.uniform(-0.3, 0.3),
        )

    def create_character_voice(self, character_id: str,
                               profile: VoiceProfile) -> 'CharacterVoiceTTS':
        """Create and register a character voice."""
        char_voice = CharacterVoiceTTS(
            character_id=character_id,
            profile=profile,
        )
        self._character_voices[character_id] = char_voice
        return char_voice

    def get_character_voice(self, character_id: str) -> Optional['CharacterVoiceTTS']:
        """Get a character's voice configuration."""
        return self._character_voices.get(character_id)

    def list_presets(self) -> List[str]:
        """List available preset names."""
        return list(self.PRESETS.keys())

    def list_characters(self) -> List[str]:
        """List registered character IDs."""
        return list(self._character_voices.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'profiles': {k: v.to_dict() for k, v in self._profiles.items()},
            'character_voices': {
                k: v.to_dict() for k, v in self._character_voices.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceLibrary':
        """Create from dictionary."""
        library = cls()

        for profile_data in data.get('profiles', {}).values():
            profile = VoiceProfile.from_dict(profile_data)
            library.register_profile(profile)

        for char_data in data.get('character_voices', {}).values():
            char_voice = CharacterVoiceTTS.from_dict(char_data)
            library._character_voices[char_voice.character_id] = char_voice

        return library


@dataclass
class CharacterVoiceTTS:
    """
    Character voice configuration for TTS synthesis.

    Links a character to their voice profile and manages
    emotional state for voice modulation.
    """
    character_id: str
    profile: VoiceProfile
    current_emotion: EmotionalState = EmotionalState.NEUTRAL
    emotion_intensity: float = 0.5

    def set_emotion(self, emotion: EmotionalState, intensity: float = 0.5) -> None:
        """Set current emotional state."""
        self.current_emotion = emotion
        self.emotion_intensity = max(0.0, min(1.0, intensity))

    def get_effective_profile(self) -> VoiceProfile:
        """Get voice profile with emotional modulation applied."""
        modulator = VoiceModulator()
        return modulator.modulate(self.profile, self.current_emotion, self.emotion_intensity)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'character_id': self.character_id,
            'profile': self.profile.to_dict(),
            'current_emotion': self.current_emotion.value,
            'emotion_intensity': self.emotion_intensity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterVoiceTTS':
        """Create from dictionary."""
        return cls(
            character_id=data['character_id'],
            profile=VoiceProfile.from_dict(data['profile']),
            current_emotion=EmotionalState(data.get('current_emotion', 'neutral')),
            emotion_intensity=data.get('emotion_intensity', 0.5),
        )
