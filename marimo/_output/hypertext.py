# Copyright 2024 Marimo. All rights reserved.
from __future__ import annotations

import os
import weakref
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Optional, cast, final

from marimo._messaging.mimetypes import KnownMimeType
from marimo._output.mime import MIME
from marimo._output.rich_help import mddoc
from marimo._output.utils import flatten_string

if TYPE_CHECKING:
    from collections.abc import Iterator

    from marimo._plugins.core.web_component import JSONType
    from marimo._plugins.ui._core.ui_element import UIElement
    from marimo._plugins.ui._impl.batch import batch as batch_plugin


def _hypertext_cleanup(virtual_filenames: list[str]) -> None:
    """Cleanup side-effects related to initialization of Html."""
    from marimo._runtime.context import (
        ContextNotInitializedError,
        get_context,
    )

    try:
        ctx = get_context()
    except ContextNotInitializedError:
        return

    if ctx is not None and ctx.virtual_files_supported:
        for f in virtual_filenames:
            ctx.virtual_file_registry.dereference(f)


@mddoc
@dataclass
class Html(MIME):
    """A wrapper around HTML text that can be used as an output.

    Output an `Html` object as the last expression of a cell to render it in
    your app.

    Use f-strings to embed Html objects as text into other HTML or markdown
    strings. For example:

    ```python3
    hello_world = Html("<h2>Hello, World</h2>")
    Html(
        f'''
        <h1>Hello, Universe!</h1>
        {hello_world}
        '''
    )
    ```

    Attributes:
        text: a string of HTML

    Args:
        text: a string of HTML

    Methods:
        batch: convert this HTML element into a batched UI element
        callout: wrap this element in a callout
        center: center this element in the output area
        right: right-justify this element in the output area
    """

    # Some libraries (e.g. polars) will serialize dataclasses so we add this
    # field to serialize the mimetype. This is to support rich display in tables/dfs.
    _serialized_mime_bundle: dict[Literal["mimetype", "data"], str] = field(
        default_factory=dict,
        repr=False,
        init=False,
    )

    def __init__(self, text: str) -> None:
        """Initialize the HTML element.

        Subclasses of HTML MUST call this method.
        """
        self._text = text
        mimetype, data = self._mime_()

        self._serialized_mime_bundle = {
            "mimetype": mimetype,
            "data": data,
        }
        # Whenever _serialized_mime_bundle is set, ensure a public copy exists.
        # This avoids declaring a public attribute (does not show up in docs)
        # Pandas does not serialize private variables, so we need this.
        self.__setattr__(
            "serialized_mime_bundle", self._serialized_mime_bundle
        )

        # A list of the virtual file names referenced by this HTML element.
        self._virtual_filenames: list[str] = []

        from marimo._runtime.context import (
            ContextNotInitializedError,
            get_context,
        )

        try:
            ctx = get_context()
        except ContextNotInitializedError:
            return

        # Virtual File Refcounting
        #
        # HTML elements are responsible for maintaining the reference counts
        # of virtual files: virtual files cannot be disposed while HTML
        # elements reference them. For example, a user might cache HTML
        # referencing a virtual file if they create it using functools.cache.
        #
        # flatten the text to make sure searching isn't broken by newlines
        flat_text = flatten_string(self._text)
        for virtual_filename in ctx.virtual_file_registry.filenames():
            if virtual_filename in flat_text:
                ctx.virtual_file_registry.reference(virtual_filename)
                self._virtual_filenames.append(virtual_filename)

        # Dereference virtual files on object destruction
        finalizer = weakref.finalize(
            self, _hypertext_cleanup, self._virtual_filenames
        )
        finalizer.atexit = False

    @property
    def text(self) -> str:
        """A string of HTML representing this element."""
        return self._text

    @final
    def _mime_(self) -> tuple[KnownMimeType, str]:
        no_js = os.getenv("MARIMO_NO_JS", "false").lower() == "true"
        if no_js and hasattr(self, "_repr_png_"):
            return (
                "image/png",
                cast(
                    str, cast(Any, self)._repr_png_().decode()
                ),  # ignore[no-untyped-call]
            )
        if no_js and hasattr(self, "_repr_markdown_"):
            return (
                "text/markdown",
                cast(
                    str, cast(Any, self)._repr_markdown_()
                ),  # ignore[no-untyped-call]
            )
        return ("text/html", self.text)

    def __format__(self, spec: str) -> str:
        """Format `self` as HTML text"""
        del spec
        return " ".join(
            [line.strip() for line in self.text.strip().split("\n")]
        )

    @mddoc
    def batch(self, **elements: UIElement[JSONType, object]) -> batch_plugin:
        """Convert an HTML object with templated text into a UI element.

        This method lets you create custom UI elements that are represented
        by arbitrary HTML.

        Example:
            ```python3
            user_info = mo.md(
                '''
                - What's your name?: {name}
                - When were you born?: {birthday}
                '''
            ).batch(name=mo.ui.text(), birthday=mo.ui.date())
            ```

            In this example, `user_info` is a UI Element whose output is markdown
            and whose value is a dict with keys `'name'` and '`birthday`'
            (and values equal to the values of their corresponding elements).

        Args:
            elements: the UI elements to interpolate into the HTML template.
        """
        from marimo._plugins.ui._impl.batch import batch as batch_plugin

        return batch_plugin(html=self, elements=elements)

    @mddoc
    def center(self) -> Html:
        """Center an item.

        Example:
            ```python3
            mo.md("# Hello, world").center()
            ```

        Returns:
            An `Html` object.
        """
        from marimo._plugins.stateless import flex

        return flex.hstack([self], justify="center")

    @mddoc
    def right(self) -> Html:
        """Right-justify.

        Example:
            ```python3
            mo.md("# Hello, world").right()
            ```

        Returns:
            An `Html` object.
        """
        from marimo._plugins.stateless import flex

        return flex.hstack([self], justify="end")

    @mddoc
    def left(self) -> Html:
        """Left-justify.

        Example:
            ```python3
            mo.md("# Hello, world").left()
            ```

        Returns:
            An `Html` object.
        """
        from marimo._plugins.stateless import flex

        return flex.hstack([self], justify="start")

    @mddoc
    def callout(
        self,
        kind: Literal[
            "neutral", "danger", "warn", "success", "info"
        ] = "neutral",
    ) -> Html:
        """Create a callout containing this HTML element.

        A callout wraps your HTML element in a raised box, emphasizing its
        importance. You can style the callout for different situations with the
        `kind` argument.

        Examples:
            ```python3
            mo.md("Hooray, you did it!").callout(kind="success")
            ```

            ```python3
            mo.md("It's dangerous to go alone!").callout(kind="warn")
            ```
        """

        from marimo._plugins.stateless.callout import callout as _callout

        return _callout(self, kind=kind)

    @mddoc
    def style(
        self, style: Optional[dict[str, Any]] = None, **kwargs: Any
    ) -> Html:
        """Wrap an object in a styled container.

        Example:
            ```python
            mo.md("...").style({"max-height": "300px", "overflow": "auto"})
            mo.md("...").style(max_height="300px", overflow="auto")
            ```

        Args:
            style: an optional dict of CSS styles, keyed by property name
            **kwargs: CSS styles as keyword arguments
        """
        from marimo._plugins.stateless import style as _style

        return _style.style(self, style=style, **kwargs)

    def _repr_html_(self) -> str:
        return self.text


def _js(text: str) -> Html:
    # TODO: interpolation of Python values to javascript
    return Html("<script>" + text + "</script>")


@contextmanager
def patch_html_for_non_interactive_output() -> Iterator[None]:
    """
    Patch Html to return text/markdown for simpler non-interactive outputs,
    that can be rendered without JS/CSS (just as in the GitHub viewer).
    """
    # HACK: we must set MARIMO_NO_JS since the rendering may happen in another
    # thread
    # This won't work when we are running a marimo server and are auto-exporting
    # with this enabled.
    old_no_js = os.getenv("MARIMO_NO_JS", "false")
    try:
        os.environ["MARIMO_NO_JS"] = "true"
        yield
    finally:
        os.environ["MARIMO_NO_JS"] = old_no_js
