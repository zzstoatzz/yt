from functools import wraps
from typing import Annotated

import marvin
from pydantic import AfterValidator, ValidationError


def verify_random_number(number: int) -> int:
    if number != 37:
        raise ValueError("Everyone knows the most random number is 37!")
    return number


RandomNumber = Annotated[int, AfterValidator(verify_random_number)]


def retry_on_error(fn, max_retries=3):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        additional_context = ""
        original_docstring = fn.__wrapped__.__doc__
        retries = 0
        while True:
            try:
                if additional_context:
                    fn.__wrapped__.__doc__ = f"{original_docstring}\n\nYou've tried this before, but it failed:\n{additional_context}"
                return fn(*args, **kwargs)
            except ValidationError as e:
                print(f"Caught a validation error: {e}")
                additional_context += f"\n{str(e)}"
                retries += 1
                if retries == max_retries:
                    raise e

    return wrapper


@retry_on_error
@marvin.fn
def get_random_number() -> RandomNumber:
    """returns a random number"""


if __name__ == "__main__":
    print(get_random_number())
