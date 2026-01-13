"""Gemini AI content generation module."""

import json
from collections import Counter
from typing import Any, Dict, List, Optional

import tenacity
from google import genai
from google.genai import types

from .config import settings
from .utils import fetch_blog_posts, format_topics, safe_get, truncate_text


class GeminiContentGenerator:
    """Handles content generation using Gemini AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate_profile_content(
        self, all_data: Dict[str, Any], trends: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Generate README content using Gemini AI."""
        if not self.client:
            print("⚠ GEMINI_API_KEY not configured")
            return None

        # Prepare data for prompt
        topic_counts = Counter(all_data["all_topics"])
        language_counts = Counter(all_data["all_languages"])

        active_repos = [
            {
                **repo,
                "description": safe_get(repo, "description", ""),
                "topics": safe_get(repo, "topics", []),
            }
            for repo in all_data["own_repos"]
            if safe_get(repo, "is_active")
        ][: settings.max_active_repos]

        recent_work = []
        for commit in all_data["activity"]["recent_commits_detail"][: settings.max_recent_commits]:
            recent_work.append(f"  • {commit['repo']}: {commit['message'][:60]}...")

        collaboration_context = ""
        if all_data["activity"]["repos_contributed"]:
            collaboration_context = f"\n**Contribuindo para projetos externos:**\n" + "\n".join(
                [f"  • {repo}" for repo in all_data["activity"]["repos_contributed"][:5]]
            )

        # Fetch blog posts
        blog_posts = fetch_blog_posts(settings.blog_rss_url, max_posts=5)
        blog_section = ""
        if blog_posts:
            blog_section = "\n## ÚLTIMOS POSTS DO BLOG\n" + "\n".join(
                [f"- [{p['title']}]({p['link']}) - {p['pub_date']}" for p in blog_posts]
            )

        prompt = f"""Você é um especialista em criar perfis GitHub profissionais e envolventes. Analise os dados abaixo e crie um README.md excepcional que conte a história profissional do desenvolvedor de forma autêntica e impactante.

# CONTEXTO COMPLETO DO DESENVOLVEDOR

## INFORMAÇÕES PESSOAIS
- Nome: {safe_get(all_data["user_info"], "name", settings.github_username)}
- Bio atual: {safe_get(all_data["user_info"], "bio", "Não definida")}
- Localização: {safe_get(all_data["user_info"], "location", "Não informada")}
- Empresa: {safe_get(all_data["user_info"], "company", "Não informada")}
- Repositórios públicos: {safe_get(all_data["user_info"], "public_repos", 0)}
- Seguidores: {safe_get(all_data["user_info"], "followers", 0)}

## ÁREAS DE EXPERTISE (OBRIGATÓRIO INCLUIR NO "SOBRE MIM" E "FOCO ATUAL")
{chr(10).join([f"- {area}" for area in settings.expertise_areas])}

## ATIVIDADE RECENTE (Últimos {settings.recent_days} dias)
- **Commits:** {all_data["activity"]["commits"]} commits
- **Pull Requests:** {all_data["activity"]["prs_created"]} criados, {
            all_data["activity"]["prs_reviewed"]
        } revisados
- **Issues:** {all_data["activity"]["issues_opened"]} abertas, {
            all_data["activity"]["issues_commented"]
        } comentadas
- **Repositórios trabalhados:** {len(all_data["activity"]["repos_worked_on"])} repos
- **Padrão de atividade:** {trends["activity_pattern"]}

## TRABALHO RECENTE EM DETALHES
{
            chr(10).join(recent_work)
            if recent_work
            else "Nenhum commit recente detectado em repos públicos"
        }
{collaboration_context}

## REPOSITÓRIOS PRÓPRIOS ATIVOS
{
            chr(10).join(
                [
                    f"- **{r['name']}** [{r['language']}]: {truncate_text(safe_get(r, 'description', 'Sem descrição'), 80)} (⭐ {safe_get(r, 'stars', 0)}, 🍴 {safe_get(r, 'forks', 0)})"
                    for r in active_repos
                ]
            )
            if active_repos
            else "Sem atividade recente em repositórios próprios"
        }

## REPOSITÓRIOS COM ESTRELA RECENTES ({len(all_data["recent_stars"])} nos últimos {
            settings.recent_days
        } dias)
{
            chr(10).join(
                [
                    f"- **{r['name']}** [{r['language']}]: {truncate_text(safe_get(r, 'description', 'Sem descrição'), 80)}"
                    + chr(10)
                    + f"  Tópicos: {format_topics(safe_get(r, 'topics', '').split('|') if safe_get(r, 'topics') else [])}"
                    for r in all_data["recent_stars"][: settings.max_recent_stars]
                ]
            )
        }

## ANÁLISE DE TENDÊNCIAS

### Tópicos Emergentes (foco recente)
{
            chr(10).join(
                [
                    f"- **{t['topic']}**: {t['recent_count']} de {t['total_count']} ocorrências são recentes ({int(t['recent_count'] / t['total_count'] * 100)}%)"
                    for t in trends["emerging_topics"][:8]
                ]
            )
            if trends["emerging_topics"]
            else "Nenhum tópico emergente identificado"
        }

### Linguagens em Crescimento
{
            ", ".join(trends["growing_languages"])
            if trends["growing_languages"]
            else "Nenhuma tendência identificada"
        }

### Áreas de Expertise Identificadas
{", ".join(trends["expertise_areas"]) if trends["expertise_areas"] else "Analisando..."}

## ESTATÍSTICAS GERAIS
- **Total de estrelas dadas:** {len(all_data["starred"])} repositórios
- **Repositórios próprios:** {len(all_data["own_repos"])} (não-forks)
- **Tópicos únicos explorados:** {len(set(all_data["all_topics"]))}

### Top 25 Tópicos (ordenado por frequência)
{", ".join([f"{t} ({c})" for t, c in topic_counts.most_common(25)])}

### Top 12 Linguagens
{", ".join([f"{l} ({c})" for l, c in language_counts.most_common(12)])}
{blog_section}

---

# SUA MISSÃO

Crie um README.md profissional, moderno e impactante seguindo estas diretrizes:

## ESTRUTURA OBRIGATÓRIA

### 1. HEADER IMPACTANTE
- Título com nome/username
- Subtítulo que captura a essência profissional (infira do contexto)
- Se tiver bio, use como inspiração mas melhore
- Badges relevantes: localização, redes sociais

### 2. "👋 Sobre Mim" (2-3 parágrafos)
- Introdução autêntica e profissional
- Mencione o papel/especialização inferido dos dados
- **OBRIGATÓRIO**: Mencione TODAS as áreas de expertise listadas acima
- Destaque expertise principal (baseado em tópicos/linguagens dominantes)
- Adicione um toque pessoal se houver informações disponíveis

### 3. "🎯 Foco Atual & Interesses"
- **OBRIGATÓRIO**: Liste TODAS as 8 áreas de expertise fornecidas acima como foco atual
- Use bullet points com emojis relevantes para cada área:
  * ☁️ Arquitetura Cloud & FinOps
  * 👨‍💻 Developer Experience (DevEx)
  * 🔄 DevOps & CI/CD Moderno
  * 🔐 DevSecOps & Segurança
  * 🏗️ Engenharia de Plataforma (IDP)
  * ⚙️ Engenharia de Software
  * ☸️ Kubernetes & Containers
  * 📊 Observabilidade & SRE
- Seja ESPECÍFICO ao descrever cada área

### 4. "🚀 Projetos em Desenvolvimento"
- Baseado em commits recentes e repos ativos
- Mencione tecnologias específicas sendo usadas
- Se houver pouca atividade pública, foque em explorações (stars recentes)
- Máximo 3-4 itens

### 5. "🌱 Aprendendo Agora"
- Tecnologias/frameworks novos (stars recentes, tópicos emergentes)
- Áreas de interesse crescente
- 3-5 itens específicos

### 6. "💼 Experiência & Stack Tecnológica"

Organize em categorias relevantes baseadas nos dados:
- **Linguagens**: principais linguagens com badges
- **Frameworks/Bibliotecas**: principais ferramentas
- **DevOps & Ferramentas**: se relevante
- **Databases**: se identificadas
- **Cloud/Infraestrutura**: se relevante

Use badges do shields.io:
`![Nome](https://img.shields.io/badge/Nome-HEX?style=for-the-badge&logo=nome&logoColor=white)`

Cores sugeridas por tecnologia (use HEX sem #):
- Python: 3776AB
- JavaScript: F7DF1E
- TypeScript: 3178C6
- Go: 00ADD8
- Rust: 000000
- Docker: 2496ED
- Kubernetes: 326CE5
- React: 61DAFB
- Vue: 4FC08D
- Node.js: 339933

### 7. "🏆 GitHub Trophies"
Inclua:
```markdown
<div align="center">
  <img src="https://github-profile-trophy.vercel.app/?username={
            settings.github_username
        }&theme=onedark&no-frame=true&no-bg=true&column=7"/>
</div>
```

### 8. "🤝 Contribuições & Colaboração"
- Se houver PRs externos, mencione
- Convite para colaboração
- Links para issues/discussions se aplicável

### 9. "📝 Últimos Posts do Blog"
- Se houver posts do blog disponíveis, liste os últimos 5
- Use o formato: [Título](link) - data
- Adicione link para o blog completo

### 10. "📫 Como me Encontrar"
- GitHub: {settings.github_username}
- Email: {settings.email}
- LinkedIn: {settings.linkedin}
- Twitter/X: {settings.twitter}
- Website/Blog: {settings.website}

## DIRETRIZES CRÍTICAS

1. **AUTENTICIDADE**: O conteúdo deve soar genuíno, não como marketing
2. **ESPECIFICIDADE**: Use nomes exatos de tecnologias, frameworks, conceitos
3. **EVIDÊNCIAS**: Tudo deve ser baseado nos dados reais fornecidos
4. **ATUALIDADE**: Priorize informações dos últimos {settings.recent_days}-{
            settings.very_recent_days
        } dias
5. **PROFISSIONALISMO**: Mantenha tom profissional mas acessível
6. **VISUAL**: Use emojis estrategicamente, não exagere
7. **CONCISÃO**: Cada seção deve ser scanning-friendly
8. **COERÊNCIA**: A narrativa deve fazer sentido como um todo

## INFERÊNCIAS INTELIGENTES

- Se muitos repos de infra: "especialista em infraestrutura"
- Se muitos repos frontend: "desenvolvedor frontend especializado"
- Se diversidade alta: "desenvolvedor full-stack versátil"
- Se foco em libraries: "open source contributor/maintainer"
- Padrão de commits intenso: "ativo em desenvolvimento"
- Muitas revisões de PR: "tem senso de code review e colaboração"

## PERSONALIZAÇÃO BASEADA EM PADRÕES

- Atividade alta → Destaque produtividade e engajamento
- Muitas linguagens → Destaque versatilidade
- Foco em uma stack → Destaque especialização profunda
- Contribuições externas → Destaque colaboração open source
- Repos bem documentados → Mencione foco em qualidade/documentação

## FORMATO DE SAÍDA

**IMPORTANTE**: Gere o README em DUAS versões completas:

1. **VERSÃO EM PORTUGUÊS (BRASIL)** - Primeiro
2. **VERSÃO EM INGLÊS** - Depois

Separe as duas versões com o seguinte marcador exato:
```
---LANG_SEPARATOR---
```

Cada versão deve:
- Ser completa e independente
- Ter links para a outra versão no topo (ex: "🇧🇷 Português | [🇺🇸 English](README.en.md)" e "[🇧🇷 Português](README.pt-br.md) | 🇺🇸 English")
- Manter o mesmo conteúdo, apenas traduzido
- Adaptar expressões idiomáticas de forma natural

Retorne APENAS o conteúdo Markdown completo e pronto para uso.
Sem explicações, sem meta-comentários.
Comece diretamente com o conteúdo do README em português.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                ),
            )
            content = response.text

            # Clean up
            content = content.replace("```markdown", "").replace("```", "").strip()

            # Split into Portuguese and English versions
            if "---LANG_SEPARATOR---" in content:
                parts = content.split("---LANG_SEPARATOR---")
                return {
                    "pt-br": parts[0].strip(),
                    "en": parts[1].strip() if len(parts) > 1 else parts[0].strip(),
                }
            else:
                # Fallback: return same content for both
                return {"pt-br": content, "en": content}
        except Exception as e:
            print(f"⚠ Error using Gemini API: {e}")
            fallback = self._generate_fallback_readme(all_data, trends)
            return {"pt-br": fallback, "en": fallback}

    def _generate_fallback_readme(
        self, all_data: Dict[str, Any], trends: Dict[str, Any]
    ) -> str:
        """Generate a basic README when AI fails."""
        user_info = all_data["user_info"]
        username = user_info.get("name", settings.github_username)

        return f"""# {username}

## About Me

I'm a developer with {len(all_data["starred"])} starred repositories and {len(all_data["own_repos"])} personal projects.

## Recent Activity

- {all_data["activity"]["commits"]} commits in the last {settings.recent_days} days
- {all_data["activity"]["prs_created"]} pull requests created
- {all_data["activity"]["prs_reviewed"]} pull requests reviewed

## Technologies

{", ".join(trends["expertise_areas"]) if trends["expertise_areas"] else "Exploring various technologies"}

## GitHub Trophies

![GitHub Trophies](https://github-profile-trophy.vercel.app/?username={settings.github_username}&theme=onedark&no-frame=true&no-bg=true&column=7)
"""
