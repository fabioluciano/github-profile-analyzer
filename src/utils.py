"""Utility functions for the GitHub analysis tool."""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


def setup_directories(dir_path: str) -> None:
    """Create directories if they don't exist."""
    os.makedirs(dir_path, exist_ok=True)


def get_timestamp() -> str:
    """Get current timestamp in YYYYMMDD_HHMMSS format."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def is_recent(date_str: str, days: int = 30) -> bool:
    """Check if a date string is within the last N days."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return date > datetime.now() - timedelta(days=days)
    except ValueError:
        return False


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    if not isinstance(data, dict):
        return default
    value = data.get(key)
    return value if value is not None else default


def validate_github_username(username: str) -> bool:
    """Validate GitHub username format."""
    import re

    return bool(re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username))


def format_topics(topics: Optional[List[str]]) -> str:
    """Format topics list to string."""
    return "|".join(topics) if topics else ""


def truncate_text(text: Optional[str], max_length: int = 80) -> str:
    """Truncate text to max length with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def fetch_blog_posts(rss_url: str, max_posts: int = 5) -> List[Dict[str, str]]:
    """Fetch recent blog posts from RSS feed."""
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            return []

        posts = []
        for item in channel.findall("item")[:max_posts]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            description = item.find("description")

            posts.append({
                "title": title.text if title is not None else "",
                "link": link.text if link is not None else "",
                "pub_date": pub_date.text if pub_date is not None else "",
                "description": truncate_text(description.text if description is not None else "", 150),
            })

        return posts
    except Exception:
        return []
