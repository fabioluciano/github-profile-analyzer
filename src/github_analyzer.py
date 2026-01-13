"""GitHub data collection and analysis module."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
import tenacity

from .config import settings
from .utils import is_recent, safe_get


class GitHubAnalyzer:
    """Handles GitHub API interactions and data analysis."""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHub-Analysis-Tool/1.0",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"token {token}"

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def _make_request(self, url: str, headers: Optional[Dict[str, Any]] = None) -> Any:
        """Make a request with retry logic."""
        try:
            response = self.session.get(
                url, headers=headers or self.get_headers(), timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(
                    "Rate limit exceeded. Please check your token or wait."
                ) from e
            raise
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}") from e

    def get_headers(self, star_header: bool = False) -> Dict[str, Any]:
        """Get appropriate headers for API requests."""
        headers = dict(self.session.headers)
        if star_header:
            headers["Accept"] = "application/vnd.github.star+json"
        return headers

    def get_starred_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetch starred repositories with pagination."""
        repos = []
        page = 1

        try:
            while True:
                url = f"{settings.github_api_base}/users/{username}/starred?page={page}&per_page=100"
                data = self._make_request(
                    url, headers=self.get_headers(star_header=True)
                )

                if not data:
                    break

                repos.extend(data)
                page += 1
        except Exception as e:
            print(f"⚠ Error fetching starred repos: {e}")
            return repos

        return repos

    def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetch user repositories with pagination."""
        repos = []
        page = 1

        try:
            while True:
                url = f"{settings.github_api_base}/users/{username}/repos?page={page}&per_page=100&sort=updated"
                data = self._make_request(url, headers=self.get_headers())

                if not data:
                    break

                repos.extend(data)
                page += 1
        except Exception as e:
            print(f"⚠ Error fetching user repos: {e}")
            return repos

        return repos

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Fetch user profile information."""
        try:
            url = f"{settings.github_api_base}/users/{username}"
            return self._make_request(url, headers=self.get_headers())
        except Exception as e:
            print(f"⚠ Error fetching user info: {e}")
            return {}

    def get_recent_activity(self, username: str) -> List[Dict[str, Any]]:
        """Fetch recent user activity."""
        try:
            url = f"{settings.github_api_base}/users/{username}/events/public?per_page=100"
            return self._make_request(url, headers=self.get_headers())
        except Exception as e:
            print(f"⚠ Error fetching recent activity: {e}")
            return []

    def analyze_recent_activity(
        self, events: List[Dict[str, Any]], own_repos_names: set
    ) -> Dict[str, Any]:
        """Analyze recent activity events."""
        activity_summary = {
            "commits": 0,
            "prs_created": 0,
            "prs_reviewed": 0,
            "issues_opened": 0,
            "issues_commented": 0,
            "repos_worked_on": set(),
            "repos_contributed": set(),
            "recent_commits_detail": [],
            "collaboration_repos": set(),
        }

        thirty_days_ago = datetime.now() - timedelta(days=settings.recent_days)

        # Extract just the repo names (without owner) from own repos
        own_repo_names_only = {name.split("/")[-1] for name in own_repos_names}

        def is_fork_of_own_repo(repo_full_name: str) -> bool:
            """Check if a repo is likely a fork of one of our own repos."""
            repo_name_only = repo_full_name.split("/")[-1]
            return repo_name_only in own_repo_names_only

        for event in events:
            try:
                event_date = datetime.strptime(
                    event["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                )
            except ValueError:
                continue

            if event_date < thirty_days_ago:
                continue

            event_type = event["type"]
            repo_name = event["repo"]["name"]
            is_own_repo = repo_name in own_repos_names
            is_fork_of_own = is_fork_of_own_repo(repo_name)

            if event_type == "PushEvent":
                commits = safe_get(event, "payload", {}).get("commits", [])
                activity_summary["commits"] += len(commits)
                activity_summary["repos_worked_on"].add(repo_name)

                if is_own_repo:
                    for commit in commits[: settings.max_recent_commits]:
                        activity_summary["recent_commits_detail"].append(
                            {
                                "repo": repo_name,
                                "message": safe_get(commit, "message", ""),
                                "date": event_date.strftime("%Y-%m-%d"),
                            }
                        )
                elif not is_fork_of_own:
                    # Only count as contribution if not a fork of own repo
                    activity_summary["repos_contributed"].add(repo_name)

            elif event_type == "PullRequestEvent":
                activity_summary["prs_created"] += 1
                if not is_own_repo and not is_fork_of_own:
                    activity_summary["collaboration_repos"].add(repo_name)

            elif event_type == "PullRequestReviewEvent":
                activity_summary["prs_reviewed"] += 1

            elif event_type == "IssuesEvent":
                if safe_get(event, "payload", {}).get("action") == "opened":
                    activity_summary["issues_opened"] += 1

            elif event_type == "IssueCommentEvent":
                activity_summary["issues_commented"] += 1

        # Convert sets to lists
        activity_summary["repos_worked_on"] = list(activity_summary["repos_worked_on"])
        activity_summary["repos_contributed"] = list(
            activity_summary["repos_contributed"]
        )
        activity_summary["collaboration_repos"] = list(
            activity_summary["collaboration_repos"]
        )

        return activity_summary

    def extract_repo_insights(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from a repository."""
        description = safe_get(repo, "description", "") or ""
        tech_keywords = {
            "frontend": ["react", "vue", "angular", "svelte", "next.js", "nuxt"],
            "backend": ["django", "flask", "fastapi", "express", "nest.js", "spring"],
            "mobile": ["react native", "flutter", "swift", "kotlin", "ionic"],
            "devops": ["docker", "kubernetes", "k8s", "terraform", "ansible", "ci/cd"],
            "data": ["pandas", "numpy", "tensorflow", "pytorch", "spark", "airflow"],
            "cloud": ["aws", "azure", "gcp", "cloud", "serverless", "lambda"],
        }

        identified_categories = []
        desc_lower = description.lower()
        for category, keywords in tech_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                identified_categories.append(category)

        return {
            "categories": identified_categories,
            "has_docs": bool(safe_get(repo, "has_wiki") or safe_get(repo, "has_pages")),
            "is_maintained": safe_get(repo, "updated_at", "")
            > (datetime.now() - timedelta(days=180)).isoformat(),
        }
