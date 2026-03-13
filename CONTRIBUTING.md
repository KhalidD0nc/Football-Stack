# Contributing to Leagues Data Project

First off, thank you for considering contributing to the Leagues Data Project! It's people like you that make the open source community such a great place to learn, inspire, and create.

## Getting Started

1. **Fork the repository** and clone it locally.
2. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## What to Contribute

**✅ Supported Contributions:**
- Adding new leagues and seasons to the configuration.
- Enhancing or adding new data models in the **dbt layer** (`leagues_data_dbt/`).
- Improving documentation (`docs/` or `README.md`).

**🚫 Ingestion Layer Changes:**
- Direct edits to the **Ingestion Layer** (e.g., Python scripts fetching data from API-Football) are **NOT** open for direct pull requests at this time. 
- If you find a bug or have a suggestion for the ingestion logic, please **open an issue** to discuss it first.

## Development Setup

1. **Python Environment**: Initialize a virtual environment and install dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**: Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   At minimum, you need `API_FOOTBALL_KEY`, `LEAGUE_ID`, and `SEASON`. Storage defaults to the local filesystem (`data_lake/` directory).

3. **dbt Setup**:
   To work on data models, navigate to the `leagues_data_dbt` directory and install dependencies:
   ```bash
   cd leagues_data_dbt
   dbt deps
   ```

## Workflow

- **Python Code**: Ensure your code is clean and tested. Run existing tests before submitting a PR.
  ```bash
  pytest tests/
  ```
- **dbt Models**: When adding new models or modifying existing ones, ensure your models compile and pass dbt tests.
  ```bash
  dbt build -s your_modified_model
  ```
- **Documentation**: Update the `docs/` or `README.md` if your changes impact the project architecture or how to run it.

## Pull Request Guidelines

1. Make sure your PR description clearly states what you changed and why.
2. Link any relevant issues to the PR.
3. Keep your commits concise and use descriptive commit messages.

Thank you for contributing!
