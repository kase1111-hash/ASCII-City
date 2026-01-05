# Module 11: ASCII Art Studio

## Overview

The ASCII Art Studio is a revolutionary system where player creativity becomes world content. Players create ASCII art that gets semantically tagged, interpreted by the LLM, and injected into the procedural world with appropriate affordances.

---

## Studio Concept

### Core Philosophy

- **Player as Creator**: Art isn't cosmetic—it becomes actual world content
- **Iterative Learning**: Usage feedback improves generation
- **Community Building**: Share assets, visit others' worlds
- **Semantic Understanding**: LLM interprets meaning, not just appearance

### Entering the Studio

Players access the studio from within the game world:

```
> enter studio

You push open the door marked "Creator's Workshop."
Inside, easels and canvases line the walls. An ASCII
grid glows softly on the central workbench.

[Studio Mode Active]
Commands: draw, tag, preview, save, gallery, exit
```

---

## ASCII Art Structure

```python
class ASCIIArt:
    id: str                       # Unique identifier
    name: str                     # Display name
    tiles: list[list[str]]        # 2D character array

    # Semantic classification
    tags: ArtTags

    # Metadata
    player_id: str                # Creator
    version: int                  # Iteration count
    created_at: datetime
    updated_at: datetime

    # Usage tracking
    usage_stats: UsageStats

    # Rendering hints
    animation: Animation | None   # Optional animation data
    color_hints: dict | None      # Optional color suggestions
```

### Semantic Tags

```python
class ArtTags:
    # Primary classification
    object_type: ObjectType       # tree, rock, NPC, item, structure

    # Interaction properties
    interaction_types: list[str]  # climbable, collectible, hideable

    # Environment context
    environment_types: list[str]  # forest, urban, cave, river

    # Size and placement
    size: Size                    # small, medium, large, multi_tile
    placement: Placement          # floor, wall, ceiling, floating

    # Optional semantic details
    mood: str | None              # ominous, friendly, mysterious
    era: str | None               # medieval, futuristic, timeless
    material: str | None          # wood, stone, metal, organic
```

---

## Creation Workflow

### Step 1: Drawing

```
> draw tree

[Drawing Mode - Tree]
Size: 5x7 tiles
Use arrow keys to move, characters to draw.
Press Enter when done.

    *
   ***
  *****
   ***
   |||
   |||
  =====
```

### Step 2: Tagging

```
> tag

Object Type: tree
Interaction Types:
  [x] climbable
  [x] harvestable
  [ ] hideable
  [x] flammable
Environment:
  [x] forest
  [x] park
  [ ] cave

Additional tags: deciduous, autumn, tall
```

### Step 3: LLM Interpretation

The LLM analyzes the art and tags to understand semantic meaning:

```python
def interpret_art(art: ASCIIArt) -> ArtInterpretation:
    """LLM interprets the submitted art."""

    prompt = f"""
    Analyze this ASCII art:
    ```
    {render_tiles(art.tiles)}
    ```

    Player tags: {art.tags}

    Determine:
    1. What this represents (validate against tags)
    2. Appropriate affordances based on appearance
    3. Suggested behavioral circuit properties
    4. Procedural variants that could be generated
    5. Appropriate placement contexts

    Output: interpretation with confidence scores
    """

    return llm.evaluate(prompt)
```

### Step 4: Variant Generation

The LLM generates procedural variants:

```python
def generate_variants(art: ASCIIArt, count: int) -> list[ASCIIArt]:
    """Generate procedural variants of player art."""

    variants = []

    for i in range(count):
        prompt = f"""
        Original ASCII art (tree):
        ```
        {render_tiles(art.tiles)}
        ```

        Generate variant #{i+1}:
        - Maintain recognizable identity
        - Vary size slightly ({random_size_modifier()})
        - Adjust details (different branch patterns)
        - Keep semantic meaning intact

        Output: ASCII art grid
        """

        variant_tiles = llm.generate(prompt)
        variants.append(create_variant(art, variant_tiles, i))

    return variants
```

---

## World Integration

### Asset Pool

Player art enters the world asset pool:

```python
class AssetPool:
    def __init__(self):
        self.assets: dict[str, list[ASCIIArt]] = {}

    def add_asset(self, art: ASCIIArt):
        """Add art to appropriate category pools."""
        for env in art.tags.environment_types:
            self.assets.setdefault(env, []).append(art)

    def get_assets(self, environment: str, object_type: str) -> list[ASCIIArt]:
        """Get matching assets for world generation."""
        return [
            a for a in self.assets.get(environment, [])
            if a.tags.object_type == object_type
        ]
```

### Procedural Placement

World generator uses player assets:

```python
def generate_forest_tile(grid, position, asset_pool):
    """Generate a forest tile using available assets."""

    # Get forest-appropriate trees
    trees = asset_pool.get_assets("forest", "tree")

    if trees:
        # Select based on usage stats (prefer underused)
        tree = weighted_select(trees, weight_by_freshness)
    else:
        # Fall back to default
        tree = DEFAULT_TREE

    # Place with affordances from tags
    place_entity(grid, position, tree, tree.tags.interaction_types)

    # Track usage
    tree.usage_stats.times_rendered += 1
```

### Affordance Inheritance

Art inherits affordances from its tags:

```python
def create_entity_from_art(art: ASCIIArt, position: Position) -> Entity:
    """Create a world entity from ASCII art."""

    entity = Entity(
        id=generate_id(),
        art=art,
        position=position
    )

    # Build affordances from tags
    affordances = []
    for interaction in art.tags.interaction_types:
        affordances.append(interaction)

    # Add material-based affordances
    if art.tags.material == "wood":
        affordances.extend(["flammable", "breakable"])
    elif art.tags.material == "stone":
        affordances.extend(["solid", "heavy"])

    entity.affordances = affordances

    return entity
```

---

## Feedback Loop

### Usage Tracking

```python
class UsageStats:
    times_rendered: int           # How often placed in world
    interactions_triggered: int   # Player interactions with this
    player_ratings: list[int]     # 1-5 star ratings
    variants_generated: int       # How many variants exist

    def quality_score(self) -> float:
        """Calculate overall quality score."""
        if self.times_rendered == 0:
            return 0.5  # Neutral for unused

        engagement = self.interactions_triggered / self.times_rendered
        rating = sum(self.player_ratings) / len(self.player_ratings) if self.player_ratings else 3.0

        return (engagement * 0.4) + ((rating / 5) * 0.6)
```

### Improvement Suggestions

LLM can suggest improvements:

```python
def suggest_improvements(art: ASCIIArt) -> list[Suggestion]:
    """Suggest improvements based on usage data."""

    if art.usage_stats.quality_score() < 0.3:
        prompt = f"""
        This ASCII art has low engagement:
        ```
        {render_tiles(art.tiles)}
        ```

        Tags: {art.tags}
        Interactions: {art.usage_stats.interactions_triggered}
        Renders: {art.usage_stats.times_rendered}

        Suggest improvements:
        1. Visual clarity enhancements
        2. Tag adjustments
        3. Affordance additions
        4. Placement context changes
        """

        return llm.evaluate(prompt)

    return []
```

---

## Gallery Mode

### Viewing Other Creations

```
> gallery

=== Community Gallery ===

[Popular This Week]
1. Gothic Castle (by ShadowMaker) ★★★★★
2. Cyberpunk Terminal (by NeonDreams) ★★★★☆
3. Ancient Oak (by ForestWalker) ★★★★★

[Recently Added]
4. Crystal Cave (by GemHunter)
5. Street Lamp (by CityScribe)

Commands: view <number>, import <number>, filter <tag>
```

### Importing Assets

```python
def import_asset(art: ASCIIArt, player_id: str) -> ASCIIArt:
    """Import another player's asset into your pool."""

    imported = ASCIIArt(
        id=generate_id(),
        name=art.name,
        tiles=art.tiles.copy(),
        tags=art.tags.copy(),
        player_id=player_id,  # New owner
        original_creator=art.player_id,
        version=1
    )

    # Credit original creator
    imported.metadata["imported_from"] = art.id

    return imported
```

---

## Animation Support

Optional animation for dynamic assets:

```python
class Animation:
    frames: list[list[list[str]]]  # Multiple tile grids
    frame_duration: float          # Seconds per frame
    loop: bool                     # Repeat animation
    trigger: str | None            # When to play (always, on_interact, on_weather)

# Example: Flickering torch
torch_animation = Animation(
    frames=[
        [["*"], ["|"]],            # Frame 1
        [["'"], ["|"]],            # Frame 2
        [["*"], ["|"]],            # Frame 3
    ],
    frame_duration=0.3,
    loop=True,
    trigger="always"
)
```

---

## Serialization

```python
def serialize_art(art: ASCIIArt) -> dict:
    return {
        "id": art.id,
        "name": art.name,
        "tiles": art.tiles,
        "tags": art.tags.to_dict(),
        "player_id": art.player_id,
        "version": art.version,
        "usage_stats": art.usage_stats.to_dict(),
        "animation": art.animation.to_dict() if art.animation else None
    }

def deserialize_art(data: dict) -> ASCIIArt:
    return ASCIIArt(
        id=data["id"],
        name=data["name"],
        tiles=data["tiles"],
        tags=ArtTags.from_dict(data["tags"]),
        player_id=data["player_id"],
        version=data["version"],
        usage_stats=UsageStats.from_dict(data["usage_stats"]),
        animation=Animation.from_dict(data["animation"]) if data["animation"] else None
    )
```

---

## Integration Points

- **Behavioral Circuits** (Module 08): Art entities use circuits
- **Tile Grid** (Module 09): Art placed on grid tiles
- **ASCII Renderer** (Module 05): Art rendered in scenes
- **Narrative Spine** (Module 01): Significant player art can affect story
- **Memory Bank** (Module 03): Player art preferences tracked
