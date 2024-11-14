"""
LLM Management System

This module provides a framework for managing and interacting with multiple
large language model (LLM) providers. It includes support for configuration,
provider switching, and dynamic instance creation. Supported providers include
Ollama, OpenAI, and Anthropic.
"""

from enum import Enum
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core.llms import LLM as LlamaLLM
import os


class LLMProvider(Enum):
    """
    Enumeration of supported LLM providers.

    Attributes:
        OLLAMA: Represents the Ollama LLM provider.
        OPENAI: Represents the OpenAI LLM provider.
        ANTHROPIC: Represents the Anthropic LLM provider.
    """

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class BaseLLMConfig(ABC):
    """
    Abstract base class for LLM configuration.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        pass


class OllamaConfig(BaseLLMConfig):
    """
    Configuration class for the Ollama LLM.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        temperature: float = 0.7,
        request_timeout: float = 120.0,
    ):
        self.model = model
        self.temperature = temperature
        self.request_timeout = request_timeout

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "request_timeout": self.request_timeout,
        }


class OpenAIConfig(BaseLLMConfig):
    """
    Configuration class for the OpenAI LLM.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def to_dict(self) -> Dict[str, Any]:
        config = {
            "model": self.model,
            "api_key": self.api_key,
            "temperature": self.temperature,
        }
        if self.max_tokens:
            config["max_tokens"] = self.max_tokens
        return config


class AnthropicConfig(BaseLLMConfig):
    """
    Configuration class for the Anthropic LLM.
    """

    def __init__(
        self,
        model: str = "claude-3-5-haiku-latest",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def to_dict(self) -> Dict[str, Any]:
        config = {
            "model": self.model,
            "api_key": self.api_key,
            "temperature": self.temperature,
        }
        if self.max_tokens:
            config["max_tokens"] = self.max_tokens
        return config


class LLMFactory:
    """
    Factory class for creating LLM instances.
    """

    @staticmethod
    def create(
        provider: LLMProvider,
        config: BaseLLMConfig,
    ) -> LlamaLLM:
        """
        Create an LLM instance based on the provider and configuration.

        Args:
            provider (LLMProvider): The LLM provider to use.
            config (BaseLLMConfig): The configuration for the LLM.

        Returns:
            LlamaLLM: An instance of the specified LLM.

        Raises:
            ValueError: If the configuration type does not match the provider.
        """
        if provider == LLMProvider.OLLAMA:
            if not isinstance(config, OllamaConfig):
                raise ValueError("Config must be OllamaConfig for Ollama provider")
            return Ollama(**config.to_dict())

        elif provider == LLMProvider.OPENAI:
            if not isinstance(config, OpenAIConfig):
                raise ValueError("Config must be OpenAIConfig for OpenAI provider")
            return OpenAI(**config.to_dict())

        elif provider == LLMProvider.ANTHROPIC:
            if not isinstance(config, AnthropicConfig):
                raise ValueError(
                    "Config must be AnthropicConfig for Anthropic provider"
                )
            return Anthropic(**config.to_dict())

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


class LLMManager:
    """
    Manager class for handling LLM operations.
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OLLAMA,
        config: Optional[BaseLLMConfig] = None,
    ):
        """
        Initialize the LLMManager.

        Args:
            provider (LLMProvider): The LLM provider to use. Defaults to Ollama.
            config (Optional[BaseLLMConfig]): Configuration for the LLM. If None, a default configuration will be used.
        """
        if config is None:
            if provider == LLMProvider.OLLAMA:
                config = OllamaConfig()
            elif provider == LLMProvider.OPENAI:
                config = OpenAIConfig()
            elif provider == LLMProvider.ANTHROPIC:
                config = AnthropicConfig()

        self.provider = provider
        self.config = config
        self.llm = LLMFactory.create(provider, config)

    def update_config(self, new_config: BaseLLMConfig):
        """
        Update the LLM configuration and recreate the instance.

        Args:
            new_config (BaseLLMConfig): The new configuration for the LLM.
        """
        self.config = new_config
        self.llm = LLMFactory.create(self.provider, new_config)

    def switch_provider(
        self, new_provider: LLMProvider, new_config: Optional[BaseLLMConfig] = None
    ):
        """
        Switch to a different LLM provider.

        Args:
            new_provider (LLMProvider): The new LLM provider to switch to.
            new_config (Optional[BaseLLMConfig]): Optional new configuration for the provider.
        """
        self.provider = new_provider
        if new_config:
            self.config = new_config
        else:
            # Create default config for the new provider
            if new_provider == LLMProvider.OLLAMA:
                self.config = OllamaConfig()
            elif new_provider == LLMProvider.OPENAI:
                self.config = OpenAIConfig()
            elif new_provider == LLMProvider.ANTHROPIC:
                self.config = AnthropicConfig()

        self.llm = LLMFactory.create(new_provider, self.config)

    def get_llm(self) -> LlamaLLM:
        """
        Get the current LLM instance.

        Returns:
            LlamaLLM: The current LLM instance.
        """
        return self.llm
