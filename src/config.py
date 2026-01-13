"""Configuration settings for the GitHub analysis tool."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    github_username: str = "fabioluciano"
    github_token: str | None = None
    gemini_api_key: str | None = None

    readme_filename: str = "README.md"

    # API settings
    github_api_base: str = "https://api.github.com"
    gemini_model: str = "gemini-2.5-flash"
    blog_rss_url: str = "https://fabioluciano.com/rss.xml"

    # Analysis settings
    recent_days: int = 30
    very_recent_days: int = 90
    max_recent_commits: int = 10
    max_active_repos: int = 5
    max_recent_stars: int = 12

    # Profile expertise areas
    expertise_areas: list[str] = [
        "Arquitetura Cloud & FinOps",
        "Developer Experience (DevEx)",
        "DevOps & CI/CD Moderno",
        "DevSecOps & Segurança",
        "Engenharia de Plataforma (IDP)",
        "Engenharia de Software",
        "Kubernetes & Containers",
        "Observabilidade & SRE",
    ]

    # Contact info
    email: str = "me@fabioluciano.com"
    linkedin: str = "fabioluciano"
    twitter: str = "fabioluciano"
    website: str = "https://fabioluciano.com"

    # Output settings
    output_dir: str = "."  # Directory where READMEs will be saved
    profile_repo: str = "fabioluciano/fabioluciano"  # Target profile repo

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
