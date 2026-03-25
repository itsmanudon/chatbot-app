"""
llm_adapter.py
--------------
Provider-agnostic abstraction layer for LLM response generation.

Architecture
~~~~~~~~~~~~
``AIProvider`` (abstract base class)
    Defines the ``generate_response`` interface.  Concrete subclasses must
    implement this method.

``OpenAIProvider``
    Wraps the OpenAI Python SDK.  Uses ``gpt-3.5-turbo`` with
    ``temperature=0.7`` and ``max_tokens=500``.  Injects retrieved context as
    a system message prepended to the conversation history.

``AnthropicProvider``
    Wraps the Anthropic Python SDK.  Uses ``claude-3-haiku-20240307`` with
    ``max_tokens=500``.  Context is prepended to the ``system`` parameter of
    the Messages API.

``LLMAdapter``
    Manages the two providers and exposes a unified ``get_response`` method.
    The active provider is selected via the ``DEFAULT_AI_PROVIDER`` environment
    variable (default ``"openai"``).  A different provider can be requested
    per-call via the optional ``provider`` argument.

Graceful degradation
~~~~~~~~~~~~~~~~~~~~
If the required API key is absent or the SDK fails to initialise,
``is_available()`` returns ``False`` and ``generate_response`` returns a
human-readable error string instead of raising an exception.

Environment variables
~~~~~~~~~~~~~~~~~~~~~
``OPENAI_API_KEY``
    Required for the OpenAI provider.
``ANTHROPIC_API_KEY``
    Required for the Anthropic provider.
``DEFAULT_AI_PROVIDER``
    ``"openai"`` (default) or ``"anthropic"``.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from abc import ABC, abstractmethod

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from logging_config import get_logger

logger = get_logger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All concrete providers must implement :meth:`generate_response`.
    """

    @abstractmethod
    def generate_response(
        self, messages: list[dict[str, str]], context: str = ""
    ) -> str:
        """Generate an AI response for the given message history.

        Args:
            messages: Conversation history as a list of
                ``{"role": str, "content": str}`` dicts.  The latest user
                message must be the last item.
            context: Optional context string assembled by the memory engine.
                Injected into the system prompt so the model can personalise
                its response.

        Returns:
            The model's reply as a plain string.
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning("Could not initialize OpenAI: %s", e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_openai(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content

    def generate_response(
        self, messages: list[dict[str, str]], context: str = ""
    ) -> str:
        if not self.client:
            return "OpenAI is not configured. Please set OPENAI_API_KEY."

        system_instruction = (
            "You are a helpful AI assistant with long-term memory. "
            "Use the provided context to answer questions about previous interactions. "
            "If the context contains personal information about the user, assume it is "
            "true and use it to personalize your response."
        )
        prefixed = [
            {
                "role": "system",
                "content": (
                    f"{system_instruction}\n\nRelevant Context/Memory:\n{context}"
                    if context
                    else system_instruction
                ),
            }
        ] + messages

        try:
            return self._call_openai(prefixed)
        except Exception as e:
            logger.error("OpenAI call failed after retries: %s", e)
            return f"Error generating response from OpenAI: {str(e)}"


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from anthropic import Anthropic

                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning("Could not initialize Anthropic: %s", e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_anthropic(
        self, system_message: str, formatted_messages: list[dict[str, str]]
    ) -> str:
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system_message if system_message else None,
            messages=formatted_messages,
        )
        return response.content[0].text

    def generate_response(
        self, messages: list[dict[str, str]], context: str = ""
    ) -> str:
        if not self.client:
            return "Anthropic is not configured. Please set ANTHROPIC_API_KEY."

        formatted_messages = []
        system_message = f"Relevant context:\n{context}\n\n" if context else ""

        for msg in messages:
            if msg["role"] == "system":
                system_message += msg["content"]
            else:
                formatted_messages.append(msg)

        try:
            return self._call_anthropic(system_message, formatted_messages)
        except Exception as e:
            logger.error("Anthropic call failed after retries: %s", e)
            return f"Error generating response from Anthropic: {str(e)}"


class LLMAdapter:
    """Unified adapter managing multiple AI providers.

    A single global instance (``llm_adapter``) is created at module import
    time.  Import and use that instance rather than instantiating this class
    directly.

    Attributes:
        providers: Dict mapping provider name strings to initialised provider
            objects (``"openai"`` and ``"anthropic"``).
        default_provider: Provider name used when ``get_response`` is called
            without an explicit ``provider`` argument.
    """

    def __init__(self):
        self.providers = {"openai": OpenAIProvider(), "anthropic": AnthropicProvider()}
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "openai")

    def get_response(
        self,
        message: str,
        context: str = "",
        provider: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate a response from the configured AI provider.

        Appends *message* to *conversation_history* and delegates to the
        selected provider's ``generate_response`` method.

        Args:
            message: The user's latest message.
            context: Memory context string from the memory engine (may be
                empty).
            provider: Override the default provider for this call.  Must be
                one of ``"openai"`` or ``"anthropic"``.  Falls back to
                ``self.default_provider`` when ``None``.
            conversation_history: Prior messages as
                ``[{"role": "user", "content": "..."}, ...]``.  Defaults to
                an empty list.

        Returns:
            The AI-generated reply string.
        """
        provider_name = provider or self.default_provider

        if provider_name not in self.providers:
            return f"Provider '{provider_name}' not supported."

        # Build messages list
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})

        return self.providers[provider_name].generate_response(messages, context)

    def is_available(self, provider: str | None = None) -> bool:
        """Return ``True`` if the selected provider was successfully initialised.

        Args:
            provider: Provider name to check.  Defaults to
                ``self.default_provider``.

        Returns:
            ``True`` when the provider's client object is not ``None``.
        """
        provider_name = provider or self.default_provider

        if provider_name not in self.providers:
            return False

        provider_obj = self.providers[provider_name]
        return provider_obj.client is not None


# Global instance
llm_adapter = LLMAdapter()
