"""Pydantic models for data validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    public_repos: int = 0
    followers: int = 0


class GitHubRepo(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    stargazers_count: int = 0
    forks_count: int = 0
    updated_at: str
    has_wiki: bool = False
    has_pages: bool = False
    private: bool = False
    fork: bool = False
    size: int = 0
    has_issues: bool = False
    open_issues_count: int = 0


class StarredRepo(BaseModel):
    """Starred repository model."""

    starred_at: str
    repo: GitHubRepo


class GitHubEvent(BaseModel):
    """GitHub event model."""

    id: str
    type: str
    created_at: str
    repo: Dict[str, str]
    payload: Dict[str, Any] = Field(default_factory=dict)


class ActivitySummary(BaseModel):
    """Activity summary model."""

    commits: int = 0
    prs_created: int = 0
    prs_reviewed: int = 0
    issues_opened: int = 0
    issues_commented: int = 0
    repos_worked_on: List[str] = Field(default_factory=list)
    repos_contributed: List[str] = Field(default_factory=list)
    recent_commits_detail: List[Dict[str, Any]] = Field(default_factory=list)
    collaboration_repos: List[str] = Field(default_factory=list)


class RepoInsights(BaseModel):
    """Repository insights model."""

    categories: List[str] = Field(default_factory=list)
    has_docs: bool = False
    is_maintained: bool = False


class Trends(BaseModel):
    """Trends analysis model."""

    emerging_topics: List[Dict[str, Any]] = Field(default_factory=list)
    growing_languages: List[str] = Field(default_factory=list)
    focus_shift: Optional[str] = None
    activity_pattern: Optional[str] = None
    expertise_areas: List[str] = Field(default_factory=list)


class Changes(BaseModel):
    """Changes comparison model."""

    is_first_run: bool = True
    new_repos_count: int = 0
    new_topics: List[str] = Field(default_factory=list)
    new_languages: List[str] = Field(default_factory=list)
    activity_change: Optional[str] = None


class AnalysisData(BaseModel):
    """Complete analysis data model."""

    starred: List[Dict[str, Any]] = Field(default_factory=list)
    own_repos: List[Dict[str, Any]] = Field(default_factory=list)
    activity: ActivitySummary
    user_info: Dict[str, Any] = Field(default_factory=dict)
    all_topics: List[str] = Field(default_factory=list)
    all_languages: List[str] = Field(default_factory=list)
    recent_stars: List[Dict[str, Any]] = Field(default_factory=list)
    topic_timeline: Dict[str, List[Any]] = Field(default_factory=dict)
    language_evolution: Dict[str, int] = Field(default_factory=dict)
    repo_categories: Dict[str, int] = Field(default_factory=dict)
