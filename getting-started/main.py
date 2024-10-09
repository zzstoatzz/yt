import asyncio
from enum import Enum
from typing import Literal

import marvin
from gh_util.functions import fetch_repo_issues
from gh_util.types import GitHubIssue
from prefect import flow, task
from prefect.context import TaskRunContext
from prefect.states import State
from pydantic import BaseModel


class IssueType(Enum):
    FEATURE_REQUEST = "feature request"
    DOCUMENTATION = "documentation"
    BUG_REPORT = "bug report"
    QUESTION = "question"
    OTHER = "other"


def cache_fn(context: TaskRunContext, parameters: dict) -> str:
    """we should cache based on the issue body, and number of comments"""
    return f"{parameters['issue'].body}-{parameters['issue'].comments}"


@task(cache_key_fn=cache_fn, persist_result=True)
def process_issue(issue: GitHubIssue) -> IssueType:
    issue_info = (
        f"Title: {issue.title}\n"
        f"Author: {issue.user.login}\n"
        f"Body: {issue.body or '<<No body present>>'}\n"
    )
    return marvin.classify(issue_info, IssueType)  # type: ignore


class Query(BaseModel):
    owner: str
    repo: str
    state: Literal["open", "closed"] = "open"
    n: int = 10


@flow
async def repo_issue_digest(query: Query):
    issues = await fetch_repo_issues(query.owner, query.repo, query.state, query.n)
    states: list[State] = process_issue.map(issues, return_state=True)  # type: ignore

    for s in zip(
        "".join([issue.title for issue in issues]),
        "".join([state.result() for state in states if state.is_completed()]),
    ):
        print(s)


if __name__ == "__main__":
    asyncio.run(repo_issue_digest(dict(owner="PrefectHQ", repo="prefect")))  # type: ignore
