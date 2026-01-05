# Future Feature: Voice & TTS System

> **Status**: Planning (implement after Phase 4 - game must be playable first)

## Vision

Transform ShadowEngine from a text-only experience into a fully voice-interactive game where:
- **Voice is the primary input** (keyboard as accessibility backup)
- **All characters have unique TTS voices**
- **Sound effects are generated via TTS + post-processing**

---

## Voice Input System

### Primary Control: Voice Commands

Players speak commands instead of typing:

```
Player: "Examine the desk"
Player: "Talk to the bartender"
Player: "Use the key on the door"
Player: "One" (hotspot selection)
```

### Input Pipeline

```
┌─────────────────┐
│  Microphone     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Speech-to-Text │  ← Whisper, Vosk, or similar
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Intent Parser  │  ← Existing interaction engine
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Game Command   │
└─────────────────┘
```

### STT Engine Options

| Engine | Pros | Cons |
|--------|------|------|
| **Whisper (local)** | High accuracy, offline, free | Requires GPU for speed |
| **Vosk** | Lightweight, offline, fast | Less accurate |
| **Web Speech API** | Easy, browser-native | Online only |
| **Azure/Google STT** | Very accurate | Costs money, online |

**Recommendation**: Whisper (local) for quality, Vosk as lightweight fallback.

### Wake Word (Optional)

Consider wake word to avoid always-listening:
- "Hey Shadow" or similar
- Push-to-talk as alternative
- Configurable per player preference

### Keyboard Fallback

All voice commands must have keyboard equivalents:
- Accessibility requirement
- Quiet environment option
- Fallback when STT fails

---

## TTS Voice System

### Character Voice Generation

Each NPC gets a distinct synthesized voice:

```python
CharacterVoice:
    voice_id: str           # base voice model
    pitch: float            # -1.0 to 1.0
    speed: float            # 0.5 to 2.0
    breathiness: float      # 0.0 to 1.0
    roughness: float        # 0.0 to 1.0
    age_modifier: float     # -1.0 (young) to 1.0 (old)
    accent: str             # accent model if available
    emotion_baseline: str   # default emotional tone
```

### Voice Variety System

Create huge range of voice characters through:

1. **Base Voice Selection** - Multiple TTS voice models
2. **Parameter Modulation** - Pitch, speed, breathiness
3. **Post-Processing** - Filters, effects, modifications
4. **Emotional States** - Same voice sounds different when scared vs angry

### TTS Engine Options

| Engine | Pros | Cons |
|--------|------|------|
| **Coqui TTS** | Free, local, customizable | Setup complexity |
| **Piper** | Fast, lightweight, offline | Fewer voices |
| **Bark** | Very natural, emotions | Slow, heavy |
| **ElevenLabs** | Excellent quality | Paid API |
| **Azure Neural** | Great quality, many voices | Paid API |

**Recommendation**: Coqui TTS or Piper for local/free, ElevenLabs for quality premium option.

### Dialogue Delivery

```
┌─────────────────┐
│  Dialogue Text  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Emotion Tag    │  ← From character state
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TTS Engine     │  ← With voice parameters
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post-Process   │  ← Room acoustics, effects
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audio Output   │
└─────────────────┘
```

---

## Post-TTS Sound Processing

### The Big Idea

Use TTS as a base for ALL game sounds, then process to create effects:

```
TTS "Ahhhhh"  →  [pitch shift + distortion + reverb]  →  Scream
TTS "Ssssss"  →  [high pitch + flanger]               →  Screech
TTS "Boom"    →  [low pitch + compression + reverb]   →  Explosion
TTS "Drip"    →  [delay + room reverb]                →  Water drops
```

### Sound Categories

| Category | TTS Base | Processing |
|----------|----------|------------|
| **Screams** | Vowel sounds "Ahh", "Ehh" | Pitch shift, distortion, long reverb |
| **Screeches** | "Sss", "Eee" | High pitch, flanger, short sharp |
| **Impacts** | "Boom", "Thud" | Low pitch, compression, short decay |
| **Ambience** | Humming, breathing | Layer, loop, subtle modulation |
| **Footsteps** | "Tap", "Thump" | EQ, timing variation |
| **Weather** | "Shhh", "Patter" | Layering, stereo spread |

### Processing Pipeline

```python
SoundEffect:
    tts_seed: str           # base TTS input
    tts_voice: str          # which voice model
    effects: list[Effect]   # processing chain

Effect:
    type: str               # pitch, distort, reverb, delay, eq, etc.
    parameters: dict        # effect-specific settings
```

### Audio Processing Stack

| Effect | Use Case |
|--------|----------|
| **Pitch Shift** | Age voices, create creatures |
| **Time Stretch** | Slow/speed without pitch change |
| **Distortion** | Screams, radio, damage |
| **Reverb** | Room size, outdoor/indoor |
| **Delay** | Echoes, space |
| **EQ** | Phone filter, muffled, bright |
| **Compression** | Punch, loudness |
| **Flanger/Phaser** | Otherworldly, mechanical |
| **Tremolo** | Fear, instability |
| **Vocoder** | Robot, possessed |

### Library Options

| Library | Purpose |
|---------|---------|
| **PyDub** | Simple audio manipulation |
| **Pedalboard** | Real-time effects processing |
| **scipy.signal** | DSP fundamentals |
| **librosa** | Audio analysis and manipulation |
| **sounddevice** | Audio I/O |

---

## Atmospheric Audio

### Generated Ambience

Each location has generated ambient sound:

```python
Ambience:
    layers: list[AmbientLayer]

AmbientLayer:
    sound_type: str         # rain, wind, crowd, machinery
    volume: float
    variation: float        # how much it changes
    stereo_width: float
```

### Weather Audio

Weather system drives sound generation:

| Weather | Sound Layers |
|---------|--------------|
| Rain | Drops on surface, distant thunder, splashing |
| Storm | Heavy rain, thunder, wind howls |
| Fog | Muffled ambience, dripping |
| Wind | Whistling, rustling, creaking |

### Tension Audio

Tension level affects audio atmosphere:
- Low: Calm, quiet ambient
- Medium: Subtle unease, minor dissonance
- High: Darker tones, more activity
- Critical: Intense, building dread

---

## Implementation Plan

### Prerequisites
- Game fully playable (Phase 4 complete)
- Audio output working in terminal environment
- Microphone input tested

### Phase 5.1: Basic TTS Output
- [ ] Integrate TTS engine
- [ ] Character voice parameter system
- [ ] Speak dialogue aloud
- [ ] Voice variety for NPCs

### Phase 5.2: Voice Input
- [ ] STT engine integration
- [ ] Voice command parsing
- [ ] Keyboard fallback
- [ ] Wake word (optional)

### Phase 5.3: Sound Effects
- [ ] Post-TTS processing pipeline
- [ ] Effect library
- [ ] Sound generation from TTS seeds
- [ ] Trigger sounds from game events

### Phase 5.4: Atmosphere
- [ ] Ambient sound generation
- [ ] Weather audio
- [ ] Tension-based audio
- [ ] Spatial audio (if terminal supports)

### Phase 5.5: Polish
- [ ] Voice customization per character
- [ ] Audio settings/preferences
- [ ] Performance optimization
- [ ] Accessibility options

---

## Accessibility Considerations

- **Always keyboard fallback** - Voice is enhancement, not requirement
- **Subtitles** - All spoken content has text display
- **Speed control** - TTS speed adjustable
- **Volume mixing** - Separate voice/effects/ambience volumes
- **Mute options** - Can disable any audio category
- **Visual cues** - Important sounds have visual indicators

---

## Technical Notes

### Audio in Terminal

Terminal audio output options:
- System audio through Python (sounddevice, pygame.mixer)
- Pipe to external player
- Web interface alternative for full audio control

### Performance

- Pre-generate common sounds at startup
- Cache generated TTS
- Async audio generation
- Stream long dialogues

### Storage

- Voice models can be large (100MB-1GB each)
- Pre-generated sounds can be cached
- Offer "download voice pack" for characters
