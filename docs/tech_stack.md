# Tech Stack

### Section 3.2: Finalizing the Tech Stack (Choosing Our Kitchen Appliances)

Based on our project requirements and the MLOps capabilities discussed in Chapter 2, we now finalize the specific tools and technologies for "Trending Now".

*   **3.2.1 Presenting the Chosen Tech Stack Document**

    **Tech Stack: "Trending Now" Application**

    *   **Backend API:**
        *   *Framework:* FastAPI (Python)
        *   *Deployment Platform:* AWS App Runner (Serverless Containers)
    *   **Frontend:**
        *   *Languages/Structure:* HTML, CSS, JavaScript (Vanilla JS)
        *   *Visualization Library:* D3.js
    *   **Data Ingestion & Storage:**
        *   *Scraping:* Python with BeautifulSoup/Scrapy (conceptual).
        *   *External APIs:* TMDb API (or similar) for movie/show metadata.
        *   *Raw/Processed Data Storage:* AWS S3 (using Parquet for structured data).
        *   *Data Versioning:* DVC.
    *   **ML Model Development (Educational Path):**
        *   *Frameworks:* Scikit-learn (XGBoost wrapper), PyTorch (for BERT).
        *   *Experiment Tracking & Model Registry:* Weights & Biases (W&B).
    *   **LLM Integration (Production Inference Path):**
        *   *Provider:* OpenAI API (or chosen alternative like Anthropic, Cohere).
        *   *Interaction:* Python client library within FastAPI.
    *   **MLOps - Pipelines & Orchestration:**
        *   *Workflow Orchestration:* Apache Airflow (deployed via Docker on EC2, or managed service if preferred later).
        *   *CI/CD Tool:* GitHub Actions.
    *   **MLOps - Monitoring:**
        *   *Infrastructure Monitoring:* AWS CloudWatch (for App Runner, S3).
        *   *Application/ML Monitoring:* Prometheus (for FastAPI metrics) + Grafana (visualization). OSS Drift Detection libs like EvidentlyAI/WhyLogs for generating reports, CloudWatch Alarms for alerts.
    *   **MLOps - Infrastructure as Code (IaC):**
        *   *Tool:* Terraform.
    *   **Source Control:**
        *   *Tool:* Git / GitHub.
    *   **Data Governance (Initial):**
        *   *Tool:* AWS IAM for resource permissions.

*   **3.2.2 Justification for Key Choices**
    *   **FastAPI:** Modern, high-performance Python web framework, good for building APIs quickly.
    *   **AWS App Runner:** Simplifies deployment and scaling of containerized web applications (like our FastAPI service) without needing to manage underlying servers or Kubernetes.
    *   **D3.js:** Chosen for its power and flexibility to create the desired unique bubble chart visualization, with the developer's confidence in implementation.
    *   **Vanilla JS/HTML/CSS:** Keeps frontend complexity low to maintain focus on MLOps in the guide.
    *   **AWS S3/Parquet/DVC:** Standard, robust, and cost-effective for data storage and versioning.
    *   **W&B:** Excellent for experiment tracking and has model registry capabilities suitable for the educational model.
    *   **OpenAI API (or similar):** Provides state-of-the-art LLM capabilities for summarization, scoring, tagging, and genre classification, demonstrating modern AI integration.
    *   **Airflow:** Mature and powerful orchestrator, widely used in production, good for demonstrating complex pipeline dependencies.
    *   **GitHub Actions:** Seamless integration with GitHub for CI/CD.
    *   **Terraform:** Industry standard for IaC, cloud-agnostic principles.
    *   **Prometheus/Grafana/CloudWatch:** Standard stack for comprehensive monitoring.

---




**Appendix: Tech Stack Selection: Thought Process**

1.  **Data sources:** Web scraping (BeautifulSoup/Scrapy) & APIs (like TMDb) - *Appropriate.*
2.  **Storage:** AWS S3 (Object Storage), Parquet (File Format) - *Excellent standard choice for raw and processed data.*
3.  **Data Versioning:** DVC - *Solid, widely-used open-source choice, integrates well.*
4.  **Data Governance (Initial):** AWS IAM - *Fundamental for AWS permissions.*
5.  **Data Analysis Language:** Python, Pandas - *Standard.*
6.  **Experimentation Environments:** IDE (local or cloud-based like VS Code with remote SSH/Codespaces) - *Flexible and practical.*
7.  **Experiment Tracking tools:** Weights & Biases (W&B) - *Excellent, feature-rich choice.*
8.  **ML Frameworks:** Scikit-learn (for XGBoost wrapper), PyTorch (for BERT) - *Standard and powerful.*
9.  **Feature Store:** Feast - *Good open-source option to demonstrate concepts. Acknowledge that for this specific project, it might be simpler initially to pass features directly, but including Feast is valuable educationally.*
10. **Data Processing Capabilities:** Batch - *Appropriate for the daily/weekly ingestion pipeline.*
11. **Workflow/ML Pipeline Orchestration:** Airflow - *Mature, powerful, widely used, though complex. Good choice for demonstrating real-world orchestration.*
12. **Source control:** Git (e.g., GitHub) - *Essential.*
13. **CI/CD Tool:** GitHub Actions - *Excellent choice, integrates seamlessly with GitHub.*
14. **IaC:** Terraform - *Excellent, industry-standard choice for managing cloud infrastructure.*
15. **Load Testing:** Locust - *Good Python-native choice for testing the FastAPI service.*
16. **Model Registries:** W&B - *Leverages the chosen experiment tracking tool's capability.*
17. **ML Metadata Management and Artifact Repositories:** W&B - *Leverages the chosen experiment tracking tool's capability.*
18. **Metrics (ML):** F1 score, Recall, Precision (specify Macro/Micro/Weighted based on class imbalance later) - *Standard and appropriate.*

**Addressing Uncertainties & Providing Recommendations:**

13. **CI/CD Strategy and Branching Model:**
    *   **Options:**
        *   **Gitflow:** More complex (main, develop, feature, release, hotfix branches). Good for versioned releases, perhaps overkill for rapid iteration.
        *   **GitHub Flow:** Simpler (main branch is always deployable, use feature branches + PRs). Encourages frequent integration and deployment.
        *   **Trunk-Based Development:** All developers work on `main` (trunk), using short-lived feature branches or direct commits (with heavy reliance on feature flags and robust testing). Fastest integration, requires mature testing culture.
    *   **Pros/Cons:** Gitflow offers strict control but can slow down development. GitHub Flow is a good balance for teams practicing CD. Trunk-based is fastest but riskiest without strong safeguards.
    *   **Recommendation:** **GitHub Flow**. It aligns well with the goal of demonstrating CI/CD best practices using GitHub Actions, is simpler to manage than Gitflow, and encourages frequent integration, which is good for MLOps iteration.
        *   *Workflow:* Create `feature` branches off `main`. Push changes, open Pull Request (PR). Automated tests (CI) run on PR. Code review/approval. Merge PR into `main`. Deploy `main` to Staging (CD). Manual approval. Deploy `main` to Production (CD).

16. **Monitoring Tools for Infrastructure:**
    *   **Options:**
        *   **Cloud-Native:** AWS CloudWatch (Metrics, Logs, Alarms). Tightly integrated with AWS services (S3, EC2, App Runner, etc.). Easy to start with.
        *   **Open-Source Stack:** Prometheus (metrics collection) + Grafana (visualization). Powerful, standard, customizable, but requires setup and maintenance.
        *   **Third-Party SaaS:** Datadog, New Relic, Dynatrace. Feature-rich, often easier UI, but can be expensive and adds another vendor.
    *   **Pros/Cons:** CloudWatch is convenient for basic AWS resource monitoring. Prometheus/Grafana offers more power and flexibility for custom application metrics (like from FastAPI) but needs hosting/setup. SaaS is easiest but costly.
    *   **Recommendation:** **AWS CloudWatch** for base infrastructure monitoring (CPU, RAM, network of deployment platform like App Runner/EC2, S3 bucket metrics) combined with **Prometheus + Grafana** for application-level metrics (FastAPI request rates/latency, potentially custom metrics from pipelines). CloudWatch provides the easy AWS integration, while P+G demonstrates a standard stack often used for deeper application observability. *Note: For simplicity in the guide's project, you might initially focus just on CloudWatch and add P+G conceptually or as an advanced step.*

17. **Continuous Training Cloud/Local:**
    *   **Your Proposal:** Short local runs (e.g., on feature branch push via CI) for sanity checks, then full cloud runs (e.g., on push/merge to dev/main branch via CI/CD).
    *   **Review:** This is a **perfectly sensible and practical approach**. It balances quick feedback during development with cost-effective, scalable training for deployment candidates. The triggers linked to Git events integrate well with CI/CD.
    *   **Recommendation:** **Adopt this strategy.** Clearly define what "local" means (e.g., runs within a GitHub Action runner using a small data subset/few epochs) versus "cloud" (e.g., triggers an AWS Batch job, SageMaker Training Job, or runs on a dedicated EC2 instance).

18. **Infrastructure Testing:**
    *   **Options:**
        *   **Linters/Static Analysis:** `tflint`, `checkov` - Check Terraform code for errors, security issues, best practices before deployment. *Essential first step.*
        *   **Unit/Integration Testing Frameworks:**
            *   `Terratest` (Go): Tests actual deployed resources. Powerful end-to-end testing. Requires Go knowledge.
            *   `Kitchen-Terraform` (Ruby): Similar goals to Terratest, uses Chef InSpec for verification. Requires Ruby knowledge.
            *   `Pytest` + Cloud SDKs (`boto3` for AWS) / Mocking (`moto`): Write Python tests to check Terraform module outputs or interact with deployed (or mocked) resources. Keeps testing in Python.
        *   **Manual Validation:** Checking resources in the console. Error-prone.
    *   **Pros/Cons:** Linters are fast and catch easy errors. Terratest/Kitchen-TF offer robust end-to-end validation but require learning other languages. Pytest keeps everything in Python but might require more effort to write comprehensive end-to-end tests compared to specialized tools.
    *   **Recommendation:** **Start with Linters (`tflint`, `checkov`) integrated into CI.** For functional testing, use **Pytest + `boto3` (or equivalent SDK for other clouds)**. Begin by writing tests for Terraform *modules* to verify their outputs/behavior. Mocking with `moto` can be useful for unit tests. Add more complex tests that spin up/tear down *real* (but temporary) resources for critical integration points as needed, understanding these will be slower and costlier.

21. **Model Serving Frameworks (within FastAPI):**
    *   **Clarification:** FastAPI is the web framework. The question is how the trained model (XGBoost/BERT) or LLM logic is *executed* within the FastAPI request handler.
    *   **Options (for XGBoost/BERT):**
        *   Load model artifact directly into the FastAPI process memory using standard libraries (`xgboost.Booster()`, `transformers.pipeline()` or `torch.load()`).
        *   Use an optimized inference server *library* within the same container (e.g., ONNX Runtime if models are converted).
    *   **Options (for LLM):**
        *   Direct API calls to the provider (OpenAI, Anthropic, etc.) using their Python client libraries.
    *   **Recommendation:** For simplicity and directness in the guide:
        *   **XGBoost/BERT:** **Load model directly in FastAPI process.** This is standard practice for models of this size when wrapped in a simple API.
        *   **LLM:** **Direct API calls to the provider.**
        This avoids adding extra layers like an internal ONNX server just for the educational model.

22. **Deployment Platforms (for FastAPI Service):**
    *   **Options (Recap):** Serverless Containers (App Runner, Cloud Run), PaaS (Heroku, Render), Managed Kubernetes (EKS, GKE), IaaS (EC2/VM), ML Platforms (SageMaker/Vertex Endpoints).
    *   **Refined Recommendation:** Given the stack (FastAPI, Docker container), **Serverless Containers (AWS App Runner / Google Cloud Run)** remain the best recommendation. They handle scaling, are cost-effective (pay-for-use), deploy directly from a container image, and are manageable via Terraform. They provide a good balance of managed service convenience without the full complexity of Kubernetes or the potential lock-in/cost of dedicated ML platform endpoints for this specific use case.

23. **Monitoring Platforms (for ML Aspects):**
    *   **Options (Recap):** OSS (EvidentlyAI, WhyLogs + P&G), SaaS (Arize, Fiddler, etc.), Cloud-Native (SageMaker/Vertex Model Monitor).
    *   **Refined Recommendation:** **Use an OSS Library (EvidentlyAI or WhyLogs)** to generate monitoring *reports* (HTML/JSON) on data/prediction drift and model quality (if labels become available). Schedule this analysis to run periodically (e.g., daily via a simple job triggered by Airflow or even a GitHub Action schedule). Store the reports in S3. Visualize key drift metrics using **Grafana** (reading from metrics exported by the analysis job, possibly stored simply in S3/Prometheus). Use **AWS CloudWatch Alarms** triggered based on the analysis outputs (e.g., a file landing in S3 indicating significant drift triggers an alarm). This demonstrates the *concepts* using accessible tools while integrating with standard alerting.

26. **Decay/Drift Detection:**
    *   **Options (Recap):** Statistical Tests (KS, Chi-Squared, PSI), Distance Metrics, Model-Based, Summary Stats.
    *   **Refined Recommendation:** Implement the following within your monitoring analysis script (using libraries like EvidentlyAI, WhyLogs, or `scipy.stats`/`pandas`):
        *   **Summary Statistics Comparison:** Track min, max, mean, median, missing % for key numerical features and compare against training set baseline.
        *   **Population Stability Index (PSI):** For important numerical features (like LLM-generated scores) and potentially model prediction probabilities. Requires binning.
        *   **Chi-Squared Test:** For key categorical features (like dominant genre predicted, key vibe tags).
        *   **Monitor Model Output Distribution:** Track the distribution of predicted genres over time. A sudden shift (e.g., everything becomes "Action") indicates a problem. Use KS-test *only* if comparing a single output probability distribution (e.g., confidence score).
    *   *Focus:* Prioritize monitoring the *LLM score distribution*, *predicted genre distribution*, and potentially *input text length/statistics* as initial drift indicators.

27. **Environment Strategy (Dev, Staging, Prod):**
    *   **Recommendation:** **Stick to the standard Dev -> Staging -> Prod approach.**
        *   **Dev:** Local machines or Cloud IDEs (Codespaces/SageMaker Studio/EC2) for development. Unit tests run locally/on commit. Access to sampled/mocked data.
        *   **Staging:** Dedicated AWS account mirroring Production infrastructure (App Runner/Cloud Run, S3, IAM roles defined by Terraform). Deployed automatically via CD from `main` branch after PR approval/CI checks. Runs integration tests, potentially load tests. Uses staging data sources (e.g., separate S3 bucket populated by staging data pipeline). Requires manual approval gate for promotion to Prod.
        *   **Prod:** Dedicated AWS account. Receives deployments promoted from Staging. Runs on live user traffic/data sources. Heavily monitored.

**Summary Table of Key Choices:**

| Component                             | Chosen Tool/Strategy                                                                                                | Notes                                                              |
| :------------------------------------ | :------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------- |
| **Data Sources**                      | Web Scraping / APIs (TMDb etc.)                                                                                     | Standard                                                           |
| **Storage**                           | AWS S3 / Parquet                                                                                                    | Standard                                                           |
| **Data Versioning**                   | DVC                                                                                                                 | Open-source standard                                               |
| **Data Governance (Base)**            | AWS IAM                                                                                                             | Essential for AWS                                                  |
| **Data Analysis**                     | Python / Pandas                                                                                                     | Standard                                                           |
| **Experimentation Env**               | IDE (VS Code Remote/Codespaces)                                                                                     | Flexible                                                           |
| **Experiment Tracking**               | W&B                                                                                                                 | Powerful, visual                                                   |
| **ML Frameworks**                     | Scikit-learn (XGBoost), PyTorch (BERT)                                                                              | Standard                                                           |
| **Feature Store**                     | Feast                                                                                                               | Included for educational value                                     |
| **Data Processing**                   | Batch                                                                                                               | Sufficient for core pipeline                                       |
| **Workflow Orchestration**            | Airflow                                                                                                             | Powerful, industry standard                                        |
| **Source Control**                    | Git / GitHub                                                                                                        | Essential                                                          |
| **Branching Strategy**                | **GitHub Flow**                                                                                                     | Recommended: Balances speed and structure                        |
| **CI/CD Tool**                        | GitHub Actions                                                                                                      | Integrates with GitHub                                             |
| **IaC (Infrastructure as Code)**      | Terraform                                                                                                           | Standard, cloud-agnostic                                           |
| **Infra Monitoring**                  | **AWS CloudWatch + Prometheus/Grafana**                                                                             | Recommended: Combines cloud-native ease with OSS power           |
| **Continuous Training**               | **Local (CI check) + Cloud (CD stage)**                                                                             | Recommended: Practical staged approach                             |
| **Infra Testing**                     | **Linters (Checkov/tflint) + Pytest + AWS SDK/moto**                                                                | Recommended: Python-centric, start with module/mock tests        |
| **Load Testing**                      | Locust                                                                                                              | Standard Python tool                                               |
| **Model Serving (Internal)**          | **Direct Load (XGB/BERT) / API Call (LLM)**                                                                         | Recommended: Simple integration with FastAPI                     |
| **Deployment Platform (FastAPI)**     | **Serverless Containers (AWS App Runner / Google Cloud Run)**                                                       | Recommended: Scalable, manageable, good balance                  |
| **ML Monitoring Platform**            | **OSS (EvidentlyAI/WhyLogs) + Grafana + CloudWatch Alarms**                                                         | Recommended: Demonstrates concepts, integrates with alerting     |
| **Model Registry**                    | W&B                                                                                                                 | Leverages chosen tracking tool                                     |
| **Metadata/Artifact Store**           | W&B                                                                                                                 | Leverages chosen tracking tool                                     |
| **Drift Detection**                   | **Summary Stats + PSI + Chi-Squared + Output Dist Monitoring**                                                      | Recommended: Combination of practical techniques                 |
| **Metrics (ML)**                      | F1, Recall, Precision (Macro F1 primary)                                                                            | Standard                                                           |
| **Environment Strategy**              | **Dev -> Staging -> Prod**                                                                                          | Recommended: Standard practice with clear promotion gates        |
