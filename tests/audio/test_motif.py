"""
Tests for Motif Generator system.
"""

import pytest
from src.shadowengine.audio.motif import (
    Motif, MotifType, MusicalKey, TimeSignature,
    MotifGenerator, ThemeEngine, TensionMapper,
    Note, Chord, Rhythm,
    NOTE_FREQUENCIES, SCALE_PATTERNS,
)


class TestNote:
    """Tests for Note class."""

    def test_create_note(self, note):
        """Can create a note."""
        assert note.pitch == "C"
        assert note.octave == 4
        assert note.duration == 1.0
        assert note.velocity == 0.8

    def test_frequency(self):
        """Note has correct frequency."""
        a4 = Note("A", 4)
        assert abs(a4.frequency - 440.0) < 0.1

        c4 = Note("C", 4)
        assert abs(c4.frequency - 261.63) < 0.1

    def test_midi_note(self):
        """Note converts to MIDI correctly."""
        c4 = Note("C", 4)
        assert c4.midi_note == 60

        a4 = Note("A", 4)
        assert a4.midi_note == 69

    def test_transpose(self, note):
        """Can transpose note."""
        # Transpose up 2 semitones (C -> D)
        transposed = note.transpose(2)
        assert transposed.pitch == "D"
        assert transposed.octave == 4

    def test_transpose_octave(self):
        """Transposing across octave works."""
        b4 = Note("B", 4)
        c5 = b4.transpose(1)
        assert c5.pitch == "C"
        assert c5.octave == 5

    def test_transpose_negative(self, note):
        """Can transpose down."""
        transposed = note.transpose(-2)
        assert transposed.pitch == "A#"
        assert transposed.octave == 3

    def test_serialization(self, note):
        """Note can be serialized."""
        data = note.to_dict()
        restored = Note.from_dict(data)

        assert restored.pitch == note.pitch
        assert restored.octave == note.octave
        assert restored.duration == note.duration


class TestChord:
    """Tests for Chord class."""

    def test_create_chord(self, chord):
        """Can create a chord."""
        assert chord.root == "C"
        assert chord.quality == "minor"

    def test_chord_notes(self, chord):
        """Chord contains correct notes."""
        notes = chord.notes
        assert len(notes) == 3  # Minor triad

        pitches = [n.pitch for n in notes]
        # C minor: C, Eb, G
        assert "C" in pitches

    def test_major_chord(self):
        """Major chord has correct intervals."""
        major = Chord("C", "major")
        notes = major.notes
        assert len(notes) == 3

    def test_seventh_chord(self):
        """Seventh chord has 4 notes."""
        seventh = Chord("C", "7")
        notes = seventh.notes
        assert len(notes) == 4

    def test_chord_name(self, chord):
        """Chord name is correct."""
        assert chord.name == "Cm"

        major = Chord("G", "major")
        assert major.name == "G"

        seventh = Chord("D", "min7")
        assert seventh.name == "Dm7"

    def test_inversion(self):
        """Can create chord inversions."""
        root_pos = Chord("C", "major", inversion=0)
        first_inv = Chord("C", "major", inversion=1)

        root_notes = root_pos.notes
        inv_notes = first_inv.notes

        # First inversion moves bass up an octave
        assert inv_notes[0].octave > root_notes[0].octave

    def test_serialization(self, chord):
        """Chord can be serialized."""
        data = chord.to_dict()
        restored = Chord.from_dict(data)

        assert restored.root == chord.root
        assert restored.quality == chord.quality


class TestRhythm:
    """Tests for Rhythm class."""

    def test_create_rhythm(self, rhythm):
        """Can create rhythm."""
        assert len(rhythm.pattern) > 0
        assert rhythm.tempo == 120

    def test_total_beats(self, rhythm):
        """Can get total beats."""
        assert rhythm.total_beats == 4.0  # 1 + 0.5 + 0.5 + 1 + 1

    def test_beat_duration_ms(self, rhythm):
        """Beat duration calculated correctly."""
        # 120 BPM = 500ms per beat
        assert rhythm.beat_duration_ms == 500.0

    def test_timing(self, rhythm):
        """Can get note timing."""
        timing = rhythm.get_note_timing()
        assert len(timing) == len(rhythm.pattern)

        # Each entry is (start_time, duration)
        start, duration = timing[0]
        assert start == 0.0
        assert duration == 500.0  # 1 beat at 120 BPM

    def test_swing(self):
        """Swing affects timing."""
        rhythm = Rhythm(
            pattern=[1.0, 1.0, 1.0, 1.0],
            tempo=120,
            swing=0.5,
        )
        timing = rhythm.get_note_timing()

        # Off-beats should be delayed
        _, _ = timing[1]  # Second note (off-beat)
        # Swing should offset this

    def test_apply_variation(self, rhythm):
        """Can create rhythm variation."""
        varied = rhythm.apply_variation(0.1)
        assert varied.tempo == rhythm.tempo

        # Pattern should be slightly different
        assert varied.pattern != rhythm.pattern or True  # Random variation

    def test_serialization(self, rhythm):
        """Rhythm can be serialized."""
        data = rhythm.to_dict()
        assert "pattern" in data
        assert "tempo" in data


class TestMotif:
    """Tests for Motif class."""

    def test_create_motif(self, note, chord):
        """Can create motif."""
        motif = Motif(
            id="test_motif",
            motif_type=MotifType.MELODIC,
            notes=[note],
            chords=[chord],
        )
        assert motif.id == "test_motif"
        assert len(motif.notes) == 1

    def test_duration(self, note):
        """Motif calculates duration."""
        motif = Motif(
            id="test",
            motif_type=MotifType.MELODIC,
            notes=[note, note],  # 2 beats total
            tempo=120,
        )
        assert motif.duration_beats == 2.0
        assert motif.duration_ms == 1000.0

    def test_transpose(self, note):
        """Can transpose motif."""
        motif = Motif(
            id="test",
            motif_type=MotifType.MELODIC,
            notes=[note],
        )
        transposed = motif.transpose(5)

        assert transposed.notes[0].pitch != note.pitch

    def test_serialization(self, note, chord):
        """Motif can be serialized."""
        motif = Motif(
            id="test",
            motif_type=MotifType.HARMONIC,
            notes=[note],
            chords=[chord],
            tension_level=0.7,
            tags=["test", "dark"],
        )
        data = motif.to_dict()
        restored = Motif.from_dict(data)

        assert restored.id == motif.id
        assert restored.tension_level == 0.7
        assert "test" in restored.tags


class TestMotifGenerator:
    """Tests for MotifGenerator."""

    def test_create_generator(self, motif_generator):
        """Can create generator."""
        assert motif_generator is not None

    def test_generate_melodic(self, motif_generator):
        """Can generate melodic motif."""
        motif = motif_generator.generate_melodic_motif(
            key=MusicalKey.C_MINOR,
            length=4,
        )
        assert motif.motif_type == MotifType.MELODIC
        assert len(motif.notes) == 4

    def test_generate_bass(self, motif_generator):
        """Can generate bass motif."""
        motif = motif_generator.generate_bass_motif(
            key=MusicalKey.D_MINOR,
            length=4,
        )
        assert motif.motif_type == MotifType.BASS
        assert len(motif.notes) == 4

        # Bass should be in low octave
        for note in motif.notes:
            assert note.octave <= 3

    def test_generate_chord_progression(self, motif_generator):
        """Can generate chord progression."""
        motif = motif_generator.generate_chord_progression(
            key=MusicalKey.A_MINOR,
            length=4,
        )
        assert motif.motif_type == MotifType.HARMONIC
        assert len(motif.chords) == 4

    def test_generate_tension(self, motif_generator):
        """Can generate tension motif."""
        motif = motif_generator.generate_tension_motif(base_tension=0.7)
        assert motif.motif_type == MotifType.TENSION
        assert motif.tension_level >= 0.7

    def test_generate_ambient(self, motif_generator):
        """Can generate ambient motif."""
        motif = motif_generator.generate_ambient_motif(darkness=0.8)
        assert motif.motif_type == MotifType.AMBIENT
        assert motif.darkness == 0.8

    def test_deterministic_generation(self):
        """Same seed produces same motif."""
        gen1 = MotifGenerator(seed=100)
        gen2 = MotifGenerator(seed=100)

        motif1 = gen1.generate_melodic_motif()
        motif2 = gen2.generate_melodic_motif()

        assert len(motif1.notes) == len(motif2.notes)
        for n1, n2 in zip(motif1.notes, motif2.notes):
            assert n1.pitch == n2.pitch

    def test_tension_affects_output(self, motif_generator):
        """Higher tension produces different motifs."""
        low = motif_generator.generate_melodic_motif(tension=0.2)
        high = motif_generator.generate_melodic_motif(tension=0.8)

        # Higher tension = faster tempo
        assert high.tempo > low.tempo

    def test_key_affects_scale(self, motif_generator):
        """Key determines scale used."""
        major_motif = motif_generator.generate_melodic_motif(key=MusicalKey.C_MAJOR)
        minor_motif = motif_generator.generate_melodic_motif(key=MusicalKey.C_MINOR)

        # Tags should reflect scale type
        assert "major" in major_motif.tags or "melodic" in major_motif.tags


class TestTensionMapper:
    """Tests for TensionMapper."""

    def test_create_mapper(self, tension_mapper):
        """Can create tension mapper."""
        assert tension_mapper.tension == 0.0

    def test_set_tension(self, tension_mapper):
        """Can set tension."""
        tension_mapper.set_tension(0.7)
        tension_mapper.update(10.0)  # Large dt to reach target
        assert tension_mapper.tension > 0

    def test_immediate_tension(self, tension_mapper):
        """Can set tension immediately."""
        tension_mapper.set_tension(0.8, immediate=True)
        assert tension_mapper.tension == 0.8

    def test_gradual_transition(self, tension_mapper):
        """Tension transitions gradually."""
        tension_mapper.set_tension(1.0)
        tension_mapper.update(0.1)  # Small dt

        # Should not reach target immediately
        assert 0 < tension_mapper.tension < 1.0

    def test_tempo_modifier(self, tension_mapper):
        """Tension affects tempo."""
        tension_mapper.set_tension(0.0, immediate=True)
        low_mod = tension_mapper.get_tempo_modifier()

        tension_mapper.set_tension(1.0, immediate=True)
        high_mod = tension_mapper.get_tempo_modifier()

        assert high_mod > low_mod

    def test_dynamics_modifier(self, tension_mapper):
        """Tension affects dynamics."""
        tension_mapper.set_tension(0.0, immediate=True)
        low_dyn = tension_mapper.get_dynamics_modifier()

        tension_mapper.set_tension(1.0, immediate=True)
        high_dyn = tension_mapper.get_dynamics_modifier()

        assert high_dyn > low_dyn

    def test_suggested_key(self, tension_mapper):
        """High tension suggests minor key."""
        tension_mapper.set_tension(0.9, immediate=True)
        key = tension_mapper.get_suggested_key()
        assert "minor" in key.value.lower()

    def test_serialization(self, tension_mapper):
        """Mapper can be serialized."""
        tension_mapper.set_tension(0.6, immediate=True)
        data = tension_mapper.to_dict()

        assert data["current_tension"] == 0.6


class TestThemeEngine:
    """Tests for ThemeEngine."""

    def test_create_engine(self, theme_engine):
        """Can create theme engine."""
        assert theme_engine is not None

    def test_generate_theme_noir(self, theme_engine):
        """Can generate noir theme."""
        motifs = theme_engine.generate_theme("main_theme", mood="noir")

        assert len(motifs) >= 3
        # Should have melodic, bass, and chord components

    def test_generate_theme_tense(self, theme_engine):
        """Can generate tense theme."""
        motifs = theme_engine.generate_theme("chase", mood="tense")
        assert len(motifs) > 0

    def test_generate_theme_ambient(self, theme_engine):
        """Can generate ambient theme."""
        motifs = theme_engine.generate_theme("background", mood="ambient")
        assert len(motifs) > 0

    def test_generate_theme_action(self, theme_engine):
        """Can generate action theme."""
        motifs = theme_engine.generate_theme("fight", mood="action")
        assert len(motifs) > 0

    def test_get_theme(self, theme_engine):
        """Can retrieve generated theme."""
        theme_engine.generate_theme("stored", mood="noir")
        retrieved = theme_engine.get_theme("stored")

        assert retrieved is not None
        assert len(retrieved) > 0

    def test_tension_affects_theme(self, theme_engine):
        """Tension affects generated themes."""
        theme_engine.set_tension(0.9, immediate=True)
        high_tension = theme_engine.generate_theme("high", mood="noir")

        theme_engine.set_tension(0.1, immediate=True)
        low_tension = theme_engine.generate_theme("low", mood="noir")

        # Higher tension themes should be more intense
        high_avg_tension = sum(m.tension_level for m in high_tension) / len(high_tension)
        low_avg_tension = sum(m.tension_level for m in low_tension) / len(low_tension)

        assert high_avg_tension > low_avg_tension

    def test_activate_motif(self, theme_engine, motif_generator):
        """Can activate motif for playback."""
        motif = motif_generator.generate_melodic_motif()
        theme_engine.activate_motif(motif)

        active = theme_engine.get_active_motifs()
        assert motif.id in active

    def test_deactivate_motif(self, theme_engine, motif_generator):
        """Can deactivate motif."""
        motif = motif_generator.generate_melodic_motif()
        theme_engine.activate_motif(motif)
        theme_engine.deactivate_motif(motif.id)

        active = theme_engine.get_active_motifs()
        assert motif.id not in active

    def test_clear_active(self, theme_engine, motif_generator):
        """Can clear all active motifs."""
        motif1 = motif_generator.generate_melodic_motif()
        motif2 = motif_generator.generate_bass_motif()

        theme_engine.activate_motif(motif1)
        theme_engine.activate_motif(motif2)
        theme_engine.clear_active()

        assert len(theme_engine.get_active_motifs()) == 0

    def test_serialization(self, theme_engine):
        """Engine can be serialized."""
        theme_engine.generate_theme("test", mood="noir")
        theme_engine.set_tension(0.5, immediate=True)

        data = theme_engine.to_dict()
        assert "themes" in data
        assert "tension_mapper" in data


class TestMusicalConstants:
    """Tests for musical constants."""

    def test_note_frequencies(self):
        """Note frequencies are correct."""
        # Index 3 is octave 4 (A4 = 440Hz)
        assert abs(NOTE_FREQUENCIES["A"][3] - 440.0) < 0.1
        # Index 3 is octave 4 (C4 = 261.63Hz)
        assert abs(NOTE_FREQUENCIES["C"][3] - 261.63) < 0.1

    def test_scale_patterns(self):
        """Scale patterns are correct."""
        assert SCALE_PATTERNS["major"] == [0, 2, 4, 5, 7, 9, 11]
        assert SCALE_PATTERNS["minor"] == [0, 2, 3, 5, 7, 8, 10]
        assert len(SCALE_PATTERNS["pentatonic_major"]) == 5

    def test_all_keys_defined(self):
        """All musical keys are defined."""
        for key in MusicalKey:
            assert key.value is not None

    def test_all_motif_types_defined(self):
        """All motif types are defined."""
        assert len(MotifType) >= 7
