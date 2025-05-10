# Trending Now - Movie & TV Show Analytics

A modern web application that provides users with up-to-date information on newly released movies and TV shows, featuring LLM-generated insights including genre classifications, review summaries, vibe-based scores, and relevant tags.

## Features

- Interactive D3.js visualization of trending movies and shows
- LLM-powered content analysis:
  - Genre classification
  - Review summarization
  - Vibe score generation
  - Descriptive tag generation
- Regular updates through automated data collection
- Modern, responsive web interface

## Project Structure

```
trending-now-app/
├── frontend/             # HTML, CSS, JS, D3.js code
├── backend/              # FastAPI application
├── mlops/               # MLOps pipelines and scripts
├── infrastructure/      # Terraform IaC
├── data/                # Managed by DVC
├── notebooks/           # Jupyter notebooks for EDA
└── .github/workflows/   # GitHub Actions CI/CD
```

## Setup for Development

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Set up pre-commit hooks:
```bash
pre-commit install
```

## Data Collection

Initial data collection and exploration is done through Jupyter notebooks in the `notebooks/` directory.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Submit a Pull Request

## License

MIT License - See LICENSE file for details
