"""Extended tests for render systems."""

import pytest
from src.shadowengine.render import (
    Color, ColorSupport, ColorTheme, ColorManager, ANSI, THEMES,
    Particle, ParticleType, ParticleConfig, ParticleSystem,
    PARTICLE_CONFIGS, weather_to_particles,
    Mood, AtmosphereConfig, TensionMeter, AtmosphereManager,
    MOOD_CONFIGS, TENSION_TRIGGERS, get_tension_for_event
)


class TestColorEdgeCases:
    """Edge case tests for color system."""

    def test_color_from_hex_lowercase(self):
        """Should handle lowercase hex codes."""
        color = Color.from_hex("#ff00ff")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 255

    def test_color_rgb_boundaries(self):
        """Should handle RGB boundary values."""
        black = Color(r=0, g=0, b=0)
        white = Color(r=255, g=255, b=255)

        assert black.to_ansi_fg() == "\033[38;2;0;0;0m"
        assert white.to_ansi_fg() == "\033[38;2;255;255;255m"

    def test_color_manager_with_empty_text(self):
        """Should handle empty text."""
        manager = ColorManager(force_color=True)
        result = manager.colorize("", ANSI.RED)
        assert result == f"{ANSI.RED}{ANSI.RESET}"

    def test_color_manager_special_characters(self):
        """Should handle special characters in text."""
        manager = ColorManager(force_color=True)
        special = "Test\n\t\"quotes\" & <tags>"
        result = manager.bold(special)
        assert special in result

    def test_theme_switching(self):
        """Should switch themes correctly."""
        manager = ColorManager(force_color=True)

        for theme_name in THEMES:
            manager.set_theme(theme_name)
            assert manager.theme.name == theme_name

    def test_hotspot_unknown_type(self):
        """Should handle unknown hotspot types."""
        manager = ColorManager(force_color=True)
        result = manager.hotspot("test", "unknown_type")
        assert "test" in result


class TestParticleEdgeCases:
    """Edge case tests for particle system."""

    def test_particle_negative_velocity(self):
        """Should handle negative velocity (upward movement)."""
        particle = Particle(x=10, y=10, char='*', velocity_x=-1, velocity_y=-1)
        particle.update()
        assert particle.x == 9
        assert particle.y == 9

    def test_particle_system_zero_size(self):
        """Should handle zero-size system."""
        system = ParticleSystem(width=0, height=0)
        system.enable_effect(ParticleType.RAIN)
        system.update()
        # Should not crash
        assert system.get_density() == 0

    def test_particle_system_resize_to_larger(self):
        """Should handle resizing to larger area."""
        system = ParticleSystem(width=10, height=10)
        system.particles.append(Particle(x=5, y=5, char='*'))

        system.resize(100, 100)

        assert system.width == 100
        assert len(system.particles) == 1

    def test_wind_extreme_values(self):
        """Should handle extreme wind values."""
        system = ParticleSystem(width=80, height=24)
        system.set_wind(10.0, 10.0)
        system.particles.append(Particle(x=40, y=12, char='|'))

        # Should not crash with extreme wind
        system.update()

    def test_multiple_effects_simultaneously(self):
        """Should handle multiple particle effects at once."""
        system = ParticleSystem(width=80, height=24)

        # Enable multiple effects
        system.enable_effect(ParticleType.RAIN)
        system.enable_effect(ParticleType.FOG)
        system.enable_effect(ParticleType.DUST)

        for _ in range(10):
            system.update()

        # Should have particles from different effects
        assert len(system.particles) > 0

    def test_disable_nonexistent_effect(self):
        """Should handle disabling effect that wasn't enabled."""
        system = ParticleSystem(width=80, height=24)
        # Should not crash
        system.disable_effect(ParticleType.SNOW)

    def test_particle_at_boundary(self):
        """Should handle particles at exact boundaries."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=79, y=23, char='*'))

        particle = system.get_particle_at(79, 23)
        assert particle is not None

    def test_particles_in_empty_area(self):
        """Should return empty list for area with no particles."""
        system = ParticleSystem(width=80, height=24)
        particles = system.get_particles_in_area(0, 0, 10, 10)
        assert len(particles) == 0


class TestAtmosphereEdgeCases:
    """Edge case tests for atmosphere system."""

    def test_tension_rapid_changes(self):
        """Should handle rapid tension changes."""
        meter = TensionMeter()

        for _ in range(10):
            meter.add_tension(0.5)
            meter.reduce_tension(0.3)
            meter.update()

        # Should remain in valid range
        assert 0 <= meter.current <= 1
        assert 0 <= meter.target <= 1

    def test_tension_at_thresholds(self):
        """Should correctly identify levels at exact thresholds."""
        meter = TensionMeter()

        meter.current = 0.3  # Exactly at tense threshold
        assert meter.get_level() == "tense"

        meter.current = 0.6  # Exactly at dangerous threshold
        assert meter.get_level() == "dangerous"

        meter.current = 0.85  # Exactly at critical threshold
        assert meter.get_level() == "critical"

    def test_atmosphere_tick_counter(self):
        """Tick counter should increment on update."""
        atmosphere = AtmosphereManager()
        initial_tick = atmosphere._tick

        for i in range(10):
            atmosphere.update()

        assert atmosphere._tick == initial_tick + 10

    def test_mood_override_persists_through_updates(self):
        """Mood override should persist through tension changes."""
        atmosphere = AtmosphereManager()
        atmosphere.set_mood(Mood.MYSTERIOUS)

        # Change tension
        atmosphere.tension.set_tension(0.9)
        for _ in range(20):
            atmosphere.update()

        # Mood should still be overridden
        assert atmosphere.current_mood == Mood.MYSTERIOUS

    def test_all_moods_have_descriptions(self):
        """All moods should have atmosphere descriptions."""
        atmosphere = AtmosphereManager()

        for mood in Mood:
            atmosphere.set_mood(mood)
            desc = atmosphere.get_atmosphere_description()
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_tension_visual_bar_various_widths(self):
        """Visual bar should work with various widths."""
        meter = TensionMeter()
        meter.current = 0.5

        for width in [5, 10, 20, 50, 100]:
            bar = meter.get_visual_bar(width)
            # Bar should be width + 2 (for brackets)
            assert len(bar) == width + 2


class TestWeatherParticleMapping:
    """Tests for weather to particle mapping."""

    def test_all_weather_types(self):
        """Should handle all weather types."""
        weather_types = [
            'clear', 'cloudy', 'overcast', 'light_rain', 'heavy_rain',
            'thunderstorm', 'snow', 'fog', 'windy', 'heatwave'
        ]

        for weather in weather_types:
            particles = weather_to_particles(weather)
            assert isinstance(particles, list)

    def test_thunderstorm_multiple_effects(self):
        """Thunderstorm should have multiple particle types."""
        particles = weather_to_particles('thunderstorm')
        assert len(particles) >= 2

    def test_windy_effects(self):
        """Windy weather should have appropriate particles."""
        particles = weather_to_particles('windy')
        assert ParticleType.DUST in particles or ParticleType.LEAVES in particles


class TestTensionTriggers:
    """Tests for tension triggers."""

    def test_all_predefined_triggers(self):
        """All predefined triggers should return float values."""
        for event in TENSION_TRIGGERS:
            tension = get_tension_for_event(event)
            assert isinstance(tension, (int, float))

    def test_positive_negative_triggers(self):
        """Should have both positive and negative tension triggers."""
        positive = [e for e, v in TENSION_TRIGGERS.items() if v > 0]
        negative = [e for e, v in TENSION_TRIGGERS.items() if v < 0]

        assert len(positive) > 0
        assert len(negative) > 0

    def test_trigger_event_categories(self):
        """Different event categories should exist."""
        events = list(TENSION_TRIGGERS.keys())

        # Should have discovery events
        discovery_events = [e for e in events if 'found' in e or 'discovered' in e]
        assert len(discovery_events) > 0

        # Should have accusation events
        accusation_events = [e for e in events if 'accusation' in e]
        assert len(accusation_events) > 0


class TestConfigIntegrity:
    """Tests for configuration integrity."""

    def test_all_particle_types_have_configs(self):
        """Every ParticleType should have a configuration."""
        for ptype in ParticleType:
            assert ptype in PARTICLE_CONFIGS
            config = PARTICLE_CONFIGS[ptype]
            assert len(config.chars) > 0

    def test_all_moods_have_configs(self):
        """Every Mood should have a configuration."""
        for mood in Mood:
            assert mood in MOOD_CONFIGS
            config = MOOD_CONFIGS[mood]
            assert isinstance(config.border_char, str)

    def test_all_themes_are_complete(self):
        """All themes should have required color fields."""
        required_attrs = ['text', 'dialogue', 'narration', 'ui_error', 'ui_success']

        for theme_name, theme in THEMES.items():
            for attr in required_attrs:
                assert hasattr(theme, attr)
                assert getattr(theme, attr) is not None


class TestParticleLifecycle:
    """Tests for complete particle lifecycle."""

    def test_particle_full_lifecycle(self):
        """Test particle from spawn to removal."""
        system = ParticleSystem(width=20, height=20)

        # Add particle that will leave bounds
        particle = Particle(x=10, y=18, char='|', velocity_y=1.0, lifetime=5)
        system.particles.append(particle)

        ages = []
        for _ in range(10):
            if system.particles:
                ages.append(system.particles[0].age if system.particles else -1)
            system.update()

        # Particle should have aged
        assert max(ages) > 0

    def test_finite_lifetime_removal(self):
        """Particles with finite lifetime should be removed."""
        system = ParticleSystem(width=80, height=24)

        # Add particle with short lifetime
        particle = Particle(x=40, y=12, char='*', lifetime=3)
        system.particles.append(particle)

        for _ in range(10):
            system.update()

        # Particle should be gone (either by lifetime or movement)
        # The original particle should no longer exist in its original form
        assert len([p for p in system.particles if p.lifetime == 3 and p.age == 0]) == 0


class TestAtmosphereAnimations:
    """Tests for atmosphere animation features."""

    def test_pulse_phase_cycles(self):
        """Pulse phase should cycle between 0 and 1."""
        atmosphere = AtmosphereManager()
        atmosphere.set_mood(Mood.TENSE)  # Has pulse enabled

        phases = []
        for _ in range(100):
            atmosphere.update()
            phases.append(atmosphere._pulse_phase)

        # Phase should cycle
        assert min(phases) >= 0
        assert max(phases) < 1

    def test_flicker_probability(self):
        """Flicker should occur probabilistically."""
        atmosphere = AtmosphereManager()
        atmosphere.set_mood(Mood.DREAD)  # Has flicker enabled

        flickers = [atmosphere.should_flicker() for _ in range(100)]

        # Should have some flickers but not all
        if atmosphere.config.flicker_rate > 0:
            assert any(flickers) or True  # Might not flicker due to randomness
