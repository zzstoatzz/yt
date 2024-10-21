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
def get_current_astronauts() -> list[dict]:
    """Get the current astronauts in space."""
    with httpx.Client() as client:
        response = client.get("http://api.open-notify.org/astros.json")
        response.raise_for_status()
        return response.json()["people"]


@task(cache_policy=INPUTS)
def enrich_astronaut_data(astronaut: dict) -> dict:
    """Enrich astronaut data with information from Wikipedia."""
    with httpx.Client() as client:
        response = client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": astronaut["name"],
            },
        )
        response.raise_for_status()
        page = next(iter(response.json()["query"]["pages"].values()))
        extract = page.get("extract", "No information found.")
        return {
            "name": astronaut["name"],
            "craft": astronaut["craft"],
            "bio": extract.split(".")[0] if extract else "",
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
    astronauts = get_current_astronauts()
    enriched_data = enrich_astronaut_data.map(astronauts)
    save_astronaut_data(enriched_data)


if __name__ == "__main__":
    track_astronauts()
