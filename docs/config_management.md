# Config Management
##
### Section 3.3: Configuration and Secrets Management Strategy (Securing Recipes & Special Ingredients)**
*   **3.3.1 Why Robust Config & Secrets Management is Crucial in MLOps**
    *   Security (protecting API keys, database credentials).
    *   Reproducibility (tracking exact configurations used for runs).
    *   Environment Management (different settings for Dev, Staging, Prod).
    *   Collaboration (sharing non-sensitive configs safely).
*   **3.3.2 Types of Configurations in an ML Project**
    *   *Data Sources:* Paths to S3 buckets, database connection strings (excluding credentials).
    *   *Feature Engineering Parameters:* Binning strategies, embedding dimensions, list of features to use.
    *   *Model Training Hyperparameters:* Learning rate, batch size, number of epochs, model architecture details.
    *   *Pipeline Parameters:* Instance types for jobs, resource allocations, trigger schedules.
    *   *Infrastructure Settings:* VPC IDs, subnet IDs, security group IDs (managed by IaC but might be referenced).
    *   *API Endpoints:* URLs for external services (e.g., LLM provider).
    *   *Secrets:* Database passwords, API keys (LLM, Cloud provider services), private certificates.
*   **3.3.3 Common Approaches to Configuration Management**
    *   **Configuration Files (e.g., YAML, JSON, TOML, INI):**
        *   *Pros:* Human-readable, easy to edit, commonly supported by libraries, good for version control (Git).
        *   *Cons:* Can become unwieldy for complex projects, managing environment-specific overrides needs a strategy.
        *   *Strategy:* Use base config files and environment-specific override files (e.g., `config_base.yaml`, `config_staging.yaml`, `config_prod.yaml`). Load base then merge environment-specific.
    *   **Environment Variables:**
        *   *Pros:* Standard way to pass configs in containerized environments (Docker, Kubernetes) and CI/CD systems. Easy to set dynamically.
        *   *Cons:* Not ideal for complex/nested structures. Managing many variables can be cumbersome. Less auditable directly within the application codebase if not explicitly loaded from a file.
    *   **Dedicated Config Management Tools (e.g., HashiCorp Consul, AWS AppConfig):**
        *   *Pros:* Centralized management, dynamic updates without redeployment, versioning, access control.
        *   *Cons:* Adds another tool to the stack, can be overkill for simpler projects.
*   **3.3.4 Best Practices for Managing Secrets**
    *   **NEVER commit secrets directly to Git.**
    *   **Use `.env` files for LOCAL development ONLY, and ensure `.env` is in `.gitignore`.**
    *   **Secrets Management Services (The Secure Ingredient Lockbox):**
        *   *Cloud-Native:* AWS Secrets Manager, Google Secret Manager, Azure Key Vault.
        *   *Third-Party:* HashiCorp Vault.
        *   *How they work:* Store secrets encrypted. Applications/Pipelines fetch secrets at runtime using IAM roles/service accounts with appropriate permissions.
    *   **Injecting Secrets into Pipelines/Applications:**
        *   CI/CD systems (e.g., GitHub Actions Secrets) can securely inject secrets as environment variables into build/deployment steps.
        *   Orchestrators (e.g., Airflow Connections, Kubernetes Secrets) can manage secrets for pipeline tasks.
        *   Applications (e.g., FastAPI service) fetch from secrets manager at startup or per request (with caching).
*   **3.3.5 Configuration and Secrets Strategy for "Trending Now"**
    *   **Non-Sensitive Configurations:**
        *   Use YAML files stored in the `mlops/config/` directory.
        *   Example: `config_base.yaml` for common settings.
        *   `config_dev.yaml`, `config_staging.yaml`, `config_prod.yaml` for environment-specific overrides (e.g., S3 bucket names, Airflow connection IDs, LLM model choice).
        *   These will be version-controlled with Git.
        *   Pipelines and applications will load the appropriate config based on an environment variable (e.g., `APP_ENV=staging`).
    *   **Secrets Management:**
        *   *Local Development (Dev):* Use a `.env` file (added to `.gitignore`) to store API keys (LLM provider, AWS keys for local DVC/S3 interaction if needed). The application/scripts will load from this `.env` file if `APP_ENV=dev`.
        *   *Staging & Production:*
            *   LLM API Key: Store in **AWS Secrets Manager**.
            *   (If needed) Database credentials for Airflow metadata DB (if self-hosted on EC2): Store in **AWS Secrets Manager**.
            *   AWS Service credentials (for S3, App Runner, etc.): Handled via **IAM Roles** attached to the EC2 instances (for Airflow workers/scheduler) or App Runner service. This is the preferred method for AWS service-to-service communication.
            *   GitHub Actions Secrets: Used to store AWS credentials needed for Terraform to deploy infrastructure and for Airflow/App Runner to pull from ECR if using private images.
    *   **Loading Configs in the Application/Pipelines:**
        *   Python scripts (in Airflow tasks, FastAPI) will use a helper function to:
            1.  Load `config_base.yaml`.
            2.  Identify current environment (from `APP_ENV` environment variable).
            3.  Load and merge the corresponding `config_<env>.yaml`.
            4.  If `APP_ENV=dev`, load secrets from `.env`.
            5.  For other environments, fetch necessary secrets from AWS Secrets Manager using `boto3` and the IAM role associated with the execution context.

---
