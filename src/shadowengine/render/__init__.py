"""
ASCII Render Engine

Procedural scene rendering with layers, particles, and atmosphere.
"""

from .scene import Scene, Location
from .renderer import Renderer
from .colors import (
    Color, ColorSupport, ColorTheme, ColorManager,
    ANSI, THEMES
)
from .particles import (
    Particle, ParticleType, ParticleConfig, ParticleSystem,
    PARTICLE_CONFIGS, weather_to_particles
)
from .atmosphere import (
    Mood, AtmosphereConfig, TensionMeter, AtmosphereManager,
    MOOD_CONFIGS, TENSION_TRIGGERS, get_tension_for_event
)

__all__ = [
    # Scene
    'Scene', 'Location', 'Renderer',
    # Colors
    'Color', 'ColorSupport', 'ColorTheme', 'ColorManager',
    'ANSI', 'THEMES',
    # Particles
    'Particle', 'ParticleType', 'ParticleConfig', 'ParticleSystem',
    'PARTICLE_CONFIGS', 'weather_to_particles',
    # Atmosphere
    'Mood', 'AtmosphereConfig', 'TensionMeter', 'AtmosphereManager',
    'MOOD_CONFIGS', 'TENSION_TRIGGERS', 'get_tension_for_event'
]
