from typing import Annotated

from pydantic import AfterValidator, BaseModel


def validate_number_somehow_complicated(value):
    if value < 0:
        raise ValueError("must be non-negative")
    return value


PositiveInteger = Annotated[int, AfterValidator(validate_number_somehow_complicated)]


class Foo(BaseModel):
    a: PositiveInteger


if __name__ == "__main__":
    print(Foo(a=1))
    print(Foo(a=-1))
