"""Main entry point for the GitHub profile analysis tool."""

import logging

from .analysis import GitHubProfileAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    """Run the GitHub profile analysis."""
    analyzer = GitHubProfileAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
