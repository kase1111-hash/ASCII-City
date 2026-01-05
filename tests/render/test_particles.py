"""Tests for the particle system."""

import pytest
from src.shadowengine.render.particles import (
    Particle, ParticleType, ParticleConfig, ParticleSystem,
    PARTICLE_CONFIGS, weather_to_particles
)


class TestParticle:
    """Tests for Particle dataclass."""

    def test_particle_creation(self):
        """Should create a particle with position and character."""
        particle = Particle(x=5.0, y=10.0, char='|')
        assert particle.x == 5.0
        assert particle.y == 10.0
        assert particle.char == '|'

    def test_particle_default_velocity(self):
        """Default velocity should be zero."""
        particle = Particle(x=0, y=0, char='.')
        assert particle.velocity_x == 0.0
        assert particle.velocity_y == 0.0

    def test_particle_update_moves_position(self):
        """Update should move particle by velocity."""
        particle = Particle(x=5.0, y=5.0, char='|', velocity_x=1.0, velocity_y=2.0)
        particle.update()
        assert particle.x == 6.0
        assert particle.y == 7.0

    def test_particle_infinite_lifetime(self):
        """Particle with -1 lifetime should live forever."""
        particle = Particle(x=0, y=0, char='.', lifetime=-1)
        for _ in range(100):
            assert particle.update() is True

    def test_particle_finite_lifetime(self):
        """Particle should die after lifetime expires."""
        particle = Particle(x=0, y=0, char='.', lifetime=5)
        for _ in range(4):
            assert particle.update() is True
        assert particle.update() is False  # Dies on 5th update

    def test_particle_age_increments(self):
        """Age should increment on each update."""
        particle = Particle(x=0, y=0, char='.')
        assert particle.age == 0
        particle.update()
        assert particle.age == 1
        particle.update()
        assert particle.age == 2


class TestParticleConfig:
    """Tests for ParticleConfig."""

    def test_config_creation(self):
        """Should create config with particle characters."""
        config = ParticleConfig(chars=['*', '.'])
        assert '*' in config.chars
        assert '.' in config.chars

    def test_default_velocity_ranges(self):
        """Default velocity should be downward."""
        config = ParticleConfig(chars=['.'])
        assert config.velocity_y_range[0] >= 0  # Positive = downward


class TestPredefinedConfigs:
    """Tests for predefined particle configurations."""

    def test_rain_config_exists(self):
        """Rain config should be defined."""
        assert ParticleType.RAIN in PARTICLE_CONFIGS
        config = PARTICLE_CONFIGS[ParticleType.RAIN]
        assert '|' in config.chars

    def test_snow_config_exists(self):
        """Snow config should be defined."""
        assert ParticleType.SNOW in PARTICLE_CONFIGS
        config = PARTICLE_CONFIGS[ParticleType.SNOW]
        assert config.velocity_y_range[1] < 0.5  # Slow falling

    def test_fog_config_exists(self):
        """Fog config should be defined."""
        assert ParticleType.FOG in PARTICLE_CONFIGS
        config = PARTICLE_CONFIGS[ParticleType.FOG]
        assert config.lifetime_range[0] > 0  # Has finite lifetime

    def test_all_particle_types_have_configs(self):
        """All particle types should have configurations."""
        for particle_type in ParticleType:
            assert particle_type in PARTICLE_CONFIGS


class TestParticleSystem:
    """Tests for ParticleSystem."""

    def test_system_creation(self):
        """Should create particle system with dimensions."""
        system = ParticleSystem(width=80, height=24)
        assert system.width == 80
        assert system.height == 24
        assert len(system.particles) == 0

    def test_enable_effect(self):
        """Should enable particle effect."""
        system = ParticleSystem(width=80, height=24)
        system.enable_effect(ParticleType.RAIN)
        assert system.active_effects.get(ParticleType.RAIN) is True

    def test_disable_effect(self):
        """Should disable particle effect and remove particles."""
        system = ParticleSystem(width=80, height=24)
        system.enable_effect(ParticleType.RAIN)
        system.update()  # Spawn some particles

        system.disable_effect(ParticleType.RAIN)
        assert system.active_effects.get(ParticleType.RAIN) is False

    def test_update_spawns_particles(self):
        """Update should spawn new particles for active effects."""
        system = ParticleSystem(width=80, height=24)
        system.enable_effect(ParticleType.RAIN)

        initial_count = len(system.particles)
        system.update()

        assert len(system.particles) > initial_count

    def test_update_moves_particles(self):
        """Update should move existing particles."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=40, y=5, char='|', velocity_y=1.0))

        system.update()

        assert system.particles[0].y == 6.0

    def test_particles_removed_when_out_of_bounds(self):
        """Particles should be removed when leaving bounds."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=40, y=23, char='|', velocity_y=2.0))

        system.update()

        assert len(system.particles) == 0

    def test_set_wind(self):
        """Should set wind velocity."""
        system = ParticleSystem(width=80, height=24)
        system.set_wind(0.5, 0.1)
        assert system.wind_x == 0.5
        assert system.wind_y == 0.1

    def test_wind_affects_particles(self):
        """Wind should affect wind-affected particles."""
        system = ParticleSystem(width=80, height=24)
        system.set_wind(1.0, 0.0)
        system.particles.append(Particle(x=40, y=10, char='|', velocity_x=0.0))

        system.update()

        # Particle should have moved right due to wind
        assert system.particles[0].velocity_x > 0

    def test_max_particles_limit(self):
        """Should not exceed max particles."""
        system = ParticleSystem(width=80, height=24, max_particles=10)
        system.enable_effect(ParticleType.HEAVY_RAIN)

        for _ in range(20):
            system.update()

        assert len(system.particles) <= 10

    def test_get_particle_at(self):
        """Should return particle at specific position."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=10, y=5, char='*'))

        particle = system.get_particle_at(10, 5)
        assert particle is not None
        assert particle.char == '*'

    def test_get_particle_at_empty(self):
        """Should return None if no particle at position."""
        system = ParticleSystem(width=80, height=24)
        particle = system.get_particle_at(10, 5)
        assert particle is None

    def test_get_particles_in_area(self):
        """Should return particles in rectangular area."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=5, y=5, char='*'))
        system.particles.append(Particle(x=15, y=5, char='.'))
        system.particles.append(Particle(x=5, y=15, char='+'))

        area_particles = system.get_particles_in_area(0, 0, 10, 10)
        assert len(area_particles) == 1
        assert area_particles[0].char == '*'

    def test_render_overlay(self):
        """Should return particle overlay dictionary."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=10, y=5, char='|'))
        system.particles.append(Particle(x=20, y=10, char='*'))

        overlay = system.render_overlay()
        assert overlay[(10, 5)] == '|'
        assert overlay[(20, 10)] == '*'

    def test_clear(self):
        """Should remove all particles."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=10, y=5, char='|'))
        system.particles.append(Particle(x=20, y=10, char='*'))

        system.clear()
        assert len(system.particles) == 0

    def test_get_density(self):
        """Should calculate particle density."""
        system = ParticleSystem(width=10, height=10)
        # 100 cells total
        for i in range(10):
            system.particles.append(Particle(x=i, y=0, char='.'))

        density = system.get_density()
        assert density == 0.1  # 10 particles / 100 cells

    def test_resize(self):
        """Should resize and remove out-of-bounds particles."""
        system = ParticleSystem(width=80, height=24)
        system.particles.append(Particle(x=70, y=20, char='|'))
        system.particles.append(Particle(x=5, y=5, char='*'))

        system.resize(50, 15)

        assert system.width == 50
        assert system.height == 15
        assert len(system.particles) == 1
        assert system.particles[0].char == '*'


class TestWeatherToParticles:
    """Tests for weather to particles mapping."""

    def test_clear_weather_no_particles(self):
        """Clear weather should have no particles."""
        particles = weather_to_particles('clear')
        assert len(particles) == 0

    def test_light_rain_particles(self):
        """Light rain should have rain particles."""
        particles = weather_to_particles('light_rain')
        assert ParticleType.RAIN in particles

    def test_heavy_rain_particles(self):
        """Heavy rain should have heavy rain particles."""
        particles = weather_to_particles('heavy_rain')
        assert ParticleType.HEAVY_RAIN in particles

    def test_thunderstorm_particles(self):
        """Thunderstorm should have rain and sparks."""
        particles = weather_to_particles('thunderstorm')
        assert ParticleType.HEAVY_RAIN in particles
        assert ParticleType.SPARKS in particles

    def test_snow_particles(self):
        """Snow weather should have snow particles."""
        particles = weather_to_particles('snow')
        assert ParticleType.SNOW in particles

    def test_fog_particles(self):
        """Fog weather should have fog particles."""
        particles = weather_to_particles('fog')
        assert ParticleType.FOG in particles

    def test_case_insensitive(self):
        """Weather lookup should be case insensitive."""
        particles = weather_to_particles('LIGHT_RAIN')
        assert ParticleType.RAIN in particles

    def test_unknown_weather(self):
        """Unknown weather should return empty list."""
        particles = weather_to_particles('unknown_weather')
        assert len(particles) == 0
