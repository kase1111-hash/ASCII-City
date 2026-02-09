"""
LLM Client - Ollama and OpenAI API integration.

Provides unified interface for language model backends.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import urllib.request
import urllib.error


class LLMBackend(Enum):
    """Supported LLM backends."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    backend: LLMBackend = LLMBackend.OLLAMA
    model: str = "llama3.2"  # Default Ollama model
    base_url: str = "http://localhost:11434"  # Ollama default
    api_key: Optional[str] = None  # For OpenAI
    temperature: float = 0.7
    max_tokens: int = 256
    timeout: int = 30
    system_prompt: str = "You are a character in a noir mystery game. Respond in character."

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables."""
        backend_str = os.environ.get("LLM_BACKEND", "ollama").lower()
        backend = LLMBackend(backend_str) if backend_str in [b.value for b in LLMBackend] else LLMBackend.OLLAMA

        return cls(
            backend=backend,
            model=os.environ.get("LLM_MODEL", "llama3.2"),
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "256")),
            timeout=int(os.environ.get("LLM_TIMEOUT", "30")),
        )


@dataclass
class LLMResponse:
    """Response from LLM."""
    text: str
    success: bool = True
    error: Optional[str] = None
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0

    @classmethod
    def error_response(cls, error: str) -> "LLMResponse":
        """Create an error response."""
        return cls(text="", success=False, error=error)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._available: Optional[bool] = None

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        """Generate a response from the LLM."""

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the LLM backend is available."""

    @property
    def is_available(self) -> bool:
        """Check availability (cached)."""
        if self._available is None:
            self._available = self.check_availability()
        return self._available

    def chat(self, messages: list[dict]) -> LLMResponse:
        """Chat with message history. Default implementation uses generate."""
        # Convert messages to a single prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                continue  # Handle separately
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"User: {content}")

        system = next((m["content"] for m in messages if m.get("role") == "system"), None)
        prompt = "\n".join(prompt_parts) + "\nAssistant:"

        return self.generate(prompt, system=system)


class OllamaClient(LLMClient):
    """Ollama LLM client for local inference."""

    def check_availability(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            url = f"{self.config.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                return self.config.model.split(":")[0] in models or len(models) > 0
        except Exception:
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        """Generate response using Ollama API."""
        import time
        start = time.time()

        url = f"{self.config.base_url}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }

        if system:
            payload["system"] = system

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode())
                latency = (time.time() - start) * 1000

                return LLMResponse(
                    text=result.get("response", ""),
                    success=True,
                    model=result.get("model", self.config.model),
                    tokens_used=result.get("eval_count", 0),
                    latency_ms=latency
                )

        except urllib.error.URLError as e:
            return LLMResponse.error_response(f"Connection error: {e}")
        except urllib.error.HTTPError as e:
            return LLMResponse.error_response(f"HTTP error {e.code}: {e.reason}")
        except json.JSONDecodeError as e:
            return LLMResponse.error_response(f"Invalid JSON response: {e}")
        except Exception as e:
            return LLMResponse.error_response(f"Unexpected error: {e}")

    def chat(self, messages: list[dict]) -> LLMResponse:
        """Chat using Ollama's chat endpoint."""
        import time
        start = time.time()

        url = f"{self.config.base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode())
                latency = (time.time() - start) * 1000

                message = result.get("message", {})
                return LLMResponse(
                    text=message.get("content", ""),
                    success=True,
                    model=result.get("model", self.config.model),
                    tokens_used=result.get("eval_count", 0),
                    latency_ms=latency
                )

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            # Log the specific error and fall back to generate endpoint
            import logging
            logging.warning(f"Ollama chat endpoint failed ({type(e).__name__}), falling back to generate: {e}")
            return super().chat(messages)
        except Exception as e:
            import logging
            logging.error(f"Unexpected error in Ollama chat: {type(e).__name__}: {e}")
            return LLMResponse.error_response(f"Unexpected error: {e}")


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if config.base_url == "http://localhost:11434":
            # Override with OpenAI URL if using default Ollama URL
            self.config.base_url = "https://api.openai.com/v1"
        if not config.model.startswith("gpt"):
            self.config.model = "gpt-3.5-turbo"

    def check_availability(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.config.api_key:
            return False
        try:
            url = f"{self.config.base_url}/models"
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        """Generate using OpenAI chat completions."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)

    def chat(self, messages: list[dict]) -> LLMResponse:
        """Chat using OpenAI API."""
        import time
        start = time.time()

        if not self.config.api_key:
            return LLMResponse.error_response("No API key configured")

        url = f"{self.config.base_url}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode())
                latency = (time.time() - start) * 1000

                choice = result.get("choices", [{}])[0]
                message = choice.get("message", {})
                usage = result.get("usage", {})

                return LLMResponse(
                    text=message.get("content", ""),
                    success=True,
                    model=result.get("model", self.config.model),
                    tokens_used=usage.get("total_tokens", 0),
                    latency_ms=latency
                )

        except urllib.error.HTTPError as e:
            return LLMResponse.error_response(f"API error {e.code}: {e.reason}")
        except Exception as e:
            return LLMResponse.error_response(f"Error: {e}")


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self, config: LLMConfig, responses: Optional[dict] = None):
        super().__init__(config)
        self.responses = responses or {}
        self.call_history: list[str] = []
        self.default_response = "I don't have much to say about that."

    def check_availability(self) -> bool:
        """Mock is always available."""
        return True

    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        """Return mock response."""
        self.call_history.append(prompt)

        # Check for keyword matches in responses
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt.lower():
                return LLMResponse(
                    text=response,
                    success=True,
                    model="mock",
                    tokens_used=len(response.split()),
                    latency_ms=1.0
                )

        return LLMResponse(
            text=self.default_response,
            success=True,
            model="mock",
            tokens_used=len(self.default_response.split()),
            latency_ms=1.0
        )

    def set_response(self, keyword: str, response: str) -> None:
        """Set a response for a keyword."""
        self.responses[keyword] = response


def create_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Create an LLM client based on configuration."""
    if config is None:
        config = LLMConfig.from_env()

    if config.backend == LLMBackend.OLLAMA:
        return OllamaClient(config)
    elif config.backend == LLMBackend.OPENAI:
        return OpenAIClient(config)
    else:
        return MockLLMClient(config)
