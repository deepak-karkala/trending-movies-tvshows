# CI/CD Strategy and Branching Model

### Section 3.5: CI/CD Strategy and Branching Model (The Kitchen's Workflow and Approval Process)

We'll use GitHub Flow as our branching strategy and GitHub Actions for CI/CD.

*   **3.5.1 Chosen Branching Strategy: GitHub Flow**
    *   `main` branch: Always reflects production-ready code.
    *   `feature/*`: Developers create feature branches from `main`.
    *   Pull Requests (PRs): Used to review and merge feature branches into `main`.
*   **3.5.2 Outline of CI Pipeline Steps (Triggered on PR to `main` or push to feature branches)**
    *   Checkout code.
    *   Setup environment (Python, dependencies).
    *   **Static Testing:**
        *   Linters (e.g., `flake8`, `black`).
        *   Static type checking (e.g., `mypy`).
        *   IaC Linters (e.g., `tflint` for Terraform).
        *   Security scans (e.g., `bandit`, Checkov for IaC).
    *   **Unit Tests:**
        *   For backend API logic.
        *   For data processing scripts.
        *   For individual ML pipeline components (if applicable).
    *   (Optional) Build Docker images for services/pipeline steps.
    *   Report status to PR.
*   **3.5.3 Outline of CD Pipeline Steps**
    *   **Trigger for Staging:** Merge to `main` branch.
        *   Build and push production-ready Docker images (FastAPI service, Airflow task containers if custom).
        *   Deploy infrastructure changes via Terraform (`terraform apply`) to Staging environment.
        *   Deploy application/pipeline updates (e.g., new Airflow DAG version, update App Runner service).
        *   Run Integration Tests against Staging (API tests, pipeline end-to-end runs on sample data).
        *   Run Performance/Load Tests (Locust) against Staging API.
        *   Require Manual Approval for Production.
    *   **Trigger for Production:** Manual approval after Staging validation (or tag/release on `main`).
        *   Deploy *same artifacts* (Docker images, Terraform configs) from Staging to Production environment.
        *   Perform smoke tests.
        *   Implement progressive rollout if applicable (e.g., App Runner's traffic splitting).
        *   Monitor closely.

---
