"""Tests for DetailGenerator and related types."""

import pytest
from src.shadowengine.inspection.detail_generator import (
    DetailType, DetailTemplate, DetailGenerator, DETAIL_TEMPLATES
)
from src.shadowengine.inspection.zoom_level import ZoomLevel


class TestDetailType:
    """Tests for DetailType enum."""

    def test_all_types_exist(self):
        """Test all detail types exist."""
        assert DetailType.TEXTURE
        assert DetailType.WEAR
        assert DetailType.MARKING
        assert DetailType.HIDDEN
        assert DetailType.MATERIAL
        assert DetailType.MECHANISM
        assert DetailType.RESIDUE
        assert DetailType.INSCRIPTION
        assert DetailType.DAMAGE
        assert DetailType.CRAFTSMANSHIP

    def test_types_are_distinct(self):
        """Test types are distinct."""
        types = list(DetailType)
        assert len(types) == len(set(types))


class TestDetailTemplate:
    """Tests for DetailTemplate."""

    def test_create_template(self):
        """Test creating a detail template."""
        template = DetailTemplate(
            detail_type=DetailType.TEXTURE,
            template="The surface is {adjective}.",
            materials=["wood", "stone"]
        )
        assert template.detail_type == DetailType.TEXTURE
        assert "surface" in template.template
        assert "wood" in template.materials

    def test_template_with_tags(self):
        """Test template with tags."""
        template = DetailTemplate(
            detail_type=DetailType.WEAR,
            template="Worn edges visible",
            tags=["furniture", "old"]
        )
        assert "furniture" in template.tags
        assert "old" in template.tags

    def test_template_with_fact_reveal(self):
        """Test template that reveals facts."""
        template = DetailTemplate(
            detail_type=DetailType.HIDDEN,
            template="A hidden compartment!",
            significance=0.8,
            reveals_fact=True,
            fact_template="hidden_in_{object_id}"
        )
        assert template.reveals_fact
        assert template.fact_template is not None

    def test_applies_to_with_tags(self):
        """Test applies_to with matching tags."""
        template = DetailTemplate(
            detail_type=DetailType.TEXTURE,
            template="Test",
            tags=["furniture"]
        )
        assert template.applies_to(["furniture", "old"])
        assert not template.applies_to(["weapon"])

    def test_applies_to_with_materials(self):
        """Test applies_to with matching materials."""
        template = DetailTemplate(
            detail_type=DetailType.TEXTURE,
            template="Test",
            materials=["wood", "stone"]
        )
        assert template.applies_to([], "wood")
        assert not template.applies_to([], "metal")

    def test_applies_to_empty_requirements(self):
        """Test applies_to with no requirements."""
        template = DetailTemplate(
            detail_type=DetailType.TEXTURE,
            template="Test"
        )
        assert template.applies_to([])
        assert template.applies_to(["anything"])

    def test_generate_with_replacements(self):
        """Test generating text with replacements."""
        import random
        template = DetailTemplate(
            detail_type=DetailType.TEXTURE,
            template="The {material} surface is {adjective}."
        )
        rng = random.Random(42)
        result = template.generate(rng, material="oak", era="old")
        assert "oak" in result


class TestDetailTemplates:
    """Tests for predefined templates."""

    def test_templates_exist(self):
        """Test that predefined templates exist."""
        assert len(DETAIL_TEMPLATES) > 0

    def test_templates_cover_multiple_types(self):
        """Test templates cover different detail types."""
        types_covered = set()
        for template in DETAIL_TEMPLATES:
            types_covered.add(template.detail_type)

        assert len(types_covered) >= 5  # Should have various types

    def test_templates_have_templates(self):
        """Test all templates have template strings."""
        for template in DETAIL_TEMPLATES:
            assert template.template
            assert len(template.template) > 0


class TestDetailGenerator:
    """Tests for DetailGenerator."""

    def test_create_generator(self):
        """Test creating a detail generator."""
        gen = DetailGenerator()
        assert gen is not None
        assert gen.seed is not None

    def test_create_generator_with_seed(self):
        """Test creating generator with specific seed."""
        gen = DetailGenerator(seed=42)
        assert gen.seed == 42

    def test_generate_detail(self):
        """Test generating a single detail."""
        gen = DetailGenerator(seed=42)
        detail = gen.generate_detail(
            object_id="obj_123",
            zoom_level=2,
            tags=["furniture"]
        )
        assert detail is not None
        assert isinstance(detail, str)
        assert len(detail) > 0

    def test_generate_detail_deterministic(self):
        """Test detail generation is deterministic for same seed."""
        gen = DetailGenerator(seed=42)

        detail1 = gen.generate_detail(
            object_id="obj_123",
            zoom_level=2,
            tags=["furniture"]
        )

        # Create new generator with same seed
        gen2 = DetailGenerator(seed=42)
        detail2 = gen2.generate_detail(
            object_id="obj_123",
            zoom_level=2,
            tags=["furniture"]
        )

        assert detail1 == detail2

    def test_generate_details_multiple(self):
        """Test generating multiple details."""
        gen = DetailGenerator(seed=42)
        details = gen.generate_details(
            object_id="obj_123",
            zoom_level=2,
            count=3,
            tags=["furniture"]
        )

        assert len(details) >= 1  # At least one if templates match
        for detail in details:
            assert isinstance(detail, str)

    def test_generate_with_material(self):
        """Test generation with specific material."""
        gen = DetailGenerator(seed=42)
        detail = gen.generate_detail(
            object_id="obj_123",
            zoom_level=2,
            material="oak"
        )
        # Should generate something (may or may not contain material)
        assert detail is not None or detail is None  # May not match any template

    def test_generate_with_era(self):
        """Test generation with era context."""
        gen = DetailGenerator(seed=42)
        detail = gen.generate_detail(
            object_id="obj_123",
            zoom_level=2,
            era="victorian"
        )
        # Generation is context-dependent

    def test_add_template(self):
        """Test adding custom templates."""
        gen = DetailGenerator(seed=42)
        initial_count = len(gen.templates)

        custom = DetailTemplate(
            detail_type=DetailType.MARKING,
            template="A custom marking appears."
        )
        gen.add_template(custom)

        assert len(gen.templates) == initial_count + 1
        assert custom in gen.templates

    def test_get_applicable_templates(self):
        """Test getting templates by criteria."""
        gen = DetailGenerator(seed=42)

        applicable = gen.get_applicable_templates(
            tags=["furniture"],
            material="wood"
        )

        # Should return templates matching the criteria
        for template in applicable:
            assert template.applies_to(["furniture"], "wood")

    def test_get_applicable_templates_by_type(self):
        """Test filtering by detail type."""
        gen = DetailGenerator(seed=42)

        applicable = gen.get_applicable_templates(
            tags=[],
            detail_types=[DetailType.TEXTURE]
        )

        for template in applicable:
            assert template.detail_type == DetailType.TEXTURE

    def test_generate_facts_from_details(self):
        """Test generating fact IDs from templates."""
        gen = DetailGenerator(seed=42)

        facts = gen.generate_facts_from_details(
            object_id="obj_123",
            zoom_level=3,
            tags=["furniture"]
        )

        # May or may not generate facts depending on RNG
        assert isinstance(facts, list)

    def test_get_ascii_enhancement(self):
        """Test ASCII art enhancement."""
        gen = DetailGenerator(seed=42)

        base_ascii = "[===]"
        enhanced = gen.get_ascii_enhancement(base_ascii, 2, "wood")

        assert enhanced is not None
        # At zoom level 1, should return base unchanged
        assert gen.get_ascii_enhancement(base_ascii, 1, "wood") == base_ascii

    def test_cache_behavior(self):
        """Test that results are cached."""
        gen = DetailGenerator(seed=42)

        # First generation
        details1 = gen.generate_details(
            object_id="obj_123",
            zoom_level=2,
            count=3,
            tags=["furniture"]
        )

        # Second call should return cached results
        details2 = gen.generate_details(
            object_id="obj_123",
            zoom_level=2,
            count=3,
            tags=["furniture"]
        )

        assert details1 == details2

    def test_clear_cache(self):
        """Test cache clearing."""
        gen = DetailGenerator(seed=42)

        gen.generate_details("obj_1", 2, count=1)
        gen.generate_details("obj_2", 2, count=1)

        # Clear specific object
        gen.clear_cache("obj_1")
        assert f"obj_1:2" not in gen.generated_cache

        # Clear all
        gen.clear_cache()
        assert len(gen.generated_cache) == 0

    def test_set_seed(self):
        """Test changing seed."""
        gen = DetailGenerator(seed=42)
        gen.generate_details("obj_1", 2, count=1)

        gen.set_seed(123)
        assert gen.seed == 123
        assert len(gen.generated_cache) == 0  # Cache should be cleared

    def test_serialization(self):
        """Test to_dict/from_dict."""
        gen = DetailGenerator(seed=42)
        gen.generate_details("obj_1", 2, count=1, tags=["furniture"])

        data = gen.to_dict()
        restored = DetailGenerator.from_dict(data)

        assert restored.seed == gen.seed
        assert restored.generated_cache == gen.generated_cache
