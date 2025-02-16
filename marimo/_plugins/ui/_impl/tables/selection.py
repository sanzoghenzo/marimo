from __future__ import annotations

from typing import TypeVar, cast

import narwhals.stable.v1 as nw
from narwhals.typing import IntoDataFrame

INDEX_COLUMN_NAME = "_marimo_row_id"

T = TypeVar("T")


def add_selection_column(data: T) -> T:
    if nw.dependencies.is_into_dataframe(data):
        df = nw.from_native(cast(IntoDataFrame, data), strict=True)
        if INDEX_COLUMN_NAME not in df.columns:
            return df.with_row_index(name=INDEX_COLUMN_NAME).to_native()  # type: ignore[return-value]
    return data


def remove_selection_column(data: T) -> T:
    if nw.dependencies.is_into_dataframe(data):
        df = nw.from_native(cast(IntoDataFrame, data), strict=True)
        if INDEX_COLUMN_NAME in df.columns:
            return df.drop(INDEX_COLUMN_NAME).to_native()  # type: ignore[return-value]
    return data
