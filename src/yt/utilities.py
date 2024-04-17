"""Module for Pydantic utilities."""

from typing import (
    Any,
    Callable,
    Literal,
    TypeVar,
    get_origin,
)

from pydantic import TypeAdapter

T = TypeVar("T")


def parse_as(
    type_: type[T],
    data: Any,
    mode: Literal["python", "json", "strings"] = "python",
) -> T:
    """Parse a given data structure as a Pydantic model via `TypeAdapter`.

    Read more about `TypeAdapter` [here](https://docs.pydantic.dev/latest/concepts/type_adapter/).

    Args:
        type_: The type to parse the data as.
        data: The data to be parsed.
        mode: The mode to use for parsing, either `python`, `json`, or `strings`.
            Defaults to `python`, where `data` should be a Python object (e.g. `dict`).

    Returns:
        The parsed `data` as the given `type_`.


    Example:
        Basic Usage of `parse_as`
        ```python
        from marvin.utilities.pydantic import parse_as
        from pydantic import BaseModel

        class ExampleModel(BaseModel):
            name: str

        # parsing python objects
        parsed = parse_as(ExampleModel, {"name": "Marvin"})
        assert isinstance(parsed, ExampleModel)
        assert parsed.name == "Marvin"

        # parsing json strings
        parsed = parse_as(
            list[ExampleModel],
            '[{"name": "Marvin"}, {"name": "Arthur"}]',
            mode="json"
        )
        assert all(isinstance(item, ExampleModel) for item in parsed)
        assert (parsed[0].name, parsed[1].name) == ("Marvin", "Arthur")
        ```

    """
    adapter = TypeAdapter(type_)

    if get_origin(type_) is list and isinstance(data, dict):
        data = next(iter(data.values()))

    parser: Callable[[Any], T] = getattr(adapter, f"validate_{mode}")

    return parser(data)
