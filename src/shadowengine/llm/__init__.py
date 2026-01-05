"""
LLM Integration Module - Ollama and API Support.

Provides language model integration for dynamic NPC responses,
narrative generation, and intelligent game behavior.

Supported backends:
- Ollama (local, recommended)
- OpenAI API (cloud)
- Mock (for testing)
"""

from .client import (
    LLMClient,
    LLMResponse,
    LLMConfig,
    LLMBackend,
    OllamaClient,
    OpenAIClient,
    MockLLMClient,
    create_llm_client,
)

from .prompts import (
    PromptTemplate,
    CharacterPrompt,
    NarrativePrompt,
    BehaviorPrompt,
)

from .integration import (
    LLMIntegration,
    DialogueGenerator,
    BehaviorEvaluator,
)

__all__ = [
    # Client
    "LLMClient",
    "LLMResponse",
    "LLMConfig",
    "LLMBackend",
    "OllamaClient",
    "OpenAIClient",
    "MockLLMClient",
    "create_llm_client",
    # Prompts
    "PromptTemplate",
    "CharacterPrompt",
    "NarrativePrompt",
    "BehaviorPrompt",
    # Integration
    "LLMIntegration",
    "DialogueGenerator",
    "BehaviorEvaluator",
]
