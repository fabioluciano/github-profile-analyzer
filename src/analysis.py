"""Main analysis module combining all components."""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .config import settings
from .data_exporter import DataExporter
from .gemini_generator import GeminiContentGenerator
from .github_analyzer import GitHubAnalyzer
from .utils import (
    format_topics,
    safe_get,
    validate_github_username,
)

logger = logging.getLogger(__name__)


class GitHubProfileAnalyzer:
    """Main analyzer that orchestrates the entire analysis process."""

    def __init__(self):
        self.analyzer = GitHubAnalyzer(settings.github_token)
        self.generator = GeminiContentGenerator(settings.gemini_api_key)
        self.exporter = DataExporter()

    def identify_trends(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify emerging trends and patterns from the GitHub data.

        Args:
            all_data: Comprehensive data dictionary containing starred repos, own repos, etc.

        Returns:
            Dictionary with trends analysis including emerging topics, languages, and expertise areas.
        """
        trends = {
            "emerging_topics": [],
            "growing_languages": [],
            "focus_shift": None,
            "activity_pattern": None,
            "expertise_areas": [],
        }

        # Emerging topics
        recent_topics = []
        for repo in all_data["recent_stars"]:
            if safe_get(repo, "topics"):
                recent_topics.extend(safe_get(repo, "topics", "").split("|"))

        recent_topic_counts = Counter(recent_topics)
        all_topic_counts = Counter(all_data["all_topics"])

        for topic, recent_count in recent_topic_counts.most_common(10):
            total_count = all_topic_counts[topic]
            if recent_count / total_count > 0.3:  # 30% recent
                trends["emerging_topics"].append(
                    {
                        "topic": topic,
                        "recent_count": recent_count,
                        "total_count": total_count,
                    }
                )

        # Growing languages
        recent_languages = [
            repo["language"]
            for repo in all_data["recent_stars"]
            if safe_get(repo, "language")
        ]
        recent_lang_counts = Counter(recent_languages)

        for lang, count in recent_lang_counts.most_common(5):
            if count >= 2:
                trends["growing_languages"].append(lang)

        # Activity pattern
        if all_data["activity"]["commits"] > 50:
            trends["activity_pattern"] = "highly_active"
        elif all_data["activity"]["commits"] > 20:
            trends["activity_pattern"] = "active"
        elif all_data["activity"]["commits"] > 5:
            trends["activity_pattern"] = "moderate"
        else:
            trends["activity_pattern"] = "light"

        # Expertise areas
        for category, count in all_data["repo_categories"].items():
            if count >= 3:
                trends["expertise_areas"].append(category)

        return trends

    def extract_comprehensive_data(
        self,
        starred_repos: List[Dict[str, Any]],
        user_repos: List[Dict[str, Any]],
        activity: Dict[str, Any],
        user_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract comprehensive data for advanced analysis."""
        all_data = {
            "starred": [],
            "own_repos": [],
            "activity": activity,
            "user_info": user_info,
            "all_topics": [],
            "all_languages": [],
            "recent_stars": [],
            "topic_timeline": defaultdict(list),
            "language_evolution": defaultdict(int),
            "repo_categories": defaultdict(int),
        }

        thirty_days_ago = datetime.now() - timedelta(days=settings.recent_days)
        ninety_days_ago = datetime.now() - timedelta(days=settings.very_recent_days)

        own_repos_names = {repo["full_name"] for repo in user_repos}

        # Process starred repos
        for item in starred_repos:
            repo = item["repo"]
            starred_at = datetime.strptime(item["starred_at"], "%Y-%m-%dT%H:%M:%SZ")

            topics = safe_get(repo, "topics", [])
            all_data["all_topics"].extend(topics)

            language = safe_get(repo, "language", "")
            if language:
                all_data["all_languages"].append(language)
                all_data["language_evolution"][language] += 1

            # Repo insights
            insights = self.analyzer.extract_repo_insights(repo)
            for category in insights["categories"]:
                all_data["repo_categories"][category] += 1

            # Topic timeline
            for topic in topics:
                all_data["topic_timeline"][topic].append(starred_at)

            repo_info = {
                "starred_at": item["starred_at"],
                "name": repo["full_name"],
                "description": safe_get(repo, "description", ""),
                "url": repo["html_url"],
                "language": language,
                "topics": format_topics(topics),
                "stars": safe_get(repo, "stargazers_count", 0),
                "forks": safe_get(repo, "forks_count", 0),
                "is_recent": starred_at > thirty_days_ago,
                "is_very_recent": starred_at > ninety_days_ago,
                "categories": format_topics(insights["categories"]),
            }

            all_data["starred"].append(repo_info)

            if repo_info["is_recent"]:
                all_data["recent_stars"].append(repo_info)

        # Process own repos
        for repo in user_repos:
            if safe_get(repo, "fork", False):
                continue

            topics = safe_get(repo, "topics", [])
            all_data["all_topics"].extend(topics)

            language = safe_get(repo, "language", "")
            if language:
                all_data["all_languages"].append(language)

            updated_at = datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            is_active = updated_at > thirty_days_ago

            insights = self.analyzer.extract_repo_insights(repo)

            repo_info = {
                "name": repo["full_name"],
                "description": safe_get(repo, "description", ""),
                "url": repo["html_url"],
                "language": language,
                "topics": format_topics(topics),
                "stars": safe_get(repo, "stargazers_count", 0),
                "forks": safe_get(repo, "forks_count", 0),
                "updated_at": repo["updated_at"],
                "is_active": is_active,
                "is_private": safe_get(repo, "private", False),
                "has_issues": safe_get(repo, "has_issues", False),
                "open_issues": safe_get(repo, "open_issues_count", 0),
                "categories": format_topics(insights["categories"]),
                "size_kb": safe_get(repo, "size", 0),
            }

            all_data["own_repos"].append(repo_info)

        # Sort own repos by activity
        all_data["own_repos"].sort(key=lambda x: x["updated_at"], reverse=True)

        return all_data

    def run_analysis(self) -> None:
        """Run the complete analysis pipeline."""
        logger.info("🚀 GitHub Profile Analysis Tool")
        logger.info("=" * 70)
        logger.info(f"User: {settings.github_username}")
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not validate_github_username(settings.github_username):
            print("⚠ Invalid GitHub username")
            return

        # 1. Fetch user info
        print("👤 Fetching user info...")
        user_info = self.analyzer.get_user_info(settings.github_username)
        print(f"  → Name: {safe_get(user_info, 'name', 'Not available')}")
        print(f"  → Bio: {safe_get(user_info, 'bio', 'Not available')}")

        # 2. Fetch starred repos
        print("📡 Fetching starred repos...")
        starred_repos = self.analyzer.get_starred_repos(settings.github_username)
        print(f"  → Total starred: {len(starred_repos)}")

        # 3. Fetch own repos
        print("📦 Fetching own repos...")
        user_repos = self.analyzer.get_user_repos(settings.github_username)
        print(f"  → Total own repos: {len(user_repos)}")

        # 4. Fetch recent activity
        print("🔄 Fetching recent activity...")
        recent_activity = self.analyzer.get_recent_activity(settings.github_username)
        print(f"  → Recent events: {len(recent_activity)}")

        # 5. Analyze activity
        print("📊 Analyzing activity...")
        activity_summary = self.analyzer.analyze_recent_activity(
            recent_activity, {repo["full_name"] for repo in user_repos}
        )
        print(f"  → Commits: {activity_summary['commits']}")
        print(f"  → PRs created: {activity_summary['prs_created']}")

        # 6. Extract comprehensive data
        print("📋 Extracting comprehensive data...")
        all_data = self.extract_comprehensive_data(
            starred_repos, user_repos, activity_summary, user_info
        )
        print(f"  → Unique topics: {len(set(all_data['all_topics']))}")

        # 7. Identify trends
        print("📈 Identifying trends...")
        trends = self.identify_trends(all_data)
        print(f"  → Emerging topics: {len(trends['emerging_topics'])}")
        print(
            f"  → Growing languages: {', '.join(trends['growing_languages']) if trends['growing_languages'] else 'None'}"
        )

        # 8. Generate content
        print("📝 Generating profile content...")
        profile_content = self.generator.generate_profile_content(all_data, trends)

        # 9. Update README
        print("📂 Updating README...")
        if self.exporter.update_readme(profile_content):
            print("✓ Analysis completed successfully!")
        else:
            print("⚠ Failed to update README")
