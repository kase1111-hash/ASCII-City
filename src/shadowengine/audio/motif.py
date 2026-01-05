"""
Motif Generator for ShadowEngine.

Provides procedural music and theme generation including motifs,
chords, rhythms, and tension-mapped audio themes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any, Tuple
import random
import math


class MusicalKey(Enum):
    """Musical keys."""
    C_MAJOR = "C_major"
    C_MINOR = "C_minor"
    D_MAJOR = "D_major"
    D_MINOR = "D_minor"
    E_MAJOR = "E_major"
    E_MINOR = "E_minor"
    F_MAJOR = "F_major"
    F_MINOR = "F_minor"
    G_MAJOR = "G_major"
    G_MINOR = "G_minor"
    A_MAJOR = "A_major"
    A_MINOR = "A_minor"
    B_MAJOR = "B_major"
    B_MINOR = "B_minor"


class TimeSignature(Enum):
    """Time signatures."""
    FOUR_FOUR = (4, 4)
    THREE_FOUR = (3, 4)
    SIX_EIGHT = (6, 8)
    TWO_FOUR = (2, 4)
    FIVE_FOUR = (5, 4)
    SEVEN_EIGHT = (7, 8)


class MotifType(Enum):
    """Types of musical motifs."""
    MELODIC = "melodic"         # Main melody theme
    RHYTHMIC = "rhythmic"       # Rhythm-focused pattern
    HARMONIC = "harmonic"       # Chord progression
    BASS = "bass"               # Bass line
    AMBIENT = "ambient"         # Atmospheric texture
    PERCUSSIVE = "percussive"   # Percussion pattern
    TENSION = "tension"         # Building tension
    RESOLUTION = "resolution"   # Resolving tension


# Note frequencies (A4 = 440Hz)
NOTE_FREQUENCIES = {
    "C": [32.70, 65.41, 130.81, 261.63, 523.25, 1046.50, 2093.00],
    "C#": [34.65, 69.30, 138.59, 277.18, 554.37, 1108.73, 2217.46],
    "D": [36.71, 73.42, 146.83, 293.66, 587.33, 1174.66, 2349.32],
    "D#": [38.89, 77.78, 155.56, 311.13, 622.25, 1244.51, 2489.02],
    "E": [41.20, 82.41, 164.81, 329.63, 659.25, 1318.51, 2637.02],
    "F": [43.65, 87.31, 174.61, 349.23, 698.46, 1396.91, 2793.83],
    "F#": [46.25, 92.50, 185.00, 369.99, 739.99, 1479.98, 2959.96],
    "G": [49.00, 98.00, 196.00, 392.00, 783.99, 1567.98, 3135.96],
    "G#": [51.91, 103.83, 207.65, 415.30, 830.61, 1661.22, 3322.44],
    "A": [55.00, 110.00, 220.00, 440.00, 880.00, 1760.00, 3520.00],
    "A#": [58.27, 116.54, 233.08, 466.16, 932.33, 1864.66, 3729.31],
    "B": [61.74, 123.47, 246.94, 493.88, 987.77, 1975.53, 3951.07],
}

# Scale patterns (semitone intervals)
SCALE_PATTERNS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
}


@dataclass
class Note:
    """A musical note."""

    pitch: str              # Note name (C, D, E, etc.)
    octave: int = 4         # Octave number
    duration: float = 1.0   # Duration in beats
    velocity: float = 0.8   # Volume/intensity (0.0 to 1.0)
    articulation: str = "normal"  # normal, staccato, legato, accent

    @property
    def frequency(self) -> float:
        """Get frequency in Hz."""
        base_pitch = self.pitch.replace("#", "").replace("b", "")
        if base_pitch in NOTE_FREQUENCIES:
            # Octave 1 maps to index 0, octave 4 maps to index 3, etc.
            index = max(0, min(self.octave - 1, 6))
            return NOTE_FREQUENCIES[base_pitch][index]
        return 440.0  # Default to A4

    @property
    def midi_note(self) -> int:
        """Get MIDI note number."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        pitch = self.pitch.replace("Db", "C#").replace("Eb", "D#").replace("Gb", "F#").replace("Ab", "G#").replace("Bb", "A#")
        if pitch in note_names:
            return (self.octave + 1) * 12 + note_names.index(pitch)
        return 60  # Middle C

    def transpose(self, semitones: int) -> 'Note':
        """Transpose note by semitones."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        current_midi = self.midi_note
        new_midi = current_midi + semitones
        new_octave = (new_midi // 12) - 1
        new_pitch = note_names[new_midi % 12]
        return Note(new_pitch, new_octave, self.duration, self.velocity, self.articulation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pitch": self.pitch,
            "octave": self.octave,
            "duration": self.duration,
            "velocity": self.velocity,
            "articulation": self.articulation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Chord:
    """A musical chord."""

    root: str               # Root note
    quality: str = "major"  # major, minor, dim, aug, 7, maj7, min7, etc.
    octave: int = 4
    duration: float = 4.0   # Duration in beats
    velocity: float = 0.7
    inversion: int = 0      # 0=root, 1=first, 2=second inversion

    # Chord intervals from root
    CHORD_INTERVALS = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "dim": [0, 3, 6],
        "aug": [0, 4, 8],
        "7": [0, 4, 7, 10],
        "maj7": [0, 4, 7, 11],
        "min7": [0, 3, 7, 10],
        "dim7": [0, 3, 6, 9],
        "sus2": [0, 2, 7],
        "sus4": [0, 5, 7],
        "add9": [0, 4, 7, 14],
        "6": [0, 4, 7, 9],
        "min6": [0, 3, 7, 9],
    }

    @property
    def notes(self) -> List[Note]:
        """Get notes in the chord."""
        intervals = self.CHORD_INTERVALS.get(self.quality, [0, 4, 7])
        root_note = Note(self.root, self.octave)

        notes = []
        for i, interval in enumerate(intervals):
            note = root_note.transpose(interval)
            note.duration = self.duration
            note.velocity = self.velocity
            notes.append(note)

        # Apply inversion
        if self.inversion > 0:
            for i in range(min(self.inversion, len(notes))):
                notes[i] = notes[i].transpose(12)  # Move up an octave

        return notes

    @property
    def name(self) -> str:
        """Get chord name."""
        quality_names = {
            "major": "",
            "minor": "m",
            "dim": "dim",
            "aug": "aug",
            "7": "7",
            "maj7": "maj7",
            "min7": "m7",
        }
        return f"{self.root}{quality_names.get(self.quality, self.quality)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root": self.root,
            "quality": self.quality,
            "octave": self.octave,
            "duration": self.duration,
            "velocity": self.velocity,
            "inversion": self.inversion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chord':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Rhythm:
    """A rhythmic pattern."""

    pattern: List[float]        # List of beat divisions (1.0 = quarter note)
    accents: List[float] = field(default_factory=list)  # Accent levels per beat
    time_signature: TimeSignature = TimeSignature.FOUR_FOUR
    tempo: int = 120            # BPM
    swing: float = 0.0          # Swing amount (0.0 to 1.0)

    @property
    def total_beats(self) -> float:
        """Get total beats in pattern."""
        return sum(self.pattern)

    @property
    def beat_duration_ms(self) -> float:
        """Get duration of one beat in milliseconds."""
        return 60000.0 / self.tempo

    def get_note_timing(self) -> List[Tuple[float, float]]:
        """Get (start_time, duration) for each note in ms."""
        timing = []
        current_time = 0.0
        beat_ms = self.beat_duration_ms

        for i, duration in enumerate(self.pattern):
            note_duration = duration * beat_ms

            # Apply swing to off-beats
            if self.swing > 0 and i % 2 == 1:
                swing_offset = note_duration * self.swing * 0.2
                current_time += swing_offset

            timing.append((current_time, note_duration))
            current_time += note_duration

        return timing

    def apply_variation(self, amount: float = 0.1, rng: Optional[random.Random] = None) -> 'Rhythm':
        """Create a variation of this rhythm."""
        rng = rng or random.Random()

        new_pattern = []
        for duration in self.pattern:
            variation = rng.uniform(-amount, amount)
            new_pattern.append(max(0.125, duration + variation))

        return Rhythm(
            pattern=new_pattern,
            accents=self.accents.copy(),
            time_signature=self.time_signature,
            tempo=self.tempo,
            swing=self.swing,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern": self.pattern,
            "accents": self.accents,
            "time_signature": self.time_signature.value,
            "tempo": self.tempo,
            "swing": self.swing,
        }


@dataclass
class Motif:
    """A musical motif (short melodic/rhythmic idea)."""

    id: str
    motif_type: MotifType
    notes: List[Note] = field(default_factory=list)
    chords: List[Chord] = field(default_factory=list)
    rhythm: Optional[Rhythm] = None

    # Musical properties
    key: MusicalKey = MusicalKey.C_MINOR  # Noir default
    tempo: int = 80
    dynamics: str = "mf"  # pp, p, mp, mf, f, ff

    # Mood/tension
    tension_level: float = 0.5
    darkness: float = 0.6
    energy: float = 0.4

    # Metadata
    tags: List[str] = field(default_factory=list)

    @property
    def duration_beats(self) -> float:
        """Get total duration in beats."""
        note_duration = sum(n.duration for n in self.notes)
        chord_duration = sum(c.duration for c in self.chords)
        return max(note_duration, chord_duration)

    @property
    def duration_ms(self) -> float:
        """Get total duration in milliseconds."""
        beat_ms = 60000.0 / self.tempo
        return self.duration_beats * beat_ms

    def transpose(self, semitones: int) -> 'Motif':
        """Transpose the motif by semitones."""
        return Motif(
            id=f"{self.id}_transposed_{semitones}",
            motif_type=self.motif_type,
            notes=[n.transpose(semitones) for n in self.notes],
            chords=self.chords.copy(),  # Would need chord transposition
            rhythm=self.rhythm,
            key=self.key,
            tempo=self.tempo,
            dynamics=self.dynamics,
            tension_level=self.tension_level,
            darkness=self.darkness,
            energy=self.energy,
            tags=self.tags.copy(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "motif_type": self.motif_type.value,
            "notes": [n.to_dict() for n in self.notes],
            "chords": [c.to_dict() for c in self.chords],
            "rhythm": self.rhythm.to_dict() if self.rhythm else None,
            "key": self.key.value,
            "tempo": self.tempo,
            "dynamics": self.dynamics,
            "tension_level": self.tension_level,
            "darkness": self.darkness,
            "energy": self.energy,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Motif':
        """Create from dictionary."""
        data = data.copy()
        data["motif_type"] = MotifType(data["motif_type"])
        data["notes"] = [Note.from_dict(n) for n in data.get("notes", [])]
        data["chords"] = [Chord.from_dict(c) for c in data.get("chords", [])]
        data["key"] = MusicalKey(data["key"])
        if data.get("rhythm"):
            data["rhythm"] = Rhythm(**data["rhythm"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class MotifGenerator:
    """Generates musical motifs procedurally."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._seed = seed
        self._motif_counter = 0

    def set_seed(self, seed: int) -> None:
        """Set random seed."""
        self._seed = seed
        self._rng = random.Random(seed)

    def generate_melodic_motif(self, key: MusicalKey = MusicalKey.C_MINOR,
                                length: int = 4,
                                tension: float = 0.5) -> Motif:
        """Generate a melodic motif."""
        self._motif_counter += 1

        # Get scale for the key
        scale_type = "minor" if "minor" in key.value else "major"
        scale = SCALE_PATTERNS.get(scale_type, SCALE_PATTERNS["minor"])

        # Higher tension = more dissonance, wider intervals
        root = key.value.split("_")[0]
        notes = []

        # Generate notes based on tension level
        octave = 4
        prev_interval = 0

        for i in range(length):
            # Higher tension allows larger intervals
            max_interval = int(2 + tension * 4)
            interval_change = self._rng.randint(-max_interval, max_interval)
            new_interval = prev_interval + interval_change

            # Keep within scale
            scale_degree = new_interval % len(scale)
            semitones = scale[scale_degree]
            octave_offset = new_interval // len(scale)

            # Create note
            base_note = Note(root, octave + octave_offset)
            note = base_note.transpose(semitones)

            # Vary duration based on position
            if i == 0:
                note.duration = 2.0  # Longer first note
            elif i == length - 1:
                note.duration = 2.0  # Longer last note
            else:
                note.duration = self._rng.choice([0.5, 1.0, 1.0, 1.5])

            # Higher tension = more dynamic variation
            note.velocity = 0.5 + self._rng.random() * 0.3 + tension * 0.2

            notes.append(note)
            prev_interval = new_interval

        return Motif(
            id=f"melodic_{self._motif_counter}",
            motif_type=MotifType.MELODIC,
            notes=notes,
            key=key,
            tempo=70 + int(tension * 40),  # Higher tension = faster
            tension_level=tension,
            darkness=0.6 if "minor" in key.value else 0.3,
            energy=0.3 + tension * 0.4,
            tags=["melodic", scale_type],
        )

    def generate_bass_motif(self, key: MusicalKey = MusicalKey.C_MINOR,
                            length: int = 4) -> Motif:
        """Generate a bass line motif."""
        self._motif_counter += 1

        root = key.value.split("_")[0]
        scale_type = "minor" if "minor" in key.value else "major"
        scale = SCALE_PATTERNS.get(scale_type, SCALE_PATTERNS["minor"])

        notes = []
        octave = 2  # Bass register

        # Bass patterns typically use root, 5th, and octave
        bass_degrees = [0, 4, 2, 4]  # Common bass pattern

        for i in range(length):
            degree = bass_degrees[i % len(bass_degrees)]
            semitones = scale[degree % len(scale)]

            base_note = Note(root, octave)
            note = base_note.transpose(semitones)
            note.duration = 1.0
            note.velocity = 0.7 + (0.2 if i == 0 else 0.0)  # Accent first beat

            notes.append(note)

        return Motif(
            id=f"bass_{self._motif_counter}",
            motif_type=MotifType.BASS,
            notes=notes,
            key=key,
            tempo=80,
            tension_level=0.4,
            darkness=0.7,
            energy=0.5,
            tags=["bass", "foundation"],
        )

    def generate_chord_progression(self, key: MusicalKey = MusicalKey.C_MINOR,
                                     length: int = 4,
                                     tension: float = 0.5) -> Motif:
        """Generate a chord progression motif."""
        self._motif_counter += 1

        root = key.value.split("_")[0]
        is_minor = "minor" in key.value

        # Common chord progressions
        if is_minor:
            progressions = [
                ["minor", "major", "major", "minor"],  # i-VI-VII-i
                ["minor", "dim", "major", "minor"],    # i-ii°-VII-i
                ["minor", "minor", "major", "major"],  # i-iv-VI-VII
            ]
        else:
            progressions = [
                ["major", "minor", "minor", "major"],  # I-ii-vi-IV
                ["major", "major", "minor", "major"],  # I-IV-vi-V
            ]

        progression = self._rng.choice(progressions)

        # Noir typically uses more 7th chords for tension
        chords = []
        scale = SCALE_PATTERNS.get("minor" if is_minor else "major")
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        root_idx = note_names.index(root)

        for i, quality in enumerate(progression[:length]):
            # Calculate chord root from scale degree
            if i == 0:
                chord_root = root
            else:
                degree = [0, 5, 6, 4][i % 4]  # Common degrees
                semitones = scale[degree % len(scale)]
                chord_root = note_names[(root_idx + semitones) % 12]

            # Add 7ths based on tension
            if tension > 0.5 and self._rng.random() < tension:
                if quality == "minor":
                    quality = "min7"
                elif quality == "major":
                    quality = self._rng.choice(["maj7", "7"])

            chord = Chord(
                root=chord_root,
                quality=quality,
                octave=3,
                duration=4.0,
                velocity=0.6 + tension * 0.2,
            )
            chords.append(chord)

        return Motif(
            id=f"chords_{self._motif_counter}",
            motif_type=MotifType.HARMONIC,
            chords=chords,
            key=key,
            tempo=70,
            tension_level=tension,
            darkness=0.7 if is_minor else 0.4,
            energy=0.3,
            tags=["harmonic", "chords", "minor" if is_minor else "major"],
        )

    def generate_tension_motif(self, base_tension: float = 0.5) -> Motif:
        """Generate a tension-building motif."""
        self._motif_counter += 1

        # Tension motifs use dissonance and rhythmic intensity
        notes = []

        # Use chromatic movement for tension
        for i in range(8):
            note = Note(
                pitch=["C", "C#", "D", "D#", "E", "F", "F#", "G"][i],
                octave=4,
                duration=0.5 - (i * 0.03),  # Accelerating
                velocity=0.5 + (i * 0.06),  # Building
            )
            notes.append(note)

        return Motif(
            id=f"tension_{self._motif_counter}",
            motif_type=MotifType.TENSION,
            notes=notes,
            key=MusicalKey.C_MINOR,
            tempo=90 + int(base_tension * 40),
            tension_level=min(1.0, base_tension + 0.3),
            darkness=0.8,
            energy=0.6 + base_tension * 0.3,
            tags=["tension", "building", "dramatic"],
        )

    def generate_ambient_motif(self, darkness: float = 0.5) -> Motif:
        """Generate an ambient texture motif."""
        self._motif_counter += 1

        # Ambient uses sustained notes and pads
        chords = []

        if darkness > 0.5:
            # Darker ambient - minor 7ths, suspensions
            chord_types = ["min7", "sus2", "minor"]
        else:
            # Lighter ambient - major 7ths, add9
            chord_types = ["maj7", "add9", "major"]

        for i in range(2):
            chord = Chord(
                root=self._rng.choice(["C", "D", "F", "G"]),
                quality=self._rng.choice(chord_types),
                octave=3,
                duration=8.0,  # Long sustained chords
                velocity=0.4,  # Soft
            )
            chords.append(chord)

        return Motif(
            id=f"ambient_{self._motif_counter}",
            motif_type=MotifType.AMBIENT,
            chords=chords,
            key=MusicalKey.C_MINOR if darkness > 0.5 else MusicalKey.C_MAJOR,
            tempo=60,
            tension_level=0.3,
            darkness=darkness,
            energy=0.2,
            tags=["ambient", "texture", "atmospheric"],
        )


class TensionMapper:
    """Maps game tension to musical parameters."""

    def __init__(self):
        self._current_tension = 0.0
        self._target_tension = 0.0
        self._transition_speed = 0.1

    @property
    def tension(self) -> float:
        """Get current tension level."""
        return self._current_tension

    def set_tension(self, tension: float, immediate: bool = False) -> None:
        """Set target tension level."""
        self._target_tension = max(0.0, min(1.0, tension))
        if immediate:
            self._current_tension = self._target_tension

    def update(self, dt: float) -> float:
        """Update tension towards target. Returns new tension."""
        if self._current_tension < self._target_tension:
            self._current_tension = min(
                self._target_tension,
                self._current_tension + self._transition_speed * dt
            )
        elif self._current_tension > self._target_tension:
            self._current_tension = max(
                self._target_tension,
                self._current_tension - self._transition_speed * dt
            )
        return self._current_tension

    def get_tempo_modifier(self) -> float:
        """Get tempo modifier based on tension."""
        return 1.0 + (self._current_tension * 0.3)  # Up to 30% faster

    def get_dynamics_modifier(self) -> float:
        """Get dynamics modifier based on tension."""
        return 0.5 + (self._current_tension * 0.5)  # 0.5 to 1.0

    def get_suggested_key(self) -> MusicalKey:
        """Get suggested key based on tension."""
        if self._current_tension > 0.7:
            return MusicalKey.C_MINOR
        elif self._current_tension > 0.4:
            return self._current_tension > 0.5 and MusicalKey.D_MINOR or MusicalKey.A_MINOR
        else:
            return MusicalKey.G_MAJOR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_tension": self._current_tension,
            "target_tension": self._target_tension,
            "transition_speed": self._transition_speed,
        }


class ThemeEngine:
    """Engine for generating and managing musical themes."""

    def __init__(self, seed: Optional[int] = None):
        self._generator = MotifGenerator(seed)
        self._tension_mapper = TensionMapper()
        self._active_motifs: Dict[str, Motif] = {}
        self._themes: Dict[str, List[Motif]] = {}

    @property
    def tension(self) -> float:
        """Get current tension level."""
        return self._tension_mapper.tension

    def set_tension(self, tension: float, immediate: bool = False) -> None:
        """Set tension level."""
        self._tension_mapper.set_tension(tension, immediate)

    def update(self, dt: float) -> None:
        """Update theme engine."""
        self._tension_mapper.update(dt)

    def generate_theme(self, theme_id: str, mood: str = "noir") -> List[Motif]:
        """Generate a complete theme with multiple motifs."""
        tension = self._tension_mapper.tension
        key = self._tension_mapper.get_suggested_key()

        motifs = []

        # Generate base components
        if mood == "noir":
            # Noir: dark, jazzy, mysterious
            motifs.append(self._generator.generate_melodic_motif(
                key=MusicalKey.C_MINOR,
                length=4,
                tension=tension,
            ))
            motifs.append(self._generator.generate_bass_motif(
                key=MusicalKey.C_MINOR,
            ))
            motifs.append(self._generator.generate_chord_progression(
                key=MusicalKey.C_MINOR,
                tension=tension,
            ))

        elif mood == "tense":
            # Tense: building, dramatic
            motifs.append(self._generator.generate_tension_motif(tension))
            motifs.append(self._generator.generate_chord_progression(
                key=MusicalKey.D_MINOR,
                tension=0.8,
            ))

        elif mood == "ambient":
            # Ambient: atmospheric, subtle
            motifs.append(self._generator.generate_ambient_motif(darkness=0.5 + tension * 0.3))

        elif mood == "action":
            # Action: energetic, driving
            motifs.append(self._generator.generate_melodic_motif(
                key=MusicalKey.E_MINOR,
                length=8,
                tension=0.7,
            ))
            motifs.append(self._generator.generate_bass_motif(
                key=MusicalKey.E_MINOR,
                length=8,
            ))

        self._themes[theme_id] = motifs
        return motifs

    def get_theme(self, theme_id: str) -> Optional[List[Motif]]:
        """Get a previously generated theme."""
        return self._themes.get(theme_id)

    def get_active_motifs(self) -> Dict[str, Motif]:
        """Get currently active motifs."""
        return self._active_motifs.copy()

    def activate_motif(self, motif: Motif) -> None:
        """Activate a motif for playback."""
        self._active_motifs[motif.id] = motif

    def deactivate_motif(self, motif_id: str) -> None:
        """Deactivate a motif."""
        self._active_motifs.pop(motif_id, None)

    def clear_active(self) -> None:
        """Clear all active motifs."""
        self._active_motifs.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tension_mapper": self._tension_mapper.to_dict(),
            "active_motifs": {k: v.to_dict() for k, v in self._active_motifs.items()},
            "themes": {k: [m.to_dict() for m in v] for k, v in self._themes.items()},
        }
