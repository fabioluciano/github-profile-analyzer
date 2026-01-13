# GitHub Profile Analyzer

Ferramenta CLI para analisar perfis do GitHub e gerar README automaticamente usando Gemini AI.

## Funcionalidades

- Analisa repositórios com estrela e próprios
- Identifica tendências e tópicos emergentes
- Rastreia atividade recente (commits, PRs, issues)
- Compara com análises anteriores
- Gera README em português e inglês usando Gemini AI
- Atualiza automaticamente o repositório de perfil via GitHub Actions

## Instalação

```bash
uv sync
```

## Configuração

Crie um arquivo `.env`:

```env
GITHUB_TOKEN=seu_token
GITHUB_USERNAME=seu_usuario
GEMINI_API_KEY=sua_chave
OUTPUT_DIR=.  # opcional, diretório de saída dos READMEs
```

## Uso Local

```bash
uv run github-analyzer
```

## GitHub Actions

Este repositório inclui um workflow que atualiza automaticamente o repositório de perfil.

### Secrets necessários

Configure no repositório:

- `GH_TOKEN` - Token do GitHub para leitura de dados (stars, repos, eventos)
- `GEMINI_API_KEY` - Chave da API do Gemini
- `PROFILE_REPO_PAT` - Token com permissão de escrita no repo de perfil

### Trigger manual

Vá em **Actions** > **Update GitHub Profile** > **Run workflow**

## Estrutura

```
src/
├── main.py              # Entrada
├── analysis.py          # Orquestrador
├── github_analyzer.py   # API do GitHub
├── gemini_generator.py  # Geração com Gemini
├── data_exporter.py     # Exportação
├── config.py            # Configurações
├── models.py            # Modelos Pydantic
└── utils.py             # Utilitários
```

## Saída

- `README.md` - Versão principal (português)
- `README.pt-br.md` - Português
- `README.en.md` - Inglês
