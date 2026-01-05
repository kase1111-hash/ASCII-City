"""
DetailGenerator - Procedural micro-detail generation.

Generates contextually appropriate details for objects when
the player zooms in closer. Uses templates and randomization
to create coherent, surprising discoveries.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import random
import hashlib


class DetailType(Enum):
    """Types of generated details."""
    TEXTURE = "texture"             # Surface texture description
    WEAR = "wear"                   # Signs of age/use
    MARKING = "marking"             # Writing, symbols, scratches
    HIDDEN = "hidden"               # Hidden compartments, features
    MATERIAL = "material"           # Material composition details
    MECHANISM = "mechanism"         # Moving parts, workings
    RESIDUE = "residue"             # Stains, dust, residue
    INSCRIPTION = "inscription"     # Engraved or carved text
    DAMAGE = "damage"               # Damage, cracks, repairs
    CRAFTSMANSHIP = "craftsmanship" # Quality of construction


@dataclass
class DetailTemplate:
    """
    A template for generating details.

    Templates can include placeholders for:
    - {material} - The object's material
    - {era} - The object's era
    - {adjective} - A random appropriate adjective
    - {noun} - A random appropriate noun
    """
    detail_type: DetailType
    template: str
    tags: list[str] = field(default_factory=list)      # Required object tags
    materials: list[str] = field(default_factory=list)  # Applicable materials
    significance: float = 0.5       # How significant (0-1)
    reveals_fact: bool = False      # Can reveal a fact
    fact_template: Optional[str] = None  # Template for fact ID

    def applies_to(
        self,
        tags: list[str],
        material: Optional[str] = None
    ) -> bool:
        """Check if this template applies to an object."""
        # Check required tags
        if self.tags:
            if not any(t in tags for t in self.tags):
                return False

        # Check material compatibility
        if self.materials and material:
            if material not in self.materials:
                return False

        return True

    def generate(
        self,
        rng: random.Random,
        material: Optional[str] = None,
        era: Optional[str] = None,
        extra_context: dict = None
    ) -> str:
        """Generate a detail from this template."""
        extra_context = extra_context or {}

        # Build replacement dict
        replacements = {
            "material": material or "unknown material",
            "era": era or "old",
            "adjective": rng.choice(ADJECTIVES.get(self.detail_type, ["notable"])),
            "noun": rng.choice(NOUNS.get(self.detail_type, ["feature"])),
        }
        replacements.update(extra_context)

        result = self.template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result


# Adjectives for different detail types
ADJECTIVES = {
    DetailType.TEXTURE: [
        "rough", "smooth", "pitted", "polished", "weathered",
        "grainy", "striated", "mottled", "glossy", "dull"
    ],
    DetailType.WEAR: [
        "faded", "worn", "rubbed", "scuffed", "eroded",
        "thinned", "discolored", "patinated", "corroded"
    ],
    DetailType.MARKING: [
        "faint", "deep", "precise", "crude", "deliberate",
        "accidental", "mysterious", "familiar", "ancient"
    ],
    DetailType.HIDDEN: [
        "concealed", "secret", "disguised", "subtle", "ingenious",
        "obvious-in-hindsight", "cleverly-hidden"
    ],
    DetailType.MATERIAL: [
        "pure", "alloyed", "composite", "layered", "treated",
        "natural", "processed", "rare"
    ],
    DetailType.MECHANISM: [
        "intricate", "simple", "elegant", "crude", "precise",
        "delicate", "robust", "worn"
    ],
    DetailType.RESIDUE: [
        "faint", "obvious", "sticky", "dried", "fresh",
        "old", "suspicious", "mundane"
    ],
    DetailType.INSCRIPTION: [
        "elegant", "hurried", "careful", "faded", "deep",
        "ornate", "simple", "cryptic"
    ],
    DetailType.DAMAGE: [
        "minor", "significant", "repaired", "fresh", "old",
        "deliberate", "accidental", "structural"
    ],
    DetailType.CRAFTSMANSHIP: [
        "exquisite", "crude", "professional", "amateur",
        "masterful", "hasty", "careful", "unique"
    ],
}

# Nouns for different detail types
NOUNS = {
    DetailType.TEXTURE: [
        "surface", "finish", "grain", "pattern", "texture"
    ],
    DetailType.WEAR: [
        "marks", "spots", "areas", "patches", "signs"
    ],
    DetailType.MARKING: [
        "scratches", "marks", "symbols", "lines", "patterns"
    ],
    DetailType.HIDDEN: [
        "compartment", "mechanism", "panel", "catch", "spring"
    ],
    DetailType.MECHANISM: [
        "gears", "springs", "levers", "hinges", "catches"
    ],
    DetailType.RESIDUE: [
        "residue", "traces", "deposits", "stains", "dust"
    ],
    DetailType.INSCRIPTION: [
        "lettering", "text", "words", "symbols", "markings"
    ],
    DetailType.DAMAGE: [
        "crack", "chip", "dent", "scratch", "break"
    ],
}


# Predefined detail templates
DETAIL_TEMPLATES = [
    # Texture details
    DetailTemplate(
        detail_type=DetailType.TEXTURE,
        template="The surface shows a {adjective} {noun}, suggesting {era} origins.",
        tags=["furniture", "statue", "tool"],
        significance=0.3
    ),
    DetailTemplate(
        detail_type=DetailType.TEXTURE,
        template="Running your fingers across it, you feel {adjective} imperfections in the {material}.",
        materials=["wood", "metal", "stone"],
        significance=0.3
    ),

    # Wear details
    DetailTemplate(
        detail_type=DetailType.WEAR,
        template="There are {adjective} {noun} where hands have touched it countless times.",
        tags=["tool", "door", "handle"],
        significance=0.4
    ),
    DetailTemplate(
        detail_type=DetailType.WEAR,
        template="One corner shows {adjective} wear, as if frequently rubbed or bumped.",
        significance=0.3
    ),

    # Marking details
    DetailTemplate(
        detail_type=DetailType.MARKING,
        template="You notice {adjective} {noun} barely visible on the underside.",
        significance=0.5,
        reveals_fact=True,
        fact_template="marking_on_{object_id}"
    ),
    DetailTemplate(
        detail_type=DetailType.MARKING,
        template="Someone has scratched {adjective} initials into the surface.",
        significance=0.6,
        reveals_fact=True,
        fact_template="initials_on_{object_id}"
    ),

    # Hidden details
    DetailTemplate(
        detail_type=DetailType.HIDDEN,
        template="There's a {adjective} {noun} here - almost impossible to see without looking closely.",
        tags=["furniture", "box", "desk"],
        significance=0.8,
        reveals_fact=True,
        fact_template="hidden_{noun}_in_{object_id}"
    ),
    DetailTemplate(
        detail_type=DetailType.HIDDEN,
        template="A {adjective} seam suggests this might open or move somehow.",
        tags=["furniture", "wall", "floor"],
        significance=0.7,
        reveals_fact=True
    ),

    # Material details
    DetailTemplate(
        detail_type=DetailType.MATERIAL,
        template="The {material} is of {adjective} quality - {era} craftsmanship.",
        significance=0.4
    ),
    DetailTemplate(
        detail_type=DetailType.MATERIAL,
        template="Closer inspection reveals this isn't solid {material}, but a {adjective} veneer.",
        materials=["wood", "metal"],
        significance=0.5,
        reveals_fact=True
    ),

    # Mechanism details
    DetailTemplate(
        detail_type=DetailType.MECHANISM,
        template="You can just make out {adjective} {noun} through a small gap.",
        tags=["clock", "lock", "device"],
        significance=0.5
    ),
    DetailTemplate(
        detail_type=DetailType.MECHANISM,
        template="The mechanism contains {adjective} components - clearly {era} technology.",
        tags=["device", "machine", "clock"],
        significance=0.4
    ),

    # Residue details
    DetailTemplate(
        detail_type=DetailType.RESIDUE,
        template="There's {adjective} {noun} in the crevices - could be {era}.",
        significance=0.4
    ),
    DetailTemplate(
        detail_type=DetailType.RESIDUE,
        template="A {adjective} stain mars one corner - something was spilled here.",
        significance=0.5,
        reveals_fact=True,
        fact_template="stain_on_{object_id}"
    ),

    # Inscription details
    DetailTemplate(
        detail_type=DetailType.INSCRIPTION,
        template="There's {adjective} {noun} engraved here, barely legible.",
        significance=0.6,
        reveals_fact=True,
        fact_template="inscription_on_{object_id}"
    ),
    DetailTemplate(
        detail_type=DetailType.INSCRIPTION,
        template="A maker's mark in {adjective} script identifies the craftsman.",
        tags=["tool", "furniture", "weapon"],
        significance=0.5,
        reveals_fact=True
    ),

    # Damage details
    DetailTemplate(
        detail_type=DetailType.DAMAGE,
        template="There's a {adjective} {noun} that's been skillfully repaired.",
        significance=0.5,
        reveals_fact=True,
        fact_template="repaired_{noun}_on_{object_id}"
    ),
    DetailTemplate(
        detail_type=DetailType.DAMAGE,
        template="A {adjective} {noun} mars the surface - {era} damage from the look of it.",
        significance=0.4
    ),

    # Craftsmanship details
    DetailTemplate(
        detail_type=DetailType.CRAFTSMANSHIP,
        template="The {adjective} workmanship suggests a {era} master craftsman.",
        significance=0.3
    ),
    DetailTemplate(
        detail_type=DetailType.CRAFTSMANSHIP,
        template="You notice {adjective} attention to detail in the joinery and finish.",
        materials=["wood"],
        significance=0.3
    ),
]


class DetailGenerator:
    """
    Generates procedural micro-details for inspection.

    Uses templates, material/era context, and deterministic
    randomization to create coherent details.
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**32)
        self.templates = DETAIL_TEMPLATES.copy()
        self.generated_cache: dict[str, list[str]] = {}

    def _get_rng(self, object_id: str, zoom_level: int) -> random.Random:
        """Get a deterministic RNG for an object and zoom level."""
        # Create deterministic seed from object ID and zoom
        seed_str = f"{self.seed}:{object_id}:{zoom_level}"
        seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        return random.Random(seed_hash)

    def add_template(self, template: DetailTemplate) -> None:
        """Add a custom template."""
        self.templates.append(template)

    def get_applicable_templates(
        self,
        tags: list[str],
        material: Optional[str] = None,
        detail_types: list[DetailType] = None
    ) -> list[DetailTemplate]:
        """Get templates that apply to an object."""
        applicable = []
        for template in self.templates:
            if not template.applies_to(tags, material):
                continue
            if detail_types and template.detail_type not in detail_types:
                continue
            applicable.append(template)
        return applicable

    def generate_detail(
        self,
        object_id: str,
        zoom_level: int,
        tags: list[str] = None,
        material: Optional[str] = None,
        era: Optional[str] = None,
        detail_types: list[DetailType] = None,
        extra_context: dict = None
    ) -> Optional[str]:
        """Generate a single detail for an object."""
        tags = tags or []
        rng = self._get_rng(object_id, zoom_level)

        applicable = self.get_applicable_templates(tags, material, detail_types)
        if not applicable:
            return None

        template = rng.choice(applicable)
        context = extra_context or {}
        context["object_id"] = object_id

        return template.generate(rng, material, era, context)

    def generate_details(
        self,
        object_id: str,
        zoom_level: int,
        count: int = 1,
        tags: list[str] = None,
        material: Optional[str] = None,
        era: Optional[str] = None,
        extra_context: dict = None
    ) -> list[str]:
        """Generate multiple details for an object."""
        # Check cache
        cache_key = f"{object_id}:{zoom_level}"
        if cache_key in self.generated_cache:
            return self.generated_cache[cache_key][:count]

        tags = tags or []
        rng = self._get_rng(object_id, zoom_level)
        applicable = self.get_applicable_templates(tags, material)

        if not applicable:
            return []

        # Generate unique details
        details = []
        used_types = set()

        for _ in range(min(count, len(applicable))):
            # Try to use different detail types
            remaining = [t for t in applicable if t.detail_type not in used_types]
            if not remaining:
                remaining = applicable

            template = rng.choice(remaining)
            used_types.add(template.detail_type)

            context = extra_context or {}
            context["object_id"] = object_id

            detail = template.generate(rng, material, era, context)
            details.append(detail)

        # Cache results
        self.generated_cache[cache_key] = details

        return details

    def generate_facts_from_details(
        self,
        object_id: str,
        zoom_level: int,
        tags: list[str] = None,
        material: Optional[str] = None
    ) -> list[str]:
        """Generate fact IDs from applicable templates."""
        tags = tags or []
        rng = self._get_rng(object_id, zoom_level)
        applicable = self.get_applicable_templates(tags, material)

        facts = []
        for template in applicable:
            if template.reveals_fact and template.fact_template:
                # Deterministically decide if this template reveals a fact
                if rng.random() < template.significance:
                    fact_id = template.fact_template.format(
                        object_id=object_id,
                        noun=rng.choice(NOUNS.get(template.detail_type, ["detail"]))
                    )
                    facts.append(fact_id)

        return facts

    def get_ascii_enhancement(
        self,
        base_ascii: str,
        zoom_level: int,
        material: Optional[str] = None
    ) -> str:
        """Enhance ASCII art based on zoom level."""
        if zoom_level <= 1:
            return base_ascii

        # Add detail characters based on zoom level
        detail_chars = {
            "wood": ["~", "=", "-"],
            "metal": ["*", ".", "+"],
            "stone": [".", ":", "'"],
            "fabric": ['"', "'", ","],
        }

        chars = detail_chars.get(material, [".", "'", "`"])

        # Simple enhancement: add detail characters
        if zoom_level >= 2:
            # Could enhance ASCII art here
            pass

        return base_ascii

    def clear_cache(self, object_id: Optional[str] = None) -> None:
        """Clear generation cache."""
        if object_id:
            keys_to_remove = [k for k in self.generated_cache if k.startswith(f"{object_id}:")]
            for key in keys_to_remove:
                del self.generated_cache[key]
        else:
            self.generated_cache.clear()

    def set_seed(self, seed: int) -> None:
        """Set the generator seed and clear cache."""
        self.seed = seed
        self.clear_cache()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "seed": self.seed,
            "generated_cache": self.generated_cache
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DetailGenerator':
        """Deserialize from dictionary."""
        generator = cls(seed=data.get("seed"))
        generator.generated_cache = data.get("generated_cache", {})
        return generator
