# Copyright 2024 Marimo. All rights reserved.
from __future__ import annotations

import json
import sys
from collections import defaultdict
from typing import Any, Union

from marimo._messaging.mimetypes import KnownMimeType
from marimo._output import formatting
from marimo._output.formatters.formatter_factory import FormatterFactory
from marimo._output.formatters.repr_formatters import maybe_get_repr_formatter
from marimo._plugins.stateless import plain_text
from marimo._utils.flatten import CyclicStructureError, flatten


def _leaf_formatter(
    value: object,
) -> bool | None | str | int:
    formatter = formatting.get_formatter(value)
    if formatter is not None:
        return ":".join(formatter(value))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    # floats are still converted to strings because JavaScript
    # can't reliably distinguish between them (eg 1 and 1.0)
    if isinstance(value, float):
        return f"text/plain+float:{value}"
    if value is None:
        return value
    if isinstance(value, set):
        return f"text/plain+set:{str(value)}"
    if isinstance(value, tuple):
        return f"text/plain+tuple:{json.dumps(value)}"

    try:
        return f"text/plain:{json.dumps(value)}"
    except TypeError:
        return f"text/plain:{value}"


def format_structure(
    t: Union[tuple[Any, ...], list[Any], dict[str, Any]],
) -> Union[tuple[Any, ...], list[Any], dict[str, Any]]:
    """Format the leaves of a structure.

    Returns a structure of the same shape as `t` with formatted
    leaves.
    """
    flattened, repacker = flatten(t, json_compat_keys=True)
    return repacker([_leaf_formatter(v) for v in flattened])


class StructuresFormatter(FormatterFactory):
    @staticmethod
    def package_name() -> None:
        return None

    def register(self) -> None:
        @formatting.formatter(list)
        @formatting.formatter(tuple)
        @formatting.formatter(dict)
        @formatting.formatter(defaultdict)
        def _format_structure(
            t: Union[
                tuple[Any, ...],
                list[Any],
                dict[str, Any],
                defaultdict[Any, Any],
            ],
        ) -> tuple[KnownMimeType, str]:
            # Some objects extend list/tuple/dict, but also have _repr_ methods
            # that we want to use preferentially.
            repr_formatter = maybe_get_repr_formatter(t)
            if repr_formatter is not None:
                return repr_formatter(t)

            # Check if the object is a subclass of tuple, list, or dict
            # and the repr is different from the default
            # e.g. sys.version_info
            if isinstance(t, tuple) and type(t) is not tuple:
                if str(t) != str(tuple(t)):
                    return plain_text.plain_text(str(t))._mime_()
            elif isinstance(t, list) and type(t) is not list:
                if str(t) != str(list(t)):
                    return plain_text.plain_text(str(t))._mime_()
            elif (
                isinstance(t, dict)
                and type(t) is not dict
                and type(t) is not defaultdict
            ):
                if str(t) != str(dict(t)):
                    return plain_text.plain_text(str(t))._mime_()
            elif isinstance(t, defaultdict) and type(t) is not defaultdict:
                if str(t) != str(defaultdict(t.default_factory, t)):
                    return plain_text.plain_text(str(t))._mime_()

            if t and "matplotlib" in sys.modules:
                # Special case for matplotlib:
                #
                # plt.plot() returns a list of lines 2D objects, one for each
                # line, which typically have identical figures. Without this
                # special case, if a plot had (say) 5 lines, it would be shown
                # 5 times.
                import matplotlib.artist  # type: ignore

                if all(isinstance(i, matplotlib.artist.Artist) for i in t):
                    figs = [getattr(i, "figure", None) for i in t]
                    if all(f is not None and f == figs[0] for f in figs):
                        matplotlib_formatter = formatting.get_formatter(
                            figs[0]
                        )
                        if matplotlib_formatter is not None:
                            return matplotlib_formatter(figs[0])
            try:
                formatted_structure = format_structure(t)
            except CyclicStructureError:
                return ("text/plain", str(t))

            return ("application/json", json.dumps(formatted_structure))
