from prefect import flow, task


@task(retries=3)
def load_data(query: str) -> list[dict]:
    """Load data from a database or API."""
    return [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]


@task
def process_data(data: list[dict]) -> list[dict]:
    """Process the data."""
    return [{"name": d["name"], "age": d["age"] + 1} for d in data]


@task
def save_data(data: list[dict]) -> None:
    """Save the processed data to a database or file."""
    print(data)


@flow
def main(query: str = "query"):
    data = load_data(query)
    print(f"loaded data: {data}")
    processed_data = process_data(data)
    print(f"processed data: {processed_data}")
    save_data(processed_data)
    print(f"saved data: {processed_data}")


if __name__ == "__main__":
    main.serve(interval=10)
