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
async def read_root():
    return {"Hello": "World"}


def get_repo_issue_output(issue: GitHubIssue) -> str:
    issue_output = "GitHub Issue\n"
    issue_output += f"Created by {issue.user.login} on {issue.created_at:%A, %B %d, %Y %I:%M %p}\n\n"
    issue_output += f"[{issue.number} {issue.title}]({issue.url})\n"
    issue_output += f"Created by {issue.user.login} on {issue.created_at}\n\n"
    issue_output += f"{issue.body}\n"

    for comment in getattr(issue, "user_comments", []):
        comment_output = "\nComment\n"
        comment_output += f"{comment.created_at:%A, %B %d, %Y %I:%M %p}\n\n"
        comment_output += f"[{comment.user.login}]({comment.user.url}) said:\n\n"
        comment_output += f"{comment.body}\n"

        issue_output += comment_output

    return issue_output


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
