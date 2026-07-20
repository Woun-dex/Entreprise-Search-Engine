from dataclasses import dataclass
from urllib.parse import urlparse


class InvalidGitHubRepositoryUrl(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GitHubRepositoryCoordinates:
    owner: str
    repository: str


def parse_github_repository_url(
    repository_url: str,
) -> GitHubRepositoryCoordinates:
    parsed = urlparse(repository_url.strip())

    if parsed.scheme != "https":
        raise InvalidGitHubRepositoryUrl(
            "GitHub repository URL must use HTTPS"
        )

    if parsed.hostname not in {"github.com", "www.github.com"}:
        raise InvalidGitHubRepositoryUrl(
            "Only github.com repositories are supported"
        )

    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) != 2:
        raise InvalidGitHubRepositoryUrl(
            "Expected https://github.com/{owner}/{repository}"
        )

    owner, repository = parts

    if repository.endswith(".git"):
        repository = repository[:-4]

    if not owner or not repository:
        raise InvalidGitHubRepositoryUrl(
            "Owner and repository are required"
        )

    return GitHubRepositoryCoordinates(
        owner=owner,
        repository=repository,
    )