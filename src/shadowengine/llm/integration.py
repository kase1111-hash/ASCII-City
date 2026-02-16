"""
LLM Integration - Connects LLM to game systems.

Provides high-level interfaces for dialogue generation,
behavior evaluation, and narrative generation.
"""

import json
from dataclasses import dataclass
from typing import Optional, Tuple

from .client import LLMClient, LLMConfig, create_llm_client
from .prompts import CharacterPrompt, NarrativePrompt, BehaviorPrompt


@dataclass
class DialogueResult:
    """Result from dialogue generation."""
    text: str
    success: bool
    mood_shift: float = 0.0  # -1.0 to 1.0
    reveals_info: bool = False
    fallback_used: bool = False


@dataclass
class BehaviorResult:
    """Result from behavior evaluation."""
    action: str
    intensity: float
    target: Optional[str] = None
    narrative: str = ""
    success: bool = True


class DialogueGenerator:
    """Generates character dialogue using LLM."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or create_llm_client()
        self.fallback_responses = {
            "default": [
                "I've got nothing to say to you.",
                "Why don't you ask someone else?",
                "That's none of your business.",
                "I don't know anything about that.",
            ],
            "nervous": [
                "I-I don't know what you're talking about.",
                "Please, just leave me alone.",
                "Why are you asking me?",
            ],
            "hostile": [
                "Get lost.",
                "I'm done talking.",
                "You're asking the wrong questions.",
            ],
            "cooperative": [
                "I wish I could help more.",
                "That's all I know, honestly.",
                "I've told you everything.",
            ]
        }

    def generate(
        self,
        character_prompt: CharacterPrompt,
        question: str,
        location: str = "unknown",
        time: str = "evening",
        topics_discussed: Optional[list] = None,
        evidence: Optional[list] = None
    ) -> DialogueResult:
        """Generate character dialogue response."""

        if not self.client.is_available:
            return self._fallback_response(character_prompt.mood)

        system = character_prompt.get_system_prompt()
        prompt = character_prompt.get_response_prompt(
            question=question,
            location=location,
            time=time,
            topics_discussed=topics_discussed,
            evidence=evidence
        )

        response = self.client.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ])

        if not response.success:
            return self._fallback_response(character_prompt.mood)

        return DialogueResult(
            text=response.text.strip(),
            success=True,
            mood_shift=0.0,
            reveals_info=self._check_reveals_info(response.text, character_prompt.secret_truth)
        )

    def _fallback_response(self, mood: str) -> DialogueResult:
        """Get a fallback response when LLM is unavailable."""
        import random

        mood_category = "default"
        if mood in ["nervous", "scared", "worried"]:
            mood_category = "nervous"
        elif mood in ["angry", "hostile", "suspicious"]:
            mood_category = "hostile"
        elif mood in ["friendly", "open", "helpful"]:
            mood_category = "cooperative"

        responses = self.fallback_responses.get(mood_category, self.fallback_responses["default"])
        return DialogueResult(
            text=random.choice(responses),
            success=True,
            fallback_used=True
        )

    def _check_reveals_info(self, response: str, secret: str) -> bool:
        """Check if response reveals secret information."""
        if not secret:
            return False
        # Filter out common stop words before comparing
        stop_words = {
            "i", "me", "my", "the", "a", "an", "is", "was", "were", "are",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "it", "its", "he", "she", "his", "her", "they", "them", "their",
            "this", "that", "and", "but", "or", "not", "no", "so", "if",
            "about", "up", "out", "just", "than", "very", "can", "into",
        }
        secret_words = set(secret.lower().split()) - stop_words
        response_words = set(response.lower().split()) - stop_words
        if not secret_words:
            return False
        overlap = secret_words & response_words
        # If more than 50% of meaningful secret words appear, consider it revealed
        return len(overlap) / len(secret_words) > 0.5


class BehaviorEvaluator:
    """Evaluates NPC behavior using LLM."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or create_llm_client()
        self.prompt_generator = BehaviorPrompt()

    def evaluate(
        self,
        npc_name: str,
        npc_type: str,
        personality: str,
        state: str,
        stimulus: str,
        distance: float,
        threat_level: float,
        time: str = "night",
        nearby_npcs: Optional[list] = None
    ) -> BehaviorResult:
        """Evaluate what behavior an NPC should exhibit."""

        if not self.client.is_available:
            return self._fallback_behavior(personality, threat_level)

        system = self.prompt_generator.get_system_prompt()
        prompt = self.prompt_generator.get_evaluation_prompt(
            npc_name=npc_name,
            npc_type=npc_type,
            personality=personality,
            state=state,
            stimulus=stimulus,
            distance=distance,
            threat_level=threat_level,
            time=time,
            nearby_npcs=nearby_npcs or []
        )

        response = self.client.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ])

        if not response.success:
            return self._fallback_behavior(personality, threat_level)

        return self._parse_behavior_response(response.text)

    def _parse_behavior_response(self, text: str) -> BehaviorResult:
        """Parse LLM response into BehaviorResult."""
        try:
            # Try to extract JSON from response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return BehaviorResult(
                    action=data.get("action", "ignore"),
                    intensity=float(data.get("intensity", 0.5)),
                    target=data.get("target"),
                    narrative=data.get("narrative", ""),
                    success=True
                )
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: try to extract action from text
        text_lower = text.lower()
        for action in ["flee", "hide", "approach", "alert", "investigate", "ignore"]:
            if action in text_lower:
                return BehaviorResult(action=action, intensity=0.5, success=True)

        return BehaviorResult(action="ignore", intensity=0.3, success=True)

    def _fallback_behavior(self, personality: str, threat_level: float) -> BehaviorResult:
        """Determine fallback behavior based on personality and threat."""
        personality_lower = personality.lower()

        if threat_level > 0.7:
            if "coward" in personality_lower or "nervous" in personality_lower:
                return BehaviorResult(action="flee", intensity=0.9)
            elif "brave" in personality_lower or "aggressive" in personality_lower:
                return BehaviorResult(action="approach", intensity=0.8)
            else:
                return BehaviorResult(action="hide", intensity=0.6)
        elif threat_level > 0.3:
            return BehaviorResult(action="investigate", intensity=0.5)
        else:
            return BehaviorResult(action="ignore", intensity=0.2)


class LLMIntegration:
    """
    Main integration class connecting LLM to game systems.

    Usage:
        integration = LLMIntegration()
        if integration.is_available:
            response = integration.generate_dialogue(character, question)
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.client = create_llm_client(config)
        self.dialogue_generator = DialogueGenerator(self.client)
        self.behavior_evaluator = BehaviorEvaluator(self.client)
        self.narrative_prompt = NarrativePrompt()

    @property
    def is_available(self) -> bool:
        """Check if LLM backend is available."""
        return self.client.is_available

    def generate_dialogue(
        self,
        name: str,
        description: str,
        archetype: str,
        trust: int,
        mood: str,
        secret_truth: str,
        public_lie: str,
        question: str,
        **context
    ) -> DialogueResult:
        """Generate character dialogue."""
        prompt = CharacterPrompt(
            name=name,
            description=description,
            archetype=archetype,
            trust=trust,
            mood=mood,
            secret_truth=secret_truth,
            public_lie=public_lie
        )
        return self.dialogue_generator.generate(prompt, question, **context)

    def evaluate_behavior(self, **kwargs) -> BehaviorResult:
        """Evaluate NPC behavior."""
        return self.behavior_evaluator.evaluate(**kwargs)

    def generate_narrative(
        self,
        location: str,
        time: str,
        weather: str,
        characters: list[str],
        events: list[str],
        action: str
    ) -> str:
        """Generate narrative description."""
        if not self.is_available:
            return self._fallback_narrative(location, action)

        system = self.narrative_prompt.get_system_prompt()
        prompt = self.narrative_prompt.get_scene_prompt(
            location=location,
            time=time,
            weather=weather,
            characters=characters,
            events=events,
            action=action
        )

        response = self.client.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ])

        if response.success:
            return response.text.strip()
        return self._fallback_narrative(location, action)

    def _fallback_narrative(self, location: str, action: str) -> str:
        """Simple fallback narrative."""
        return f"You {action}. The {location} feels quiet and watchful."

    def get_circuit_evaluator(self):
        """
        Get an evaluator function compatible with CircuitProcessor.

        Returns a callable that can be passed to CircuitProcessor.set_llm_evaluator()
        """
        def evaluator(circuit, signal, context) -> Tuple[list, str]:
            # Use behavior evaluator for circuit signals
            result = self.evaluate_behavior(
                npc_name=circuit.id,
                npc_type=str(circuit.circuit_type.value) if hasattr(circuit, 'circuit_type') else "entity",
                personality="neutral",
                state=str(circuit.state) if hasattr(circuit, 'state') else "idle",
                stimulus=str(signal.signal_type.value) if hasattr(signal, 'signal_type') else "unknown",
                distance=context.player_distance if hasattr(context, 'player_distance') else 10.0,
                threat_level=signal.intensity if hasattr(signal, 'intensity') else 0.5,
                time=str(context.time_of_day) if hasattr(context, 'time_of_day') else "night"
            )

            # Convert to circuit output format
            outputs = []  # Would create OutputSignals based on result.action
            narrative = result.narrative or f"The entity responds with {result.action}."

            return outputs, narrative

        return evaluator
