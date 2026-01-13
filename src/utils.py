"""Utility functions for the GitHub analysis tool."""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
import yaml


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


def fetch_resume_data(base_url: str) -> Dict[str, Any]:
    """Fetch and parse resume data from GitHub repository.

    Args:
        base_url: Base URL for raw GitHub content (e.g.,
            https://raw.githubusercontent.com/user/repo/main/data)

    Returns:
        Dictionary with parsed resume data including skills categories.
    """
    resume_data: Dict[str, Any] = {
        "skills": {},
        "certifications": [],
    }

    # Define badge colors for common technologies
    badge_colors = {
        # Languages
        "go": "00ADD8", "python": "3776AB", "shell": "121011", "bash": "121011",
        "typescript": "3178C6", "rust": "000000", "lua": "2C2D72",
        # Cloud
        "aws": "232F3E", "azure": "0078D4", "gcp": "4285F4",
        # Containers & Orchestration
        "kubernetes": "326CE5", "docker": "2496ED", "helm": "0F1689",
        "kustomize": "326CE5", "podman": "892CA0",
        # CI/CD & GitOps
        "argocd": "EF7B4D", "github actions": "2088FF", "gitlab ci": "FC6D26",
        "tekton": "FD495C", "jenkins": "D24939",
        # IaC
        "terraform": "7B42BC", "ansible": "EE0000", "pulumi": "8A3391",
        "crossplane": "326CE5",
        # Observability
        "prometheus": "E6522C", "grafana": "F46800", "opentelemetry": "000000",
        "jaeger": "66CFE3",
        # DevSecOps
        "sonarqube": "4E9BCD", "snyk": "4C4A73", "trivy": "1904DA",
        "opa": "7D9199", "gatekeeper": "7D9199",
        # Service Mesh
        "istio": "466BB0", "linkerd": "2BEDA7", "envoy": "AC6199", "cilium": "F8C517",
        # Databases & Messaging
        "postgresql": "4169E1", "redis": "DC382D", "mongodb": "47A248",
        "kafka": "231F20", "rabbitmq": "FF6600",
    }

    try:
        # Fetch resume.ptbr.yaml
        response = requests.get(f"{base_url}/resume.ptbr.yaml", timeout=10)
        response.raise_for_status()
        ptbr_data = yaml.safe_load(response.text)

        # Extract skills from resume
        if ptbr_data and "skills" in ptbr_data:
            for skill_category in ptbr_data["skills"]:
                category_name = skill_category.get("name", "")
                keywords = skill_category.get("keywords", [])
                if category_name and keywords:
                    resume_data["skills"][category_name] = keywords

        # Try to fetch common.yaml for certifications
        try:
            common_response = requests.get(f"{base_url}/common.yaml", timeout=10)
            common_response.raise_for_status()
            common_data = yaml.safe_load(common_response.text)
            if common_data and "certifications" in common_data:
                resume_data["certifications"] = common_data["certifications"]
        except Exception:
            pass

    except Exception as e:
        print(f"⚠ Error fetching resume data: {e}")
        return resume_data

    # Add badge colors for reference
    resume_data["badge_colors"] = badge_colors

    return resume_data


def format_skills_for_prompt(resume_data: Dict[str, Any]) -> str:
    """Format skills data into a string for the Gemini prompt.

    Args:
        resume_data: Resume data dictionary from fetch_resume_data.

    Returns:
        Formatted string with skills categories and technologies with valid badges only.
    """
    if not resume_data.get("skills"):
        return "Dados do currículo não disponíveis."

    # Technologies with valid shields.io logos (logo parameter works)
    # Format: "display_name": ("logo_name", "hex_color")
    valid_badges = {
        # Languages
        "Go": ("go", "00ADD8"),
        "Python": ("python", "3776AB"),
        "Shell": ("gnubash", "121011"),
        "Bash": ("gnubash", "121011"),
        "TypeScript": ("typescript", "3178C6"),
        "Rust": ("rust", "000000"),
        "Lua": ("lua", "2C2D72"),
        # Cloud
        "AWS": ("amazonwebservices", "232F3E"),
        "Azure": ("microsoftazure", "0078D4"),
        "GCP": ("googlecloud", "4285F4"),
        # Containers & Orchestration
        "Kubernetes": ("kubernetes", "326CE5"),
        "Docker": ("docker", "2496ED"),
        "Helm": ("helm", "0F1689"),
        "Podman": ("podman", "892CA0"),
        # CI/CD & GitOps
        "ArgoCD": ("argo", "EF7B4D"),
        "GitHub Actions": ("githubactions", "2088FF"),
        "GitLab CI": ("gitlab", "FC6D26"),
        "Tekton": ("tekton", "FD495C"),
        "Jenkins": ("jenkins", "D24939"),
        # IaC
        "Terraform": ("terraform", "7B42BC"),
        "Ansible": ("ansible", "EE0000"),
        "Pulumi": ("pulumi", "8A3391"),
        "Crossplane": ("crossplane", "326CE5"),
        # Observability
        "Prometheus": ("prometheus", "E6522C"),
        "Grafana": ("grafana", "F46800"),
        "OpenTelemetry": ("opentelemetry", "000000"),
        "Jaeger": ("jaeger", "66CFE3"),
        # DevSecOps
        "SonarQube": ("sonarqube", "4E9BCD"),
        "Snyk": ("snyk", "4C4A73"),
        "Trivy": ("trivy", "1904DA"),
        # Service Mesh
        "Istio": ("istio", "466BB0"),
        "Envoy": ("envoyproxy", "AC6199"),
        "Cilium": ("cilium", "F8C517"),
        # Databases & Messaging
        "PostgreSQL": ("postgresql", "4169E1"),
        "Redis": ("redis", "DC382D"),
        "MongoDB": ("mongodb", "47A248"),
        "Apache Kafka": ("apachekafka", "231F20"),
        "RabbitMQ": ("rabbitmq", "FF6600"),
        # Other tools
        "Git": ("git", "F05032"),
        "Linux": ("linux", "FCC624"),
        "Nginx": ("nginx", "009639"),
        "HashiCorp Vault": ("vault", "000000"),
    }

    lines = []
    lines.append("**REGRA IMPORTANTE**: Use badges APENAS para tecnologias listadas abaixo.")
    lines.append("NÃO misture badges com texto. Se a tecnologia não tem badge, NÃO a inclua.")
    lines.append("")

    # Group technologies by category
    category_mapping = {
        "Linguagens de Programação": ["Go", "Python", "Shell", "TypeScript", "Rust", "Lua"],
        "Cloud & FinOps": ["AWS", "Azure", "GCP"],
        "Orquestração de Containers": ["Kubernetes", "Docker", "Helm", "Podman"],
        "CI/CD & GitOps": ["ArgoCD", "GitHub Actions", "GitLab CI", "Tekton", "Jenkins"],
        "Infraestrutura como Código": ["Terraform", "Ansible", "Pulumi", "Crossplane"],
        "Observabilidade": ["Prometheus", "Grafana", "OpenTelemetry", "Jaeger"],
        "DevSecOps": ["SonarQube", "Snyk", "Trivy"],
        "Service Mesh & Redes": ["Istio", "Envoy", "Cilium"],
        "Bancos de Dados & Message Brokers": ["PostgreSQL", "Redis", "MongoDB", "Apache Kafka", "RabbitMQ"],
    }

    for category, techs in category_mapping.items():
        lines.append(f"#### {category}")
        badge_list = []
        for tech in techs:
            if tech in valid_badges:
                logo, color = valid_badges[tech]
                badge_list.append(
                    f"![{tech}](https://img.shields.io/badge/{tech.replace(' ', '_')}-{color}?style=for-the-badge&logo={logo}&logoColor=white)"
                )
        lines.append(" ".join(badge_list))
        lines.append("")

    return "\n".join(lines)
