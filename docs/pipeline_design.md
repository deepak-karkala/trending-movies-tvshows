# Pipeline Design

### Section 3.3: Pipeline Design for "Trending Now" (The Main Production Lines)

We'll outline the three core automated pipelines: Data Ingestion, Model Training (for the educational XGBoost/BERT model), and the LLM-based Inference pipeline.

*   **3.3.1 High-Level Definition of Core Pipelines**

    **Core Pipelines Overview**
    <img src="../../_static/mlops/problem_framing/pipelines.svg"/>

*   **3.3.2 Inputs, Outputs, Key Steps, and Triggers for Each Pipeline**

    *   **Pipeline 1: Data Ingestion Pipeline**
        *   *Trigger:* Daily/Weekly schedule (via Airflow).
        *   *Inputs:* List of websites/APIs to scrape.
        *   *Key Steps:*
            1.  Fetch new movie/TV show listings (metadata, plot).
            2.  Fetch user reviews for these listings.
            3.  Basic cleaning (HTML removal, standardization).
            4.  Store raw and cleaned data in S3 (Parquet format).
            5.  Version data with DVC.
            6.  Update a simple data catalog/manifest.
        *   *Outputs:* Versioned, cleaned movie/show data and reviews in S3.
    *   **Pipeline 2: Model Training Pipeline (XGBoost/BERT - Educational)**
        *   *Trigger:* Manual (initially), can be scheduled or triggered by new data availability post-ingestion (via Airflow).
        *   *Inputs:* Path to versioned, cleaned data (from DVC/S3), training configuration (hyperparameters).
        *   *Key Steps:*
            1.  Load data.
            2.  Feature Engineering (TF-IDF for XGBoost, BERT tokenizer/embeddings for BERT).
            3.  Train model (XGBoost or fine-tune BERT).
            4.  Evaluate model on a holdout set (offline metrics like Macro F1, Precision/Recall per genre).
            5.  If validation passes, version and register the model artifact in W&B.
        *   *Outputs:* Trained model artifact, evaluation metrics, training logs (all versioned and tracked in W&B).
    *   **Pipeline 3: Inference & Content Enrichment Pipeline (LLM)**
        *   *Trigger:* Triggered after successful Data Ingestion Pipeline run for new content, or can be scheduled.
        *   *Inputs:* Path to new, cleaned movie/show data (plots, reviews) from S3/DVC. LLM API keys/configs.
        *   *Key Steps (can be parallelized or sequential):*
            1.  For each new item, call LLM API to generate genre(s) from plot/reviews.
            2.  Call LLM API to summarize aggregated reviews.
            3.  Call LLM API to generate a vibe score (1-10) from reviews/plot.
            4.  Call LLM API to generate descriptive vibe tags from reviews/plot.
            5.  Parse and validate LLM outputs.
            6.  Store these LLM-generated structured data fields (e.g., in a Parquet file in S3 or a simple database accessible by the FastAPI backend).
        *   *Outputs:* Enriched movie/show data with LLM-generated genres, summaries, scores, and tags.

*   **3.3.3 Discussion of Necessary Scripts (Conceptual Level)**
    *   Scraping scripts (Python with BeautifulSoup/Requests/Scrapy).
    *   Data cleaning and transformation scripts (Python, Pandas).
    *   Feature engineering scripts (Python, Pandas, Scikit-learn, Transformers).
    *   Model training scripts (Python with Scikit-learn/XGBoost, PyTorch/Transformers).
    *   LLM interaction scripts (Python with OpenAI client library).
    *   Pipeline definition files (Python for Airflow DAGs).
    *   Terraform configuration files for infrastructure.

---
