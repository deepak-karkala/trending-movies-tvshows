# Environment Strategy
##
### Section 3.4: Environment Strategy (Dev, Staging, Prod) (Organizing Our Kitchen Stations)

We adopt a standard three-environment strategy to ensure stability and quality.

*   **3.4.1 Purpose and Configuration Goals for Each Environment**
    *   **Development (Dev):**
        *   *Purpose:* For developers to write and test code locally/in personal cloud workspaces. Focus on iteration speed and individual productivity.
        *   *Configuration:* Local machines (with Docker for consistency) or cloud-based IDEs (GitHub Codespaces, AWS Cloud9, SageMaker Studio). Access to *sampled, anonymized, or synthetic data*. Minimal resources. Uses `feature` branches.
    *   **Staging (Pre-Production):**
        *   *Purpose:* To test code changes in an environment that *mirrors production* before deploying to live users. Focus on integration, end-to-end testing, and performance validation.
        *   *Configuration:* Dedicated AWS account. Infrastructure managed by Terraform, identical or scaled-down version of Prod. Deploys from `main` branch after PR merge. Uses *staging-specific data sources* (e.g., a separate S3 bucket with a larger, more realistic dataset than dev, but not live prod data). Runs full integration tests, load tests.
    *   **Production (Prod):**
        *   *Purpose:* To serve live user traffic. Focus on stability, reliability, performance, and security.
        *   *Configuration:* Dedicated AWS account. Infrastructure managed by Terraform. Deploys from `main` branch after successful Staging validation and manual approval. Uses *live production data sources*. Comprehensive monitoring and alerting.

*   **3.4.2 Data Access Strategy and Permissions Across Environments**
    *   **Dev:** Read-only access to specific, small, and potentially anonymized/synthetic datasets (e.g., sample of S3 data). No access to production databases or sensitive user data.
    *   **Staging:** Read-only access to dedicated staging data sources that mimic production data structure and volume but are not live production data. This might be a regularly refreshed, sanitized snapshot of production data or a large, curated test dataset.
    *   **Prod:**
        *   *Data Ingestion Pipeline:* Read access to raw data sources (scraping targets, APIs). Write access to its S3 processed data bucket.
        *   *Training Pipeline:* Read access to processed data in S3 (Prod). Write access to Model Registry (W&B) and artifact stores.
        *   *Inference Pipeline (LLM path):* Read access to processed data in S3 (Prod). Write access to the enriched data store for the FastAPI backend.
        *   *FastAPI Backend:* Read access to its enriched data store. No direct write access to core data pipelines, only to its own logs.
    *   *IAM Roles:* Define specific IAM roles for each pipeline/service within each environment to enforce least privilege.

---
