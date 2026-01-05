"""
Particle System - ASCII visual effects for atmosphere.

Provides:
- Rain, snow, fog, dust particles
- Animated particle movement
- Weather-responsive effects
- Integration with tension/atmosphere
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto
import random


class ParticleType(Enum):
    """Types of particles for visual effects."""
    RAIN = auto()
    HEAVY_RAIN = auto()
    SNOW = auto()
    FOG = auto()
    MIST = auto()
    DUST = auto()
    SMOKE = auto()
    SPARKS = auto()
    LEAVES = auto()


@dataclass
class Particle:
    """A single particle in the system."""
    x: float
    y: float
    char: str
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    lifetime: int = -1  # -1 = infinite
    age: int = 0

    def update(self) -> bool:
        """
        Update particle position.

        Returns True if particle is still alive.
        """
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.age += 1

        if self.lifetime > 0 and self.age >= self.lifetime:
            return False
        return True


@dataclass
class ParticleConfig:
    """Configuration for a particle type."""
    chars: list[str]
    velocity_x_range: tuple[float, float] = (0.0, 0.0)
    velocity_y_range: tuple[float, float] = (0.5, 1.0)
    density: float = 0.1  # Particles per cell
    lifetime_range: tuple[int, int] = (-1, -1)  # -1 = infinite
    spawn_top: bool = True
    spawn_bottom: bool = False
    spawn_left: bool = False
    spawn_right: bool = False
    wind_affected: bool = True


# Predefined particle configurations
PARTICLE_CONFIGS: dict[ParticleType, ParticleConfig] = {
    ParticleType.RAIN: ParticleConfig(
        chars=['|', '/', '\\'],
        velocity_x_range=(-0.1, 0.1),
        velocity_y_range=(0.8, 1.2),
        density=0.15,
        spawn_top=True
    ),
    ParticleType.HEAVY_RAIN: ParticleConfig(
        chars=['|', '/', '\\', '│'],
        velocity_x_range=(-0.2, 0.2),
        velocity_y_range=(1.0, 1.5),
        density=0.3,
        spawn_top=True
    ),
    ParticleType.SNOW: ParticleConfig(
        chars=['*', '.', '·', '○'],
        velocity_x_range=(-0.3, 0.3),
        velocity_y_range=(0.2, 0.4),
        density=0.1,
        spawn_top=True
    ),
    ParticleType.FOG: ParticleConfig(
        chars=['░', '▒', '·', '.'],
        velocity_x_range=(-0.1, 0.1),
        velocity_y_range=(-0.05, 0.05),
        density=0.05,
        lifetime_range=(20, 40),
        spawn_top=True,
        spawn_bottom=True,
        spawn_left=True,
        spawn_right=True
    ),
    ParticleType.MIST: ParticleConfig(
        chars=['·', '.', ' '],
        velocity_x_range=(-0.05, 0.05),
        velocity_y_range=(-0.02, 0.02),
        density=0.03,
        lifetime_range=(30, 60),
        spawn_top=True,
        spawn_bottom=True
    ),
    ParticleType.DUST: ParticleConfig(
        chars=['·', '.', ':', '∙'],
        velocity_x_range=(0.1, 0.3),
        velocity_y_range=(-0.1, 0.1),
        density=0.02,
        lifetime_range=(15, 30),
        spawn_left=True
    ),
    ParticleType.SMOKE: ParticleConfig(
        chars=['░', '▒', '▓', '○'],
        velocity_x_range=(-0.1, 0.1),
        velocity_y_range=(-0.3, -0.1),
        density=0.04,
        lifetime_range=(20, 40),
        spawn_bottom=True
    ),
    ParticleType.SPARKS: ParticleConfig(
        chars=['*', '+', '·', '°'],
        velocity_x_range=(-0.5, 0.5),
        velocity_y_range=(-0.8, -0.3),
        density=0.02,
        lifetime_range=(5, 15),
        spawn_bottom=True
    ),
    ParticleType.LEAVES: ParticleConfig(
        chars=['~', '∿', '❧', '♠'],
        velocity_x_range=(0.2, 0.5),
        velocity_y_range=(0.1, 0.3),
        density=0.01,
        lifetime_range=(30, 60),
        spawn_top=True,
        spawn_left=True
    )
}


@dataclass
class ParticleSystem:
    """
    Manages particle effects for ASCII rendering.

    Handles spawning, updating, and rendering of particles
    for weather and atmospheric effects.
    """

    width: int
    height: int
    particles: list[Particle] = field(default_factory=list)
    active_effects: dict[ParticleType, bool] = field(default_factory=dict)
    wind_x: float = 0.0
    wind_y: float = 0.0
    max_particles: int = 500

    def enable_effect(self, effect: ParticleType) -> None:
        """Enable a particle effect."""
        self.active_effects[effect] = True

    def disable_effect(self, effect: ParticleType) -> None:
        """Disable a particle effect."""
        self.active_effects[effect] = False
        # Remove existing particles of this type
        config = PARTICLE_CONFIGS.get(effect)
        if config:
            self.particles = [
                p for p in self.particles
                if p.char not in config.chars
            ]

    def set_wind(self, x: float, y: float) -> None:
        """Set wind velocity affecting particles."""
        self.wind_x = x
        self.wind_y = y

    def update(self) -> None:
        """Update all particles and spawn new ones."""
        # Update existing particles
        alive_particles = []
        for particle in self.particles:
            # Apply wind
            config = self._get_config_for_particle(particle)
            if config and config.wind_affected:
                particle.velocity_x += self.wind_x * 0.1
                particle.velocity_y += self.wind_y * 0.1

            if particle.update():
                # Check bounds
                if 0 <= particle.x < self.width and 0 <= particle.y < self.height:
                    alive_particles.append(particle)

        self.particles = alive_particles

        # Spawn new particles
        self._spawn_particles()

    def _spawn_particles(self) -> None:
        """Spawn new particles for active effects."""
        for effect_type, active in self.active_effects.items():
            if not active:
                continue

            config = PARTICLE_CONFIGS.get(effect_type)
            if not config:
                continue

            # Calculate spawn count based on density
            spawn_count = int(self.width * config.density)

            # Limit total particles
            if len(self.particles) + spawn_count > self.max_particles:
                spawn_count = max(0, self.max_particles - len(self.particles))

            for _ in range(spawn_count):
                particle = self._create_particle(config)
                if particle:
                    self.particles.append(particle)

    def _create_particle(self, config: ParticleConfig) -> Optional[Particle]:
        """Create a new particle based on configuration."""
        # Determine spawn position
        x, y = self._get_spawn_position(config)

        # Random velocity within range
        vx = random.uniform(*config.velocity_x_range)
        vy = random.uniform(*config.velocity_y_range)

        # Random character
        char = random.choice(config.chars)

        # Random lifetime
        if config.lifetime_range[0] > 0:
            lifetime = random.randint(*config.lifetime_range)
        else:
            lifetime = -1

        return Particle(
            x=x,
            y=y,
            char=char,
            velocity_x=vx,
            velocity_y=vy,
            lifetime=lifetime
        )

    def _get_spawn_position(self, config: ParticleConfig) -> tuple[float, float]:
        """Get spawn position based on configuration."""
        spawn_edges = []
        if config.spawn_top:
            spawn_edges.append('top')
        if config.spawn_bottom:
            spawn_edges.append('bottom')
        if config.spawn_left:
            spawn_edges.append('left')
        if config.spawn_right:
            spawn_edges.append('right')

        if not spawn_edges:
            spawn_edges = ['top']

        edge = random.choice(spawn_edges)

        if edge == 'top':
            return random.uniform(0, self.width), 0
        elif edge == 'bottom':
            return random.uniform(0, self.width), self.height - 1
        elif edge == 'left':
            return 0, random.uniform(0, self.height)
        else:  # right
            return self.width - 1, random.uniform(0, self.height)

    def _get_config_for_particle(self, particle: Particle) -> Optional[ParticleConfig]:
        """Find the config that matches a particle's character."""
        for config in PARTICLE_CONFIGS.values():
            if particle.char in config.chars:
                return config
        return None

    def get_particle_at(self, x: int, y: int) -> Optional[Particle]:
        """Get particle at a specific position (if any)."""
        for particle in self.particles:
            if int(particle.x) == x and int(particle.y) == y:
                return particle
        return None

    def get_particles_in_area(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> list[Particle]:
        """Get all particles in a rectangular area."""
        return [
            p for p in self.particles
            if x <= int(p.x) < x + width and y <= int(p.y) < y + height
        ]

    def render_overlay(self) -> dict[tuple[int, int], str]:
        """
        Get particle overlay for rendering.

        Returns dict mapping (x, y) to particle character.
        """
        overlay = {}
        for particle in self.particles:
            pos = (int(particle.x), int(particle.y))
            # Later particles overwrite earlier ones
            overlay[pos] = particle.char
        return overlay

    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()

    def get_density(self) -> float:
        """Get current particle density (particles per cell)."""
        total_cells = self.width * self.height
        if total_cells == 0:
            return 0.0
        return len(self.particles) / total_cells

    def resize(self, width: int, height: int) -> None:
        """Resize the particle area."""
        self.width = width
        self.height = height
        # Remove particles outside new bounds
        self.particles = [
            p for p in self.particles
            if 0 <= p.x < width and 0 <= p.y < height
        ]


def weather_to_particles(weather_type: str) -> list[ParticleType]:
    """Map weather type to particle effects."""
    weather_particles = {
        'clear': [],
        'cloudy': [],
        'overcast': [ParticleType.MIST],
        'light_rain': [ParticleType.RAIN],
        'heavy_rain': [ParticleType.HEAVY_RAIN],
        'thunderstorm': [ParticleType.HEAVY_RAIN, ParticleType.SPARKS],
        'snow': [ParticleType.SNOW],
        'fog': [ParticleType.FOG],
        'windy': [ParticleType.DUST, ParticleType.LEAVES],
        'heatwave': [ParticleType.DUST]
    }
    return weather_particles.get(weather_type.lower(), [])
