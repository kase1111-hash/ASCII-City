"""
World State - Maintains consistent context for LLM generation.

Tracks generated locations, NPCs, events, and story elements
to ensure the LLM maintains consistency across the game world.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import json


class StoryThread(Enum):
    """Active narrative threads the player can follow."""
    MAIN_MYSTERY = "main_mystery"
    SIDE_QUEST = "side_quest"
    CHARACTER_STORY = "character_story"
    WORLD_EVENT = "world_event"
    EXPLORATION = "exploration"


@dataclass
class DialogueMemory:
    """Record of a generated dialogue exchange."""
    npc_id: str
    player_said: str
    npc_response: str
    location_id: str
    topics_mentioned: list[str] = field(default_factory=list)
    revealed_info: Optional[str] = None
    timestamp: int = 0


@dataclass
class GenerationMemory:
    """
    Tracks all LLM-generated content for consistency.

    This ensures the LLM can reference what it said before
    and maintain consistency across conversations and locations.
    """

    # Dialogue history per NPC
    npc_dialogues: dict[str, list[DialogueMemory]] = field(default_factory=dict)

    # Generated descriptions per location (beyond initial description)
    location_details: dict[str, list[str]] = field(default_factory=dict)

    # Items/objects that were generated and their properties
    generated_items: dict[str, dict] = field(default_factory=dict)

    # Clues and information revealed during gameplay
    revealed_clues: list[dict] = field(default_factory=list)

    # Narrative elements generated (rumors, backstories, etc.)
    generated_lore: list[dict] = field(default_factory=list)

    def record_dialogue(self, npc_id: str, player_said: str, npc_response: str,
                       location_id: str, topics: list[str] = None,
                       revealed: str = None, timestamp: int = 0) -> None:
        """Record a dialogue exchange."""
        if npc_id not in self.npc_dialogues:
            self.npc_dialogues[npc_id] = []

        memory = DialogueMemory(
            npc_id=npc_id,
            player_said=player_said,
            npc_response=npc_response,
            location_id=location_id,
            topics_mentioned=topics or [],
            revealed_info=revealed,
            timestamp=timestamp
        )
        self.npc_dialogues[npc_id].append(memory)

    def get_npc_dialogue_history(self, npc_id: str, limit: int = 5) -> str:
        """Get recent dialogue history for an NPC."""
        if npc_id not in self.npc_dialogues:
            return ""

        recent = self.npc_dialogues[npc_id][-limit:]
        lines = []
        for mem in recent:
            lines.append(f"Player asked: \"{mem.player_said}\"")
            lines.append(f"You said: \"{mem.npc_response}\"")
            if mem.revealed_info:
                lines.append(f"(Revealed: {mem.revealed_info})")
        return "\n".join(lines)

    def record_location_detail(self, location_id: str, detail: str) -> None:
        """Record a generated detail about a location."""
        if location_id not in self.location_details:
            self.location_details[location_id] = []
        self.location_details[location_id].append(detail)

    def get_location_details(self, location_id: str) -> list[str]:
        """Get all generated details about a location."""
        return self.location_details.get(location_id, [])

    def record_item(self, item_id: str, properties: dict) -> None:
        """Record a generated item and its properties."""
        self.generated_items[item_id] = properties

    def record_clue(self, clue: str, source: str, location: str, related_to: list[str] = None) -> None:
        """Record a revealed clue."""
        self.revealed_clues.append({
            "clue": clue,
            "source": source,
            "location": location,
            "related_to": related_to or []
        })

    def record_lore(self, lore_type: str, content: str, source: str) -> None:
        """Record generated lore/backstory."""
        self.generated_lore.append({
            "type": lore_type,
            "content": content,
            "source": source
        })

    def get_relevant_lore(self, keywords: list[str], limit: int = 3) -> list[str]:
        """Get lore relevant to given keywords."""
        relevant = []
        for lore in self.generated_lore:
            content = lore["content"].lower()
            if any(kw.lower() in content for kw in keywords):
                relevant.append(lore["content"])
        return relevant[:limit]

    def to_dict(self) -> dict:
        """Serialize for saving."""
        return {
            "npc_dialogues": {
                npc_id: [{
                    "npc_id": d.npc_id,
                    "player_said": d.player_said,
                    "npc_response": d.npc_response,
                    "location_id": d.location_id,
                    "topics_mentioned": d.topics_mentioned,
                    "revealed_info": d.revealed_info,
                    "timestamp": d.timestamp
                } for d in dialogues]
                for npc_id, dialogues in self.npc_dialogues.items()
            },
            "location_details": self.location_details,
            "generated_items": self.generated_items,
            "revealed_clues": self.revealed_clues,
            "generated_lore": self.generated_lore
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationMemory":
        """Deserialize from saved data."""
        mem = cls()

        for npc_id, dialogues in data.get("npc_dialogues", {}).items():
            mem.npc_dialogues[npc_id] = [
                DialogueMemory(
                    npc_id=d["npc_id"],
                    player_said=d["player_said"],
                    npc_response=d["npc_response"],
                    location_id=d["location_id"],
                    topics_mentioned=d.get("topics_mentioned", []),
                    revealed_info=d.get("revealed_info"),
                    timestamp=d.get("timestamp", 0)
                ) for d in dialogues
            ]

        mem.location_details = data.get("location_details", {})
        mem.generated_items = data.get("generated_items", {})
        mem.revealed_clues = data.get("revealed_clues", [])
        mem.generated_lore = data.get("generated_lore", [])

        return mem


@dataclass
class GeneratedNPC:
    """Record of an LLM-generated NPC."""
    id: str
    name: str
    location_id: str
    description: str
    archetype: str
    secret: str
    public_persona: str
    topics: list[str] = field(default_factory=list)
    relationships: dict[str, str] = field(default_factory=dict)  # npc_id -> relationship
    mentioned_in: list[str] = field(default_factory=list)  # location_ids where they're mentioned


@dataclass
class GeneratedLocation:
    """Record of an LLM-generated location."""
    id: str
    name: str
    location_type: str
    description: str
    is_outdoor: bool
    connections: dict[str, str] = field(default_factory=dict)  # direction -> description
    npcs: list[str] = field(default_factory=list)  # NPC IDs present here
    items_found: list[str] = field(default_factory=list)
    clues_found: list[str] = field(default_factory=list)
    generated_from: Optional[str] = None  # What location/direction this was generated from


@dataclass
class WorldEvent:
    """A significant event that occurred in the world."""
    id: str
    description: str
    location_id: str
    involved_npcs: list[str] = field(default_factory=list)
    timestamp: int = 0  # Game time when it occurred
    is_public: bool = True  # Whether NPCs generally know about this


@dataclass
class StoryFact:
    """A fact established in the narrative."""
    id: str
    fact: str
    source: str  # How this was established (NPC dialogue, location description, etc.)
    related_npcs: list[str] = field(default_factory=list)
    related_locations: list[str] = field(default_factory=list)
    is_secret: bool = False  # True if player discovered this through investigation


class WorldState:
    """
    Maintains world consistency for procedural generation.

    This is the central context that gets passed to the LLM
    to ensure new generations are consistent with what exists.
    """

    def __init__(self):
        # Generated content tracking
        self.locations: dict[str, GeneratedLocation] = {}
        self.npcs: dict[str, GeneratedNPC] = {}
        self.events: list[WorldEvent] = []
        self.facts: list[StoryFact] = []

        # Memory of all LLM-generated content
        self.generation_memory: GenerationMemory = GenerationMemory()

        # Active narrative threads
        self.active_threads: dict[str, dict] = {}  # thread_id -> thread_data
        self.main_mystery: Optional[dict] = None

        # World rules and constraints
        self.world_genre: str = "noir mystery"
        self.world_era: str = "1940s"
        self.world_rules: list[str] = []

        # Geographic relationships
        self.region_map: dict[str, list[str]] = {}  # region_name -> location_ids

    def register_location(self, location_data: dict) -> None:
        """Register a newly generated location."""
        loc = GeneratedLocation(
            id=location_data.get("id", "unknown"),
            name=location_data.get("name", "Unknown Location"),
            location_type=location_data.get("location_type", "generic"),
            description=location_data.get("description", ""),
            is_outdoor=location_data.get("is_outdoor", True),
            connections=location_data.get("connections", {}),
            generated_from=location_data.get("generated_from")
        )
        self.locations[loc.id] = loc

    def register_npc(self, npc_data: dict, location_id: str) -> None:
        """Register a newly generated NPC."""
        npc = GeneratedNPC(
            id=npc_data.get("id", "unknown"),
            name=npc_data.get("name", "Stranger"),
            location_id=location_id,
            description=npc_data.get("description", ""),
            archetype=npc_data.get("archetype", "survivor"),
            secret=npc_data.get("secret", ""),
            public_persona=npc_data.get("public_persona", ""),
            topics=npc_data.get("topics", [])
        )
        self.npcs[npc.id] = npc

        # Update location's NPC list
        if location_id in self.locations:
            self.locations[location_id].npcs.append(npc.id)

    def add_npc_relationship(self, npc_id: str, other_npc_id: str, relationship: str) -> None:
        """Add a relationship between two NPCs."""
        if npc_id in self.npcs:
            self.npcs[npc_id].relationships[other_npc_id] = relationship
        # Relationships are bidirectional with inverse
        if other_npc_id in self.npcs:
            inverse_map = {
                "knows": "knows",
                "friend": "friend",
                "enemy": "enemy",
                "employer": "employee",
                "employee": "employer",
                "family": "family",
                "lover": "lover",
                "rival": "rival",
            }
            inverse = inverse_map.get(relationship, "knows")
            self.npcs[other_npc_id].relationships[npc_id] = inverse

    def record_event(self, event_id: str, description: str, location_id: str,
                     npcs: list[str] = None, game_time: int = 0, is_public: bool = True) -> None:
        """Record a significant world event."""
        event = WorldEvent(
            id=event_id,
            description=description,
            location_id=location_id,
            involved_npcs=npcs or [],
            timestamp=game_time,
            is_public=is_public
        )
        self.events.append(event)

    def add_fact(self, fact_id: str, fact: str, source: str,
                 npcs: list[str] = None, locations: list[str] = None, is_secret: bool = False) -> None:
        """Add an established narrative fact."""
        story_fact = StoryFact(
            id=fact_id,
            fact=fact,
            source=source,
            related_npcs=npcs or [],
            related_locations=locations or [],
            is_secret=is_secret
        )
        self.facts.append(story_fact)

    def set_main_mystery(self, mystery_data: dict) -> None:
        """Set the main mystery for the narrative."""
        self.main_mystery = mystery_data

    def add_story_thread(self, thread_id: str, thread_type: StoryThread, data: dict) -> None:
        """Add an active story thread."""
        self.active_threads[thread_id] = {
            "type": thread_type.value,
            "data": data,
            "active": True
        }

    def resolve_thread(self, thread_id: str, resolution: str) -> None:
        """Mark a story thread as resolved."""
        if thread_id in self.active_threads:
            self.active_threads[thread_id]["active"] = False
            self.active_threads[thread_id]["resolution"] = resolution

    def get_location_context(self, location_id: str) -> dict:
        """Get context for a specific location."""
        if location_id not in self.locations:
            return {}

        loc = self.locations[location_id]
        npcs_here = [self.npcs[npc_id] for npc_id in loc.npcs if npc_id in self.npcs]

        return {
            "location": {
                "id": loc.id,
                "name": loc.name,
                "type": loc.location_type,
                "description": loc.description,
                "connections": loc.connections
            },
            "npcs": [{
                "name": npc.name,
                "description": npc.description,
                "topics": npc.topics
            } for npc in npcs_here],
            "events_here": [e.description for e in self.events if e.location_id == location_id],
            "items_found": loc.items_found,
            "clues_found": loc.clues_found
        }

    def get_npc_context(self, npc_id: str) -> dict:
        """Get context for a specific NPC."""
        if npc_id not in self.npcs:
            return {}

        npc = self.npcs[npc_id]

        # Get their relationships
        relationships = []
        for other_id, rel in npc.relationships.items():
            if other_id in self.npcs:
                relationships.append(f"{rel} of {self.npcs[other_id].name}")

        # Get events they were involved in
        involved_events = [e.description for e in self.events if npc_id in e.involved_npcs]

        return {
            "npc": {
                "name": npc.name,
                "location": npc.location_id,
                "description": npc.description,
                "archetype": npc.archetype,
                "topics": npc.topics,
                "public_persona": npc.public_persona
            },
            "relationships": relationships,
            "events_involved": involved_events,
            "mentioned_in": npc.mentioned_in
        }

    def get_world_context_for_generation(self, context_type: str = "location") -> str:
        """
        Generate a context string for LLM generation.

        This is the key method that provides consistency information
        to the LLM when generating new content.
        """
        context_parts = []

        # World setting
        context_parts.append(f"WORLD SETTING: {self.world_genre}, {self.world_era}")
        if self.world_rules:
            context_parts.append("World rules: " + "; ".join(self.world_rules))

        # Main mystery context
        if self.main_mystery:
            mystery_ctx = []
            if "victim" in self.main_mystery:
                mystery_ctx.append(f"Victim: {self.main_mystery['victim']}")
            if "crime" in self.main_mystery:
                mystery_ctx.append(f"Crime: {self.main_mystery['crime']}")
            if "suspects" in self.main_mystery:
                mystery_ctx.append(f"Known suspects: {', '.join(self.main_mystery['suspects'])}")
            if mystery_ctx:
                context_parts.append("MAIN MYSTERY: " + "; ".join(mystery_ctx))

        # Existing locations summary
        if self.locations:
            loc_summaries = []
            for loc_id, loc in list(self.locations.items())[-10:]:  # Last 10 locations
                loc_summaries.append(f"- {loc.name} ({loc.location_type})")
            context_parts.append("KNOWN LOCATIONS:\n" + "\n".join(loc_summaries))

        # Key NPCs summary
        if self.npcs:
            npc_summaries = []
            for npc_id, npc in list(self.npcs.items())[-8:]:  # Last 8 NPCs
                npc_summaries.append(f"- {npc.name} ({npc.archetype}) at {npc.location_id}")
            context_parts.append("KNOWN CHARACTERS:\n" + "\n".join(npc_summaries))

        # Recent events
        recent_events = self.events[-5:] if self.events else []
        if recent_events:
            event_summaries = [f"- {e.description}" for e in recent_events]
            context_parts.append("RECENT EVENTS:\n" + "\n".join(event_summaries))

        # Established facts (non-secret)
        public_facts = [f for f in self.facts if not f.is_secret][-5:]
        if public_facts:
            fact_summaries = [f"- {f.fact}" for f in public_facts]
            context_parts.append("ESTABLISHED FACTS:\n" + "\n".join(fact_summaries))

        # Active story threads
        active = [t for t in self.active_threads.values() if t.get("active")]
        if active:
            thread_summaries = []
            for t in active[:3]:  # Top 3 active threads
                if "description" in t.get("data", {}):
                    thread_summaries.append(f"- {t['data']['description']}")
            if thread_summaries:
                context_parts.append("ACTIVE STORY THREADS:\n" + "\n".join(thread_summaries))

        return "\n\n".join(context_parts)

    def get_npc_knowledge(self, npc_id: str) -> str:
        """
        Get what a specific NPC would know about the world.

        Used to inform NPC dialogue - they only know about
        public events and things related to them.
        """
        if npc_id not in self.npcs:
            return ""

        npc = self.npcs[npc_id]
        knowledge_parts = []

        # Their location
        if npc.location_id in self.locations:
            loc = self.locations[npc.location_id]
            knowledge_parts.append(f"You are at {loc.name}")

        # People they know
        if npc.relationships:
            relationships = []
            for other_id, rel in npc.relationships.items():
                if other_id in self.npcs:
                    relationships.append(f"{self.npcs[other_id].name} ({rel})")
            if relationships:
                knowledge_parts.append("You know: " + ", ".join(relationships))

        # Public events they'd know about
        public_events = [e for e in self.events if e.is_public or npc_id in e.involved_npcs]
        if public_events:
            event_knowledge = [e.description for e in public_events[-3:]]
            knowledge_parts.append("You've heard: " + "; ".join(event_knowledge))

        # Facts related to them
        related_facts = [f for f in self.facts if npc_id in f.related_npcs and not f.is_secret]
        if related_facts:
            fact_knowledge = [f.fact for f in related_facts[-2:]]
            knowledge_parts.append("You know: " + "; ".join(fact_knowledge))

        return "\n".join(knowledge_parts)

    def to_dict(self) -> dict:
        """Serialize world state for saving."""
        return {
            "locations": {lid: {
                "id": loc.id,
                "name": loc.name,
                "location_type": loc.location_type,
                "description": loc.description,
                "is_outdoor": loc.is_outdoor,
                "connections": loc.connections,
                "npcs": loc.npcs,
                "items_found": loc.items_found,
                "clues_found": loc.clues_found,
                "generated_from": loc.generated_from
            } for lid, loc in self.locations.items()},
            "npcs": {nid: {
                "id": npc.id,
                "name": npc.name,
                "location_id": npc.location_id,
                "description": npc.description,
                "archetype": npc.archetype,
                "secret": npc.secret,
                "public_persona": npc.public_persona,
                "topics": npc.topics,
                "relationships": npc.relationships,
                "mentioned_in": npc.mentioned_in
            } for nid, npc in self.npcs.items()},
            "events": [{
                "id": e.id,
                "description": e.description,
                "location_id": e.location_id,
                "involved_npcs": e.involved_npcs,
                "timestamp": e.timestamp,
                "is_public": e.is_public
            } for e in self.events],
            "facts": [{
                "id": f.id,
                "fact": f.fact,
                "source": f.source,
                "related_npcs": f.related_npcs,
                "related_locations": f.related_locations,
                "is_secret": f.is_secret
            } for f in self.facts],
            "active_threads": self.active_threads,
            "main_mystery": self.main_mystery,
            "world_genre": self.world_genre,
            "world_era": self.world_era,
            "world_rules": self.world_rules,
            "region_map": self.region_map
        }

    def adapt_narrative(self, player_location: str, distance_from_start: int) -> dict:
        """
        Adapt the narrative based on player exploration.

        Returns guidance for the LLM on how to connect new content
        back to the main story or create new narrative threads.
        """
        adaptation = {
            "should_connect_to_main": True,
            "connection_strength": "strong",
            "suggested_threads": [],
            "narrative_guidance": ""
        }

        # If player is far from starting area, weaken main mystery connection
        if distance_from_start > 5:
            adaptation["connection_strength"] = "weak"
            adaptation["narrative_guidance"] = (
                "The player has wandered far from the main mystery. "
                "New content can hint at the main story but should also "
                "introduce new mysteries or adventures that stand alone."
            )
        elif distance_from_start > 10:
            adaptation["should_connect_to_main"] = False
            adaptation["connection_strength"] = "none"
            adaptation["narrative_guidance"] = (
                "The player is exploring freely. Create self-contained "
                "adventures. The main mystery can be a distant rumor "
                "or completely absent. Let the player discover new stories."
            )

        # Check if location type suggests different narrative
        if player_location and player_location in self.locations:
            loc = self.locations[player_location]
            loc_type = loc.location_type.lower()

            # Wilderness locations = adventure narrative
            if loc_type in ["wilderness", "forest", "mountain", "desert", "arctic"]:
                adaptation["suggested_threads"].append({
                    "type": "adventure",
                    "description": "survival, exploration, discovery of ancient secrets"
                })

            # Exotic locations = mystery or wonder
            if "space" in loc_type or "fantasy" in loc_type or "ancient" in loc_type:
                adaptation["suggested_threads"].append({
                    "type": "wonder",
                    "description": "strange phenomena, alien/magical encounters, cosmic mystery"
                })

        # Suggest tying back to main mystery if active threads exist
        active_threads = [t for t in self.active_threads.values() if t.get("active")]
        if active_threads and adaptation["should_connect_to_main"]:
            adaptation["suggested_threads"].append({
                "type": "callback",
                "description": "reference to the main mystery - a clue, a connection, a shared enemy"
            })

        return adaptation

    def get_narrative_prompt_addition(self, player_location: str, distance: int) -> str:
        """
        Get additional prompt text to guide narrative adaptation.

        This is injected into location generation prompts.
        """
        adaptation = self.adapt_narrative(player_location, distance)

        lines = ["NARRATIVE ADAPTATION:"]

        if adaptation["connection_strength"] == "strong":
            lines.append("- Connect this location to the main mystery")
            if self.main_mystery:
                lines.append(f"- Reference the victim ({self.main_mystery.get('victim', 'unknown')})")
                lines.append("- NPCs here might have heard rumors about the crime")
        elif adaptation["connection_strength"] == "weak":
            lines.append("- Light connection to main mystery (distant rumor, vague reference)")
            lines.append("- Focus on local stories and characters")
        else:
            lines.append("- No connection to main mystery needed")
            lines.append("- Create a self-contained story for this area")

        if adaptation["suggested_threads"]:
            lines.append("SUGGESTED STORY ELEMENTS:")
            for thread in adaptation["suggested_threads"]:
                lines.append(f"- {thread['type']}: {thread['description']}")

        if adaptation["narrative_guidance"]:
            lines.append(f"\nGUIDANCE: {adaptation['narrative_guidance']}")

        return "\n".join(lines)

    def create_story_branch(self, branch_id: str, description: str,
                           branch_type: StoryThread, origin_location: str) -> None:
        """
        Create a new story branch when the player discovers something significant.

        Story branches are mini-narratives that can run parallel to the main mystery.
        """
        self.add_story_thread(branch_id, branch_type, {
            "description": description,
            "origin": origin_location,
            "discovered_at": len(self.events),  # Use event count as rough timestamp
            "resolved": False
        })

    def check_for_story_convergence(self) -> Optional[str]:
        """
        Check if multiple story threads can converge.

        Returns a narrative hint if threads should merge.
        """
        active = [tid for tid, t in self.active_threads.items() if t.get("active")]

        if len(active) >= 2:
            # If we have multiple active threads, suggest convergence
            return (
                "Multiple story threads are active. Consider having them intersect - "
                "perhaps a character from one thread knows something about another."
            )

        return None

    @classmethod
    def from_dict(cls, data: dict) -> "WorldState":
        """Deserialize world state from saved data."""
        ws = cls()

        # Restore locations
        for lid, loc_data in data.get("locations", {}).items():
            ws.locations[lid] = GeneratedLocation(
                id=loc_data["id"],
                name=loc_data["name"],
                location_type=loc_data["location_type"],
                description=loc_data["description"],
                is_outdoor=loc_data["is_outdoor"],
                connections=loc_data.get("connections", {}),
                npcs=loc_data.get("npcs", []),
                items_found=loc_data.get("items_found", []),
                clues_found=loc_data.get("clues_found", []),
                generated_from=loc_data.get("generated_from")
            )

        # Restore NPCs
        for nid, npc_data in data.get("npcs", {}).items():
            ws.npcs[nid] = GeneratedNPC(
                id=npc_data["id"],
                name=npc_data["name"],
                location_id=npc_data["location_id"],
                description=npc_data["description"],
                archetype=npc_data["archetype"],
                secret=npc_data.get("secret", ""),
                public_persona=npc_data.get("public_persona", ""),
                topics=npc_data.get("topics", []),
                relationships=npc_data.get("relationships", {}),
                mentioned_in=npc_data.get("mentioned_in", [])
            )

        # Restore events
        for e_data in data.get("events", []):
            ws.events.append(WorldEvent(
                id=e_data["id"],
                description=e_data["description"],
                location_id=e_data["location_id"],
                involved_npcs=e_data.get("involved_npcs", []),
                timestamp=e_data.get("timestamp", 0),
                is_public=e_data.get("is_public", True)
            ))

        # Restore facts
        for f_data in data.get("facts", []):
            ws.facts.append(StoryFact(
                id=f_data["id"],
                fact=f_data["fact"],
                source=f_data["source"],
                related_npcs=f_data.get("related_npcs", []),
                related_locations=f_data.get("related_locations", []),
                is_secret=f_data.get("is_secret", False)
            ))

        ws.active_threads = data.get("active_threads", {})
        ws.main_mystery = data.get("main_mystery")
        ws.world_genre = data.get("world_genre", "noir mystery")
        ws.world_era = data.get("world_era", "1940s")
        ws.world_rules = data.get("world_rules", [])
        ws.region_map = data.get("region_map", {})

        return ws
