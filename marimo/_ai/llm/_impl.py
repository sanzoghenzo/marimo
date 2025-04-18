# Copyright 2024 Marimo. All rights reserved.
from __future__ import annotations

import contextlib
import os
from typing import Callable, Optional, cast

from marimo._ai._convert import (
    convert_to_anthropic_messages,
    convert_to_google_messages,
    convert_to_groq_messages,
    convert_to_openai_messages,
)
from marimo._ai._types import (
    ChatMessage,
    ChatModel,
    ChatModelConfig,
)
from marimo._dependencies.dependencies import DependencyManager

DEFAULT_SYSTEM_MESSAGE = (
    "You are a helpful assistant specializing in data science."
)


class simple(ChatModel):
    """
    Convenience class for wrapping a ChatModel or callable to
    take a single prompt

    **Args:**

    - delegate: A callable that takes a
        single prompt and returns a response
    """

    def __init__(self, delegate: Callable[[str], object]):
        self.delegate = delegate

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        del config
        prompt = str(messages[-1].content)
        return self.delegate(prompt)


class openai(ChatModel):
    """
    OpenAI ChatModel

    **Args:**

    - model: The model to use.
        Can be found on the [OpenAI models page](https://platform.openai.com/docs/models)
    - system_message: The system message to use
    - api_key: The API key to use.
        If not provided, the API key will be retrieved
        from the OPENAI_API_KEY environment variable or the user's config.
    - base_url: The base URL to use
    """

    def __init__(
        self,
        model: str,
        *,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.system_message = system_message
        self.api_key = api_key
        self.base_url = base_url

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        DependencyManager.openai.require(
            "chat model requires openai. `pip install openai`"
        )
        from openai import OpenAI  # type: ignore[import-not-found]
        from openai.types.chat import (  # type: ignore[import-not-found]
            ChatCompletionMessageParam,
        )

        client = OpenAI(
            api_key=self.api_key
            or _require_api_key("OPENAI_API_KEY", "open_ai", "OpenAI"),
            base_url=self.base_url or None,
        )

        openai_messages = convert_to_openai_messages(
            [ChatMessage(role="system", content=self.system_message)]
            + messages
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], openai_messages),
            max_completion_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=False,
        )

        choice = response.choices[0]
        content = choice.message.content
        return content or ""


class azure(ChatModel):
    """
    AzureOpenAI ChatModel

    **Args:**

    - model: The model to use.
        Can be found on the [Azure OpenAI Service models page](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions)
    - system_message: The system message to use
    - api_key: The API key to use.
        If not provided, the API key will be retrieved
        from the OPENAI_API_KEY environment variable or the user's config.
    - base_url: The base URL to use
    """

    def __init__(
        self,
        model: str,
        *,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.system_message = system_message
        self.api_key = api_key
        self.base_url = base_url

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        DependencyManager.openai.require(
            "chat model requires openai. `pip install openai`"
        )
        from urllib.parse import parse_qs, urlparse

        from openai import AzureOpenAI  # type: ignore[import-not-found]
        from openai.types.chat import (  # type: ignore[import-not-found]
            ChatCompletionMessageParam,
        )

        # Extract the model and api version from the url
        # https://[domain]/openai/deployments/[model]/chat/completions?api-version=[api_version]
        parsed_url = urlparse(self.base_url)
        self.model = cast(str, parsed_url.path).split("/")[3]
        api_version = parse_qs(cast(str, parsed_url.query))["api-version"][0]
        client = AzureOpenAI(
            api_key=self.api_key
            or _require_api_key("AZURE_API_KEY", "azure", "Azure OpenAI"),
            api_version=api_version,
            azure_endpoint=f"{cast(str, parsed_url.scheme)}://{cast(str, parsed_url.hostname)}",
        )

        openai_messages = convert_to_openai_messages(
            [ChatMessage(role="system", content=self.system_message)]
            + messages
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], openai_messages),
            max_completion_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=False,
        )

        choice = response.choices[0]
        content = choice.message.content
        return content or ""


class anthropic(ChatModel):
    """
    Anthropic ChatModel

    **Args:**

    - model: The model to use.
        Can be found on the [Anthropic models page](https://docs.anthropic.com/en/docs/about-claude/models)
    - system_message: The system message to use
    - api_key: The API key to use.
        If not provided, the API key will be retrieved
        from the ANTHROPIC_API_KEY environment variable
        or the user's config.
    - base_url: The base URL to use
    """

    def __init__(
        self,
        model: str,
        *,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.system_message = system_message
        self.api_key = api_key
        self.base_url = base_url
        self.system_message = system_message

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        DependencyManager.anthropic.require(
            "chat model requires anthropic. `pip install anthropic`"
        )
        from anthropic import (  # type: ignore[import-not-found]
            NOT_GIVEN,
            Anthropic,
        )
        from anthropic.types.message_param import (  # type: ignore[import-not-found]
            MessageParam,
        )

        client = Anthropic(
            api_key=self.api_key
            or _require_api_key("ANTHROPIC_API_KEY", "anthropic", "Antropic"),
            base_url=self.base_url,
        )

        anthropic_messages = convert_to_anthropic_messages(messages)
        response = client.messages.create(
            model=self.model,
            system=self.system_message,
            max_tokens=config.max_tokens or 4096,
            messages=cast(list[MessageParam], anthropic_messages),
            top_p=config.top_p if config.top_p is not None else NOT_GIVEN,
            top_k=config.top_k if config.top_k is not None else NOT_GIVEN,
            stream=False,
            temperature=config.temperature
            if config.temperature is not None
            else NOT_GIVEN,
        )

        content = response.content
        if len(content) > 0:
            if content[0].type == "text":
                return content[0].text
            elif content[0].type == "tool_use":
                return content
        return ""


class google(ChatModel):
    """
    Google AI ChatModel

    **Args:**

    - model: The model to use.
        Can be found on the [Gemini models page](https://ai.google.dev/gemini-api/docs/models/gemini)
    - system_message: The system message to use
    - api_key: The API key to use.
        If not provided, the API key will be retrieved
        from the GOOGLE_AI_API_KEY environment variable
        or the user's config.
    """

    def __init__(
        self,
        model: str,
        *,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.system_message = system_message
        self.api_key = api_key

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        DependencyManager.google_ai.require(
            "chat model requires google. `pip install google-generativeai`"
        )
        import google.generativeai as genai  # type: ignore[import-not-found]

        genai.configure(
            api_key=self.api_key
            or _require_api_key("GOOGLE_AI_API_KEY", "google", "Google AI")
        )
        client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.GenerationConfig(
                max_output_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
            ),
        )

        google_messages = convert_to_google_messages(messages)
        response = client.generate_content(google_messages)

        content = response.text
        return content or ""


class groq(ChatModel):
    """
    Groq ChatModel

    **Args:**

    - model: The model to use.
        Can be found on the [Groq models page](https://console.groq.com/docs/models)
    - system_message: The system message to use
    - api_key: The API key to use.
        If not provided, the API key will be retrieved
        from the GROQ_API_KEY environment variable or the user's config.
    - base_url: The base URL to use
    """

    def __init__(
        self,
        model: str,
        *,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.system_message = system_message
        self.api_key = api_key
        self.base_url = base_url

    def __call__(
        self, messages: list[ChatMessage], config: ChatModelConfig
    ) -> object:
        DependencyManager.groq.require(
            "chat model requires groq. `pip install groq`"
        )
        from groq import Groq  # type: ignore[import-not-found]

        client = Groq(
            api_key=self.api_key
            or _require_api_key("GROQ_API_KEY", "groq", "Groq"),
            base_url=self.base_url,
        )

        groq_messages = convert_to_groq_messages(
            [ChatMessage(role="system", content=self.system_message)]
            + messages
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=groq_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stop=None,
            stream=False,
        )

        choice = response.choices[0]
        content = choice.message.content
        return content or ""


def _require_api_key(env_var: str, config_key: str, name: str) -> str:
    # Then check the environment variable
    env_key = os.environ.get(env_var)
    if env_key is not None:
        return env_key

    # Then check the user's config
    with contextlib.suppress(Exception):
        from marimo._runtime.context.types import get_context

        api_key = get_context().marimo_config["ai"][config_key]["api_key"]
        if api_key:
            return api_key

    raise ValueError(
        f"{name} api key not provided. Pass it as an argument or "
        f"set {env_var} as an environment variable"
    )
