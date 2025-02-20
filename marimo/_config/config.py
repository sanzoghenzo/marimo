# Copyright 2024 Marimo. All rights reserved.
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from marimo._config.packages import infer_package_manager
from marimo._config.utils import deep_copy

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
    cast,
)

from marimo._output.rich_help import mddoc
from marimo._utils.deep_merge import deep_merge


@mddoc
@dataclass
class CompletionConfig(TypedDict):
    """Configuration for code completion.

    A dict with key/value pairs configuring code completion in the marimo
    editor.

    **Keys.**

    - `activate_on_typing`: if `False`, completion won't activate
    until the completion hotkey is entered
    - `copilot`: if `True`, enable the GitHub Copilot language server
    """

    activate_on_typing: bool
    copilot: Union[bool, Literal["github", "codeium"]]
    codeium_api_key: NotRequired[Optional[str]]


@mddoc
@dataclass
class SaveConfig(TypedDict):
    """Configuration for saving.

    **Keys.**

    - `autosave`: one of `"off"` or `"after_delay"`
    - `delay`: number of milliseconds to wait before autosaving
    - `format_on_save`: if `True`, format the code on save
    """

    autosave: Literal["off", "after_delay"]
    autosave_delay: int
    format_on_save: bool


@mddoc
@dataclass
class KeymapConfig(TypedDict):
    """Configuration for keymaps.

    **Keys.**

    - `preset`: one of `"default"` or `"vim"`
    - `overrides`: a dict of keymap actions to their keymap override
    """

    preset: Literal["default", "vim"]
    overrides: NotRequired[Dict[str, str]]


OnCellChangeType = Literal["lazy", "autorun"]
ExecutionType = Literal["relaxed", "strict"]


@mddoc
@dataclass
class RuntimeConfig(TypedDict):
    """Configuration for runtime.

    **Keys.**

    - `auto_instantiate`: if `False`, cells won't automatically
        run on startup. This only applies when editing a notebook,
        and not when running as an application.
        The default is `True`.
    - `auto_reload`: if `lazy`, cells importing modified modules will marked
      as stale; if `autorun`, affected cells will be automatically run. similar
      to IPython's %autoreload extension but with more code intelligence.
    - `on_cell_change`: if `lazy`, cells will be marked stale when their
      ancestors run but won't autorun; if `autorun`, cells will automatically
      run when their ancestors run.
    - `execution_type`: if `relaxed`, marimo will not clone cell declarations;
      if `strict` marimo will clone cell declarations by default, avoiding
      hidden potential state build up.
    - `watcher_on_save`: how to handle file changes when saving. `"lazy"` marks
        affected cells as stale, `"autorun"` automatically runs affected cells.
    - `output_max_bytes`: the maximum size in bytes of cell outputs; larger
        values may affect frontend performance
    - `std_stream_max_bytes`: the maximum size in bytes of console outputs;
      larger values may affect frontend performance
    """

    auto_instantiate: bool
    auto_reload: Literal["off", "lazy", "autorun"]
    on_cell_change: OnCellChangeType
    watcher_on_save: Literal["lazy", "autorun"]
    output_max_bytes: int
    std_stream_max_bytes: int


# TODO(akshayka): remove normal, migrate to compact
# normal == compact
WidthType = Literal["normal", "compact", "medium", "full"]
Theme = Literal["light", "dark", "system"]


@mddoc
@dataclass
class DisplayConfig(TypedDict):
    """Configuration for display.

    **Keys.**

    - `theme`: `"light"`, `"dark"`, or `"system"`
    - `code_editor_font_size`: font size for the code editor
    - `cell_output`: `"above"` or `"below"`
    - `dataframes`: `"rich"` or `"plain"`
    """

    theme: Theme
    code_editor_font_size: int
    cell_output: Literal["above", "below"]
    default_width: WidthType
    dataframes: Literal["rich", "plain"]


@mddoc
@dataclass
class FormattingConfig(TypedDict):
    """Configuration for code formatting.

    **Keys.**

    - `line_length`: max line length
    """

    line_length: int


@dataclass
class ServerConfig(TypedDict):
    """Configuration for the server.

    **Keys.**

    - `browser`: the web browser to use. `"default"` or a browser registered
        with Python's webbrowser module (eg, `"firefox"` or `"chrome"`)
    - `follow_symlink`: if true, the server will follow symlinks it finds
        inside its static assets directory.
    """

    browser: Union[Literal["default"], str]
    follow_symlink: bool


@dataclass
class PackageManagementConfig(TypedDict):
    """Configuration options for package management.

    **Keys.**

    - `manager`: the package manager to use
    """

    manager: Literal["pip", "rye", "uv", "poetry", "pixi"]


@dataclass
class AiConfig(TypedDict, total=False):
    """Configuration options for AI.

    **Keys.**

    - `rules`: custom rules to include in all AI completion prompts
    - `open_ai`: the OpenAI config
    - `anthropic`: the Anthropic config
    - `google`: the Google AI config
    """

    rules: NotRequired[str]
    open_ai: OpenAiConfig
    anthropic: AnthropicConfig
    google: GoogleAiConfig


@dataclass
class OpenAiConfig(TypedDict, total=False):
    """Configuration options for OpenAI or OpenAI-compatible services.

    **Keys.**

    - `api_key`: the OpenAI API key
    - `model`: the model to use.
        if model starts with `claude-` we use the AnthropicConfig
    - `base_url`: the base URL for the API
    """

    api_key: str
    model: NotRequired[str]
    base_url: NotRequired[str]


@dataclass
class AnthropicConfig(TypedDict, total=False):
    """Configuration options for Anthropic.

    **Keys.**

    - `api_key`: the Anthropic
    """

    api_key: str


@dataclass
class GoogleAiConfig(TypedDict, total=False):
    """Configuration options for Google AI.

    **Keys.**

    - `api_key`: the Google AI API key
    """

    api_key: str


@dataclass
class SnippetsConfig(TypedDict):
    """Configuration for snippets.

    **Keys.**

    - `custom_path`: the path to the custom snippets directory
    """

    custom_paths: NotRequired[List[str]]
    include_default_snippets: NotRequired[bool]


@mddoc
@dataclass
class MarimoConfig(TypedDict):
    """Configuration for the marimo editor"""

    completion: CompletionConfig
    display: DisplayConfig
    formatting: FormattingConfig
    keymap: KeymapConfig
    runtime: RuntimeConfig
    save: SaveConfig
    server: ServerConfig
    package_management: PackageManagementConfig
    ai: NotRequired[AiConfig]
    experimental: NotRequired[Dict[str, Any]]
    snippets: NotRequired[SnippetsConfig]


@mddoc
@dataclass
class PartialMarimoConfig(TypedDict, total=False):
    """Partial configuration for the marimo editor"""

    completion: CompletionConfig
    display: DisplayConfig
    formatting: FormattingConfig
    keymap: KeymapConfig
    runtime: RuntimeConfig
    save: SaveConfig
    server: ServerConfig
    package_management: PackageManagementConfig
    ai: NotRequired[AiConfig]
    experimental: NotRequired[Dict[str, Any]]
    snippets: SnippetsConfig


DEFAULT_CONFIG: MarimoConfig = {
    "completion": {"activate_on_typing": True, "copilot": False},
    "display": {
        "theme": "light",
        "code_editor_font_size": 14,
        "cell_output": "above",
        "default_width": "medium",
        "dataframes": "rich",
    },
    "formatting": {"line_length": 79},
    "keymap": {"preset": "default", "overrides": {}},
    "runtime": {
        "auto_instantiate": True,
        "auto_reload": "off",
        "on_cell_change": "autorun",
        "watcher_on_save": "lazy",
        "output_max_bytes": int(
            os.getenv("MARIMO_OUTPUT_MAX_BYTES", 8_000_000)
        ),
        "std_stream_max_bytes": int(
            os.getenv("MARIMO_STD_STREAM_MAX_BYTES", 1_000_000)
        ),
    },
    "save": {
        "autosave": "after_delay",
        "autosave_delay": 1000,
        "format_on_save": False,
    },
    "package_management": {"manager": infer_package_manager()},
    "server": {
        "browser": "default",
        "follow_symlink": False,
    },
    "snippets": {
        "custom_paths": [],
        "include_default_snippets": True,
    },
}


def merge_default_config(
    config: PartialMarimoConfig | MarimoConfig,
) -> MarimoConfig:
    """Merge a user configuration with the default configuration."""
    return merge_config(DEFAULT_CONFIG, config)


def merge_config(
    config: MarimoConfig, new_config: PartialMarimoConfig | MarimoConfig
) -> MarimoConfig:
    """Merge a user configuration with a new configuration."""
    # Remove the keymap overrides from the incoming config,
    # so that they don't get merged into the new config
    if new_config.get("keymap", {}).get("overrides") is not None:
        # Clone config to avoid modifying the original
        config = deep_copy(config)
        config.get("keymap", {}).pop("overrides", {})

    merged = cast(
        MarimoConfig,
        deep_merge(
            cast(Dict[Any, Any], config), cast(Dict[Any, Any], new_config)
        ),
    )

    # Patches for backward compatibility
    if "runtime" in merged:
        if (
            merged["runtime"].get("auto_reload") is False  # type:ignore[comparison-overlap]
        ):
            merged["runtime"]["auto_reload"] = "off"
        elif (
            merged["runtime"].get("auto_reload") is True  # type:ignore[comparison-overlap]
        ):
            merged["runtime"]["auto_reload"] = "lazy"
        elif (
            merged["runtime"].get("auto_reload") == "detect"  # type:ignore[comparison-overlap]
        ):
            merged["runtime"]["auto_reload"] = "lazy"

    return merged
