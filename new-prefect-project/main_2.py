from datetime import timedelta

import httpx
from prefect import Task, flow, task
from prefect.artifacts import create_table_artifact
from prefect.cache_policies import INPUTS
from prefect.client.schemas.objects import State, TaskRun


def is_rate_limit_error(task: Task, task_run: TaskRun, state: State) -> bool:
    try:
        state.result()
    except httpx.HTTPStatusError as e:
        return e.response.status_code == 429


@task(
    retries=42,
    retry_delay_seconds=30,
    retry_condition_fn=is_rate_limit_error,
)
def get_astronauts() -> list[str]:
    """Get the current astronauts in space."""
    with httpx.Client() as client:
        response = client.get("http://api.open-notify.org/astros.json")
        response.raise_for_status()
        return [person["name"] for person in response.json()["people"]]


@task(cache_policy=INPUTS, cache_expiration=timedelta(hours=1))
def get_astronaut_info(name: str) -> dict:
    """Get information about an astronaut from Wikipedia."""
    with httpx.Client() as client:
        response = client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": name,
            },
        )
        response.raise_for_status()
        page = next(iter(response.json()["query"]["pages"].values()))
        return {"name": name, "extract": page.get("extract", "No information found.")}


@task
def process_astronaut(info: list[dict]) -> list[dict]:
    """Process the astronaut information."""
    return {
        "name": info["name"],
        "first_sentence": info["extract"].split(".")[0] if info["extract"] else "",
    }


@task
def save_astronaut_data(data: list[dict]) -> None:
    """Save the processed astronaut data."""
    create_table_artifact(
        key="astronaut-info",
        table=data,
        description="Current astronauts in space \n\n![](https://i.imgflip.com/97ctl5.jpg)",
    )


@flow
def track_astronauts():
    astronauts = get_astronauts()
    astronaut_info = get_astronaut_info.map(astronauts)
    processed_info = process_astronaut.map(astronaut_info)
    save_astronaut_data(processed_info)


if __name__ == "__main__":
    track_astronauts()
