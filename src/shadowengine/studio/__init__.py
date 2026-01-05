"""
ASCII Art Studio Module - Player creativity becomes world content.

This module provides the ASCII Art Studio system including:
- ASCIIArt: Base art structure with tiles and metadata
- ArtTags: Semantic tagging system for classification
- StaticArt: Non-interactive visual elements
- DynamicEntity: Interactive entities with behavior
- PersonalityTemplate: Behavioral personalities for entities
- Animation: Frame-based ASCII animations
- AssetPool: World asset management
- Gallery: Community sharing and discovery
- Studio: Main creation interface
"""

from .art import ASCIIArt, ArtCategory
from .tags import (
    ArtTags, ObjectType, Size, Placement,
    InteractionType, EnvironmentType
)
from .static_art import StaticArt, RenderLayer, TileCoverage
from .entity import DynamicEntity, EntityState
from .personality import (
    PersonalityTemplate, IdleBehavior, ThreatResponse, Attitude,
    PERSONALITY_TEMPLATES
)
from .animation import Animation, AnimationFrame, AnimationTrigger
from .asset_pool import AssetPool
from .usage_stats import UsageStats
from .gallery import Gallery, GalleryEntry
from .studio import Studio, StudioMode

__all__ = [
    # Core art
    "ASCIIArt",
    "ArtCategory",
    "ArtTags",

    # Classification
    "ObjectType",
    "Size",
    "Placement",
    "InteractionType",
    "EnvironmentType",

    # Art types
    "StaticArt",
    "RenderLayer",
    "TileCoverage",
    "DynamicEntity",
    "EntityState",

    # Personality
    "PersonalityTemplate",
    "IdleBehavior",
    "ThreatResponse",
    "Attitude",
    "PERSONALITY_TEMPLATES",

    # Animation
    "Animation",
    "AnimationFrame",
    "AnimationTrigger",

    # World integration
    "AssetPool",
    "UsageStats",

    # Gallery
    "Gallery",
    "GalleryEntry",

    # Studio
    "Studio",
    "StudioMode",
]
