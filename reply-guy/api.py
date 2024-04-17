import marvin
from fastapi import FastAPI
from gh_util.functions import (
    create_issue_comment,
    fetch_repo_issue,
    fetch_repo_labels,
    update_labels_on_issue,
)
from gh_util.logging import get_logger
from gh_util.types import GitHubIssue, GitHubLabel
from jinja2 import Template
from starlette.requests import Request

app = FastAPI()


logger = get_logger(__name__)


@marvin.fn
def select_labels_for_issue(
    labels: list[GitHubLabel],
    issue_digest: str,
    existing_labels: list[str] = None,
) -> list[str]:
    """Select labels for an issue based on the issue digest.

    If existing labels are appropriate, just return them.
    """


@marvin.fn
def write_a_comment(issue: GitHubIssue) -> str:
    """provide a comment on the issue as if you were a maintainer, but
    always speak in the style of Arnold Schwarzenegger."""


@app.get("/")
async def healthcheck():
    return {"Hello": "World"}


def get_repo_issue_output(issue: GitHubIssue) -> str:
    template = Template(
        """
        GitHub Issue
        Created by {{ issue.user.login }} on {{ issue.created_at.strftime('%A, %B %d, %Y %I:%M %p') }}

        [{{ issue.number }} {{ issue.title }}]({{ issue.url }})
        Created by {{ issue.user.login }} on {{ issue.created_at }}

        {{ issue.body }}
        {% for comment in issue.user_comments %}
            Comment
            {{ comment.created_at.strftime('%A, %B %d, %Y %I:%M %p') }}

            [{{ comment.user.login }}]({{ comment.user.url }}) said:

            {{ comment.body }}
        {% endfor %}
    """
    )

    return template.render(issue=issue)


@app.post("/webhook")
async def webhook(request: Request):
    event_type = request.headers.get("X-GitHub-Event")
    logger.info(f"Received event: {event_type}")

    if not event_type.startswith("issue"):
        return {"status": "ignored"}

    payload = await request.json()

    issue_number = payload.get("issue", {}).get("number")

    logger.info(f"Issue number: {issue_number}")

    owner = payload.get("repository", {}).get("owner", {}).get("login")
    repo = payload.get("repository", {}).get("name")

    issue = await fetch_repo_issue(owner, repo, issue_number, include_comments=True)

    new_labels = select_labels_for_issue(
        labels=[label.name for label in await fetch_repo_labels(owner, repo)],
        issue_digest=get_repo_issue_output(issue),
        existing_labels=issue.labels,
    )

    await update_labels_on_issue(owner, repo, issue_number, new_labels)

    updated_issue = await fetch_repo_issue(owner, repo, issue_number)

    comment = write_a_comment(updated_issue)

    await create_issue_comment(owner, repo, issue_number, comment)

    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="localhost", port=8000, reload=True)
