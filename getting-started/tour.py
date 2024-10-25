import math

from prefect import flow, task
from pydantic import BaseModel, Field


class Inputs(BaseModel):
    x: list[int] = Field(default_factory=lambda: [1, 2, 3])
    y: list[int] = Field(default_factory=lambda: [4, 5, 6])
    multiplier: int = Field(default=42)


@task(task_run_name="add {x} and {y}")
def add(x: int, y: int) -> int:
    return x + y


@task(task_run_name="multiply {x} and {y}")
def multiply(x: int, y: int) -> int:
    return x * y


@flow(flow_run_name="perform some computation")
def perform_some_computation(inputs: Inputs):
    futures = add.map(x=inputs.x, y=inputs.y)
    # multiply each of the results by the multiplier
    return multiply.map(x=futures, y=inputs.multiplier)


@task(task_run_name="calculate stats")
def calculate_stats(results: list[int]) -> dict:
    return {
        "sum": task(task_run_name=f"sum {results}")(lambda x: sum(x))(results),
        "product": task(task_run_name=f"product {results}")(lambda x: math.prod(x))(
            results
        ),
    }


@flow
def main(inputs: Inputs = Inputs()):
    results = perform_some_computation(inputs)
    stats = calculate_stats(results)
    print(stats)


if __name__ == "__main__":
    main()
