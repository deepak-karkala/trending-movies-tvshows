# Directory Structure

##
### Section 3.6: Project Directory Structure (Organizing the Kitchen Pantry and Recipe Books)

A well-organized directory structure is key for maintainability.

*   **Proposed Layout:**

    ```
    trending-now-app/
    ├── frontend/             # HTML, CSS, JS, D3.js code
    │   ├── css/
    │   ├── js/
    │   └── index.html
    ├── backend/              # FastAPI application
    │   ├── app/
    │   │   ├── routers/      # API route definitions
    │   │   ├── services/     # Business logic, LLM integration
    │   │   ├── models/       # Pydantic models for request/response
    │   │   └── main.py       # FastAPI app instantiation
    │   ├── tests/            # Pytest tests for backend
    │   │   ├── unit/
    │   │   └── integration/
    │   └── Dockerfile        # For the FastAPI service
    ├── mlops/
    │   ├── pipelines/        # Airflow DAG definitions
    │   │   ├── data_ingestion_dag.py
    │   │   ├── model_training_dag.py
    │   │   └── llm_inference_dag.py
    │   ├── scripts/          # Reusable scripts for pipeline tasks
    │   │   ├── scraping/
    │   │   ├── preprocessing/
    │   │   ├── training/     # XGBoost/BERT training scripts
    │   │   └── llm_utils/    # LLM interaction helpers
    │   ├── tests/            # Tests for MLOps scripts/pipelines
    │   │   ├── unit/
    │   │   └── integration/
    │   ├── containers/       # Dockerfiles for custom Airflow tasks (if any)
    │   └── config/           # Pipeline configurations, prompts
    ├── infrastructure/       # Terraform IaC
    │   ├── environments/
    │   │   ├── staging/
    │   │   └── production/
    │   ├── modules/          # Reusable Terraform modules
    ├── data/                 # Managed by DVC (contains .dvc files)
    │   ├── raw/              # Scraped data
    │   └── processed/        # Cleaned data for training/inference
    ├── notebooks/            # Jupyter notebooks for EDA, experimentation
    ├── .github/workflows/    # GitHub Actions CI/CD workflows
    │   ├── ci.yml
    │   ├── cd_staging.yml
    │   └── cd_production.yml
    ├── requirements.txt      # Python dependencies for backend/mlops
    ├── dvc.yaml              # DVC pipeline definition (optional for data stages)
    └── README.md
    ```

---
