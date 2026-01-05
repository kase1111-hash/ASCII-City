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
