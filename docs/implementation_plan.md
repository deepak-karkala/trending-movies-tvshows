# Implementation Plan

##
### Section 3.7: Detailed Implementation Plan (The Master Prep List)

This section presents a high-level mapping of how the "Trending Now" project development will unfold alongside the study guide chapters.

*   **Chapter 4 (The Market Run – Data Sourcing, Discovery & Understanding):**
    *   *Project:*
        *   Finalize and document data sources (APIs, scraping targets for movies/shows and reviews).
        *   Implement initial scraping scripts (e.g., using Python with BeautifulSoup/Requests) for a sample set of data.
        *   Perform Exploratory Data Analysis (EDA) on the scraped samples using Pandas and visualization libraries in a notebook.
        *   Assess initial data quality, identify common issues (missing fields, inconsistent formats).
        *   Create initial Data Cards or documentation for the chosen data sources.
        *   Set up basic S3 buckets for raw data storage.
*   **Chapter 5 (Mise en Place – Data Engineering for Reliable ML Pipelines):**
    *   *Project:*
        *   Develop Python scripts for cleaning and preprocessing the scraped movie/review data (handle missing values, standardize text).
        *   Store processed data in Parquet format in S3.
        *   Initialize DVC for versioning the processed datasets.
        *   Design the schema for the processed data.
        *   Implement initial data validation checks (e.g., for expected fields, data types) as Python functions.
        *   Conceptualize the Airflow DAG for the Data Ingestion Pipeline (Steps: Scrape -> Clean -> Store -> Version).
*   **Chapter 6 (Perfecting Flavor Profiles – Feature Engineering and Feature Stores):**
    *   *Project:*
        *   Develop feature extraction logic for plot summaries and reviews (e.g., TF-IDF using Scikit-learn, placeholder for BERT embeddings).
        *   Create functions for generating these features.
        *   Discuss how these features would be defined and managed in Feast (conceptual design).
        *   Identify potential issues with feature consistency between a batch training path and a future online inference path.
*   **Chapter 7 (The Experimental Kitchen – Model Development & Iteration):**
    *   *Project:*
        *   Set up Weights & Biases for experiment tracking.
        *   Train baseline models (e.g., keyword-based or simple logistic regression on TF-IDF for genre classification).
        *   Develop and train the XGBoost model for genre classification.
        *   Develop scripts to fine-tune a pre-trained BERT model (e.g., from Hugging Face Transformers) for genre classification on a sample of the data.
        *   Track all experiments (parameters, metrics, code versions) in W&B.
        *   Perform hyperparameter tuning for XGBoost and/or BERT.
*   **Chapter 8 (Standardizing the Signature Dish – Building Scalable Training Pipelines):**
    *   *Project:*
        *   Refactor the XGBoost/BERT training scripts into modular, production-ready Python code.
        *   Design and implement the Airflow DAG for the Model Training Pipeline (Data Loading -> Feature Engineering -> Training -> Evaluation -> Registration).
        *   Integrate W&B for tracking automated training runs.
        *   Set up a CI (GitHub Actions) workflow for testing the training pipeline code.
*   **Chapter 9 (The Head Chef's Approval – Rigorous Offline Model Evaluation & Validation):**
    *   *Project:*
        *   Implement comprehensive model evaluation steps within the training pipeline DAG (calculating Macro F1, Precision/Recall per genre).
        *   Perform slice-based evaluation on important data segments (e.g., movies vs. TV shows).
        *   Register the validated XGBoost/BERT model versions and their metrics in W&B Model Registry.
        *   Create a Model Card for the best performing educational model.
*   **Chapter 10 (Grand Opening – Model Deployment Strategies & Serving Infrastructure):**
    *   *Project:*
        *   Develop the FastAPI backend service with endpoints for:
            *   Serving genres from the trained XGBoost/BERT model (educational path).
            *   Integrating with the chosen LLM API to get genre, summary, score, and tags.
        *   Package the FastAPI application with Docker.
        *   Write Terraform scripts to define and deploy the FastAPI service to AWS App Runner (for both Staging and Prod environments).
        *   Set up CI/CD using GitHub Actions to build and deploy the FastAPI service.
*   **Chapter 11 (Listening to the Diners – Production Monitoring & Observability for ML Systems):**
    *   *Project:*
        *   Set up AWS CloudWatch for monitoring the App Runner service (FastAPI).
        *   Implement structured logging within the FastAPI application.
        *   Design a conceptual process for using EvidentlyAI/WhyLogs to generate drift reports on LLM input/output and store them in S3.
        *   Set up basic Grafana dashboards (conceptual) to visualize key operational and LLM output metrics.
        *   Configure CloudWatch Alarms based on critical FastAPI metrics or the presence of drift reports.
*   **Chapter 12 (Refining the Menu – Continual Learning & Production Testing for Model Evolution):**
    *   *Project:*
        *   Define triggers for retraining the educational XGBoost/BERT model (e.g., based on new data from the Data Ingestion Pipeline).
        *   Update the Airflow Training Pipeline DAG to handle retraining logic.
        *   Design conceptual A/B testing (e.g., using App Runner's traffic splitting) to compare a new version of the XGBoost/BERT model or a new LLM prompt.
*   **Chapter 13 (Running a World-Class Establishment – Governance, Ethics & The Human Element in MLOps):**
    *   *Project:*
        *   Review the "Trending Now" project's MLOps setup for governance (auditability of pipeline runs via Airflow & W&B, data lineage via DVC).
        *   Discuss ethical considerations for the "Trending Now" app: potential biases in scraped genre data, fairness in how "vibes" or scores are generated by the LLM, and user data privacy related to review content.
        *   Reflect on the team collaboration aspects if this were a multi-person project.
        *   Consider potential UX improvements for presenting LLM-generated insights responsibly.

---
