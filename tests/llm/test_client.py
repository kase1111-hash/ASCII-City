"""Tests for LLM client implementations."""

import pytest
from shadowengine.llm import (
    LLMConfig,
    LLMBackend,
    LLMResponse,
    MockLLMClient,
    OllamaClient,
    OpenAIClient,
    create_llm_client,
)


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.backend == LLMBackend.OLLAMA
        assert config.model == "llama3.2"
        assert config.base_url == "http://localhost:11434"
        assert config.temperature == 0.7
        assert config.max_tokens == 256

    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("LLM_BACKEND", "mock")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.5")
        monkeypatch.setenv("LLM_MAX_TOKENS", "100")

        config = LLMConfig.from_env()
        assert config.backend == LLMBackend.MOCK
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 100

    def test_invalid_backend_defaults_to_ollama(self, monkeypatch):
        """Test that invalid backend defaults to Ollama."""
        monkeypatch.setenv("LLM_BACKEND", "invalid")
        config = LLMConfig.from_env()
        assert config.backend == LLMBackend.OLLAMA


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_success_response(self):
        """Test successful response creation."""
        response = LLMResponse(text="Hello", success=True, model="test")
        assert response.text == "Hello"
        assert response.success
        assert response.error is None

    def test_error_response(self):
        """Test error response creation."""
        response = LLMResponse.error_response("Connection failed")
        assert response.text == ""
        assert not response.success
        assert response.error == "Connection failed"


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    def test_always_available(self):
        """Test that mock client is always available."""
        client = MockLLMClient(LLMConfig())
        assert client.is_available
        assert client.check_availability()

    def test_default_response(self):
        """Test default response."""
        client = MockLLMClient(LLMConfig())
        response = client.generate("Tell me something")
        assert response.success
        assert response.text == "I don't have much to say about that."

    def test_keyword_response(self):
        """Test keyword-based response."""
        client = MockLLMClient(LLMConfig(), responses={
            "watch": "The watch was stolen last night."
        })
        response = client.generate("Tell me about the watch")
        assert response.success
        assert response.text == "The watch was stolen last night."

    def test_set_response(self):
        """Test setting a response."""
        client = MockLLMClient(LLMConfig())
        client.set_response("butler", "The butler did it.")

        response = client.generate("Who is the butler?")
        assert response.text == "The butler did it."

    def test_call_history(self):
        """Test that call history is recorded."""
        client = MockLLMClient(LLMConfig())
        client.generate("First question")
        client.generate("Second question")

        assert len(client.call_history) == 2
        assert "First question" in client.call_history
        assert "Second question" in client.call_history

    def test_chat_method(self):
        """Test chat method."""
        client = MockLLMClient(LLMConfig(), responses={"hello": "Hi there!"})
        response = client.chat([
            {"role": "user", "content": "Hello!"}
        ])
        assert response.success
        assert response.text == "Hi there!"


class TestOllamaClient:
    """Tests for OllamaClient."""

    def test_availability_check_when_offline(self):
        """Test availability check when Ollama is not running."""
        config = LLMConfig(base_url="http://localhost:99999")
        client = OllamaClient(config)
        # Should not raise, just return False
        assert not client.check_availability()

    def test_generate_when_offline(self):
        """Test generate returns error when Ollama is offline."""
        config = LLMConfig(base_url="http://localhost:99999", timeout=1)
        client = OllamaClient(config)
        response = client.generate("Hello")
        assert not response.success
        assert response.error is not None


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    def test_no_api_key(self):
        """Test that client reports unavailable without API key."""
        config = LLMConfig(backend=LLMBackend.OPENAI, api_key=None)
        client = OpenAIClient(config)
        assert not client.is_available

    def test_generate_without_key(self):
        """Test generate returns error without API key."""
        config = LLMConfig(backend=LLMBackend.OPENAI, api_key=None)
        client = OpenAIClient(config)
        response = client.generate("Hello")
        assert not response.success
        assert "API key" in response.error

    def test_model_default(self):
        """Test that non-GPT model defaults to gpt-3.5-turbo."""
        config = LLMConfig(backend=LLMBackend.OPENAI, model="llama3.2")
        client = OpenAIClient(config)
        assert client.config.model == "gpt-3.5-turbo"


class TestCreateLLMClient:
    """Tests for create_llm_client factory."""

    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        config = LLMConfig(backend=LLMBackend.OLLAMA)
        client = create_llm_client(config)
        assert isinstance(client, OllamaClient)

    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        config = LLMConfig(backend=LLMBackend.OPENAI)
        client = create_llm_client(config)
        assert isinstance(client, OpenAIClient)

    def test_create_mock_client(self):
        """Test creating mock client."""
        config = LLMConfig(backend=LLMBackend.MOCK)
        client = create_llm_client(config)
        assert isinstance(client, MockLLMClient)

    def test_default_creates_ollama(self):
        """Test that default config creates Ollama client."""
        client = create_llm_client()
        assert isinstance(client, OllamaClient)
