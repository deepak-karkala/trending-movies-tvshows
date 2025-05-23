**Detailed Step-by-Step Implementation Plan for Data Ingestion Pipeline (for CursorAI)**

**Objective:** Create a daily automated Airflow pipeline that scrapes new movie/TV show data and reviews, enriches it using Google Gemini LLM, validates it, versions it with DVC, and loads it into an AWS Redshift data warehouse.

**Phase 1: Setup & Configuration**

1.  **Project Structure:**
    *   `trending-movies-tvshows/`
        *   `mlops/`
            *   `pipelines/` (for Airflow DAGs)
            *   `scripts/`
                *   `scraping/`
                *   `preprocessing/`
                *   `llm_utils/`
                *   `validation/`
            *   `config/`
        *   `infrastructure/` (for Terraform)
        *   `data/` (for DVC tracking - `.dvc` files will go here)
        *   `.github/workflows/`
2.  **Configuration Files (`mlops/config/`):**
    *   Create `config_base.yaml`:
        *   `s3_raw_bucket: "trending-now-raw-data-YOUR_SUFFIX"`
        *   `s3_processed_bucket: "trending-now-processed-data-YOUR_SUFFIX"`
        *   `dvc_remote_name: "s3remote"`
        *   `redshift_schema_name: "public"`
        *   `redshift_table_name: "movies_tv_shows_enriched"`
        *   `llm_provider_config: { "model_name": "gemini-pro" } # Or your specific model`
    *   Create `config_dev.yaml`, `config_staging.yaml`, `config_prod.yaml` (initially can be empty or inherit all from base, will be populated by Terraform outputs for secrets/endpoints).
    *   Create `.env.template` (for local dev secrets, to be copied to `.env` and added to `.gitignore`):
        *   `GEMINI_API_KEY="YOUR_GEMINI_API_KEY"`
        *   `AWS_ACCESS_KEY_ID="YOUR_AWS_KEY_FOR_LOCAL_DVC_TESTING"`
        *   `AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_FOR_LOCAL_DVC_TESTING"`
        *   `REDSHIFT_HOST_DEV="localhost_or_dev_endpoint"`
        *   `REDSHIFT_PORT_DEV="5439"`
        *   `REDSHIFT_DB_DEV="dev"`
        *   `REDSHIFT_USER_DEV="your_user"`
        *   `REDSHIFT_PASSWORD_DEV="your_password"`
3.  **Python Helper for Config Loading (`mlops/scripts/utils/config_loader.py`):**
    *   Create a Python function `load_config()` that:
        *   Reads `APP_ENV` environment variable (defaults to `dev`).
        *   Loads `config_base.yaml`.
        *   Loads `config_<APP_ENV>.yaml` and merges it over the base config.
        *   If `APP_ENV == 'dev'`, loads secrets from `.env` file using `python-dotenv`.
        *   For other environments, it should be designed to fetch secrets from AWS Secrets Manager (implement placeholder for now, actual fetching logic later).
        *   Returns the final configuration dictionary.
4.  **Redshift Table Schema: `movies_tv_shows_enriched`**

    *   `id` (VARCHAR, Primary Key) - Unique ID (e.g., derived from `detailUrl` or a combination of title/year if no external stable ID is consistently available from all sources)
    *   `title` (VARCHAR)
    *   `content_type` (VARCHAR) - "Movie" or "TV Show" (from your `contentType`)
    *   `streaming_platforms` (VARCHAR) - Comma-separated string of platforms (e.g., "Amazon Prime Video, Amazon Prime Video with Ads"). *Alternatively, Redshift supports `SUPER` type for JSON arrays, or we could normalize this to a separate table if complex querying on platforms is needed, but CSV string is simpler for this guide.*
    *   `release_year` (INTEGER) - Extracted from `releaseDate` or `yearReleased`
    *   `release_date_text` (VARCHAR) - Original `releaseDate` string for reference
    *   `detail_url` (VARCHAR) - Source URL
    *   `source_genres` (VARCHAR) - Comma-separated string of genres from the source (e.g., TMDb)
    *   `imdb_rating` (FLOAT) - Nullable
    *   `rotten_tomatoes_rating` (VARCHAR) - Store as text to handle "%", nullable
    *   `synopsis` (VARCHAR) - Scraped plot summary
    *   `cast_members` (VARCHAR) - JSON string of the cast array `[{"name": "...", "character": "..."}, ...]`. *Redshift `SUPER` type could also be used.*
    *   `directors` (VARCHAR) - JSON string of the directors array (similar to cast)
    *   `duration_text` (VARCHAR) - e.g., "24min" or "1h 30min"
    *   `maturity_rating` (VARCHAR) - Nullable
    *   `language` (VARCHAR) - Nullable
    *   `country` (VARCHAR) - Nullable
    *   `scraped_reviews` (VARCHAR) - JSON string of an array of review objects: `[{"source_name": "CriticSiteX", "review_text": "...", "original_score": "..."}, {"source_name": "BlogY", "review_text": "..."}]`. *Again, `SUPER` type is an option.*
    *   `llm_review_summary` (VARCHAR) - LLM-generated summary of `scraped_reviews`
    *   `llm_generated_score` (FLOAT) - LLM-generated score (1-10) based on reviews/synopsis
    *   `llm_generated_vibe_tags` (VARCHAR) - Comma-separated string of LLM-generated vibe tags
    *   `llm_generated_primary_genre` (VARCHAR) - Primary genre classified by LLM
    *   `llm_generated_secondary_genres` (VARCHAR) - Other genres by LLM (comma-separated)
    *   `data_ingestion_timestamp` (TIMESTAMP WITH TIME ZONE) - When this record was last updated/created by the pipeline
    *   `source_data_hash` (VARCHAR) - An MD5 or SHA256 hash of key input fields (e.g., title, year, synopsis) to help detect if source data for an existing entry has changed significantly, potentially triggering re-processing by the LLM.



**Phase 2: Script Development (Python scripts in `mlops/scripts/`)**

1.  **Scraping Scripts (`mlops/scripts/scraping/`):**
    *   `justwatch_scraper.py`: (script is already available, make necessary changes as per the plan described)
        *   Function `fetch_new_releases(api_key, days_ago=7)`:
            *   Scrapes JustWatch for movies/shows released in the last `days_ago`.
            *   Parses data into a list of dictionaries matching the raw structure of your sample JSON.
            *   Returns list of movie/show data.
    *   `review_scraper.py`:
        *   Function `fetch_reviews_for_item(item_title, item_detail_url, max_reviews=5)`:
            *   Simulate scraping reviews for a given item from 2-3 predefined (dummy or accessible) review sites/blogs.
            *   Extract review text, source name, and any original score.
            *   Returns a list of review dictionaries: `[{"source_name": "...", "review_text": "...", "original_score": "..."}, ...]`.
2.  **Preprocessing Script (`mlops/scripts/preprocessing/preprocess_data.py`):**
    *   Function `preprocess_raw_data(raw_movies_data, raw_reviews_data_map)`:
        *   Takes list of raw movie/show dicts and a map of `item_id -> list_of_review_dicts`.
        *   Cleans text fields (synopsis, review text): basic HTML removal, normalize whitespace.
        *   Extracts `release_year` from `releaseDate`.
        *   Standardizes `streaming_platforms`, `source_genres` into comma-separated strings.
        *   Converts `cast`, `directors` to JSON strings.
        *   Combines movie/show data with its corresponding list of reviews (also as a JSON string for `scraped_reviews` field).
        *   Creates `id` (e.g., from `detailUrl` or a robust hash).
        *   Calculates `source_data_hash`.
        *   Returns a Pandas DataFrame with columns matching the *non-LLM parts* of the defined Redshift schema.
3.  **LLM Interaction Script (`mlops/scripts/llm_utils/gemini_enricher.py`):**
    *   Function `enrich_with_gemini(data_df, api_key)`:
        *   Takes Pandas DataFrame (output from preprocessing).
        *   For each row:
            *   Construct prompt for review summarization using `scraped_reviews`. Call Gemini API. Add `llm_review_summary`.
            *   Construct prompt for vibe score generation using `synopsis` and `llm_review_summary`. Call Gemini API. Add `llm_generated_score`.
            *   Construct prompt for vibe tag generation. Call Gemini API. Add `llm_generated_vibe_tags`.
            *   Construct prompt for genre classification. Call Gemini API. Add `llm_generated_primary_genre` and `llm_generated_secondary_genres`.
        *   Handle API errors, rate limits gracefully (with retries/backoff).
        *   Log API call costs/tokens if possible.
        *   Returns DataFrame with added LLM columns.
4.  **Data Validation Script (`mlops/scripts/validation/validate_with_ge.py`):**
    *   Function `validate_enriched_data(data_df)`:
        *   Uses Great Expectations (or simple Pandas checks for guide simplicity if GE is too complex for initial setup):
            *   Initialize DataContext, create ExpectationSuite for `movies_tv_shows_enriched`.
            *   Add expectations:
                *   `id`, `title`, `content_type`, `release_year`, `synopsis`, `llm_review_summary`, `llm_generated_primary_genre` to be not null.
                *   `llm_generated_score` to be between 1 and 10.
                *   `streaming_platforms`, `source_genres`, `llm_generated_vibe_tags`, `llm_generated_secondary_genres` to be strings.
                *   `data_ingestion_timestamp` to be a valid timestamp.
            *   Run validation on `data_df`.
            *   If validation fails, raise an exception or return a failure status. Print/log validation results.
            *   Returns boolean success status.

**Phase 3: Airflow DAG (`mlops/pipelines/data_ingestion_dag.py`)**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Import your custom script functions
# from mlops.scripts.scraping.justwatch_scraper import fetch_new_releases
# from mlops.scripts.scraping.review_scraper import fetch_reviews_for_item
# from mlops.scripts.preprocessing.preprocess_data import preprocess_raw_data
# from mlops.scripts.llm_utils.gemini_enricher import enrich_with_gemini
# from mlops.scripts.validation.validate_with_ge import validate_enriched_data
# from mlops.scripts.loading.redshift_loader import load_df_to_redshift
# from mlops.scripts.utils.config_loader import load_config
# from mlops.scripts.utils.s3_utils import save_df_to_s3_parquet, load_df_from_s3_parquet

# Placeholder functions for now (to be implemented in actual scripts)
def fetch_new_releases_callable(**kwargs):
    print("Fetching new releases...")
    # config = load_config()
    # api_key = config['tmdb_api_key'] # Assuming API key in config or fetched from Secrets
    # releases = fetch_new_releases(api_key)
    # For now, return dummy data
    dummy_releases = [{"id": "tmdb123", "title": "Dummy Movie", "contentType": "Movie", "releaseDate": "2025-01-01", "synopsis": "A great movie.", "detailUrl": "http://example.com/movie/123", "genres": ["Action"], "cast": [], "directors": [], "duration": "120min", "maturityRating": "PG-13", "language": "English", "country": "USA", "yearReleased": "2025", "imdbRating": "7.5", "rottenTomatoesRating": "80%"}]
    ti = kwargs['ti']
    ti.xcom_push(key='new_releases', value=dummy_releases)
    # In reality: save_to_s3_raw(releases, config['s3_raw_bucket'], 'new_releases.parquet')

def fetch_reviews_callable(**kwargs):
    print("Fetching reviews...")
    ti = kwargs['ti']
    releases = ti.xcom_pull(task_ids='scrape_new_releases_task', key='new_releases')
    # reviews_map = {}
    # for item in releases:
    #     reviews_map[item['id']] = fetch_reviews_for_item(item['title'], item['detailUrl'])
    # For now, return dummy data
    dummy_reviews_map = {"tmdb123": [{"source_name": "DummySite", "review_text": "Loved it!", "original_score": "9/10"}]}
    ti.xcom_push(key='reviews_map', value=dummy_reviews_map)
    # In reality: save_to_s3_raw(reviews_map, config['s3_raw_bucket'], 'reviews_map.json')


def preprocess_data_callable(**kwargs):
    print("Preprocessing data...")
    ti = kwargs['ti']
    # In reality: releases = load_df_from_s3_raw(config['s3_raw_bucket'], 'new_releases.parquet')
    # reviews_map = load_json_from_s3_raw(config['s3_raw_bucket'], 'reviews_map.json')
    releases = ti.xcom_pull(task_ids='scrape_new_releases_task', key='new_releases')
    reviews_map = ti.xcom_pull(task_ids='scrape_reviews_task', key='reviews_map')
    # processed_df = preprocess_raw_data(releases, reviews_map)
    # For now, use dummy processed data
    import pandas as pd
    processed_df = pd.DataFrame(releases) # Simplified
    processed_df['scraped_reviews'] = '[{"source_name": "DummySite", "review_text": "Loved it!"}]' # as JSON string
    processed_df['source_data_hash'] = "dummy_hash"

    ti.xcom_push(key='processed_df', value=processed_df.to_json()) # Pass DataFrame as JSON string via XCom
    # In reality: save_df_to_s3_parquet(processed_df, config['s3_processed_bucket'], 'processed_data.parquet')

def get_llm_predictions_callable(**kwargs):
    print("Getting LLM predictions...")
    ti = kwargs['ti']
    # config = load_config()
    # api_key = config['gemini_api_key'] # Fetched via Secrets Manager in prod
    # processed_df_json = ti.xcom_pull(task_ids='preprocess_data_task', key='processed_df')
    # import pandas as pd
    # processed_df = pd.read_json(processed_df_json)
    # enriched_df = enrich_with_gemini(processed_df, api_key)
    # For now, add dummy LLM columns
    import pandas as pd
    processed_df_json = ti.xcom_pull(task_ids='preprocess_data_task', key='processed_df')
    enriched_df = pd.read_json(processed_df_json)
    enriched_df['llm_review_summary'] = "Great movie!"
    enriched_df['llm_generated_score'] = 8.5
    enriched_df['llm_generated_vibe_tags'] = "exciting,fun"
    enriched_df['llm_generated_primary_genre'] = "Action"
    enriched_df['llm_generated_secondary_genres'] = "Adventure"
    enriched_df['data_ingestion_timestamp'] = datetime.now().isoformat()

    ti.xcom_push(key='enriched_df', value=enriched_df.to_json())
    # In reality: save_df_to_s3_parquet(enriched_df, config['s3_processed_bucket'], 'enriched_data.parquet')

def validate_data_callable(**kwargs):
    print("Validating data...")
    ti = kwargs['ti']
    # enriched_df_json = ti.xcom_pull(task_ids='get_llm_predictions_task', key='enriched_df')
    # import pandas as pd
    # enriched_df = pd.read_json(enriched_df_json)
    # success = validate_enriched_data(enriched_df)
    # if not success:
    #     raise ValueError("Data validation failed!")
    print("Validation successful (simulated).")


def load_to_datawarehouse_callable(**kwargs):
    print("Loading data to Redshift...")
    ti = kwargs['ti']
    # config = load_config()
    # enriched_df_json = ti.xcom_pull(task_ids='get_llm_predictions_task', key='enriched_df')
    # import pandas as pd
    # enriched_df = pd.read_json(enriched_df_json)
    # load_df_to_redshift(enriched_df,
    #                     host=config['redshift_host'], # Fetched via Secrets Manager in prod
    #                     database=config['redshift_db'],
    #                     user=config['redshift_user'],
    #                     password=config['redshift_password'],
    #                     table_name=config['redshift_table_name'],
    #                     schema_name=config['redshift_schema_name'])
    print("Load to Redshift successful (simulated).")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False, # Configure actual email later
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'data_ingestion_trending_now',
    default_args=default_args,
    description='Daily ingestion pipeline for Trending Now app',
    schedule_interval=timedelta(days=1), # Daily schedule
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['trending_now'],
) as dag:

    scrape_new_releases_task = PythonOperator(
        task_id='scrape_new_releases_task',
        python_callable=fetch_new_releases_callable,
    )

    scrape_reviews_task = PythonOperator(
        task_id='scrape_reviews_task',
        python_callable=fetch_reviews_callable,
    )

    preprocess_data_task = PythonOperator(
        task_id='preprocess_data_task',
        python_callable=preprocess_data_callable,
    )

    get_llm_predictions_task = PythonOperator(
        task_id='get_llm_predictions_task',
        python_callable=get_llm_predictions_callable,
    )

    validate_data_task = PythonOperator(
        task_id='validate_data_task',
        python_callable=validate_data_callable,
    )

    # DVC versioning task - assumes DVC is setup in Airflow worker environment
    # and data is accessible (e.g. config_base.yaml specifies s3_processed_bucket path)
    # This requires a shared volume or consistent way to access data files for dvc add.
    # For a full DVC integration, the path to data would be more explicit.
    # For simplicity here, assuming processed data is saved to a known path.
    version_data_task = BashOperator(
        task_id='version_data_task',
        bash_command="""
            # cd /path/to/dvc/project/data/processed
            # dvc add enriched_data.parquet
            # git add enriched_data.parquet.dvc
            # git commit -m "Automated: Update enriched data"
            # dvc push -r s3remote
            echo "DVC commands executed (simulated)."
        """,
        # Note: Actual DVC commands need project context, proper paths, and Git setup.
        # This task might be better handled by a PythonOperator calling DVC API
        # or a custom operator if running in managed Airflow where direct shell access is tricky.
    )

    load_to_datawarehouse_task = PythonOperator(
        task_id='load_to_datawarehouse_task',
        python_callable=load_to_datawarehouse_callable,
    )

    scrape_new_releases_task >> scrape_reviews_task >> preprocess_data_task >> \
    get_llm_predictions_task >> validate_data_task >> version_data_task >> \
    load_to_datawarehouse_task
```
*   **Note:**
    *   The PythonOperator callables will import functions from the scripts developed in Phase 2.
    *   Actual S3/DVC/Redshift interactions and API key handling need to be fleshed out in the Python scripts using `boto3`, `dvc`, `psycopg2-binary`, and Google Gemini SDK.
    *   Error handling: Use Airflow's `on_failure_callback` to send alerts (e.g., to Slack, email).
    *   XComs are used to pass small data (like filenames or pandas df as JSON) between tasks. For large data, tasks should read/write from S3.

**Phase 4: Unit Tests (`mlops/scripts/<subfolder>/tests/`)**

1.  For `justwatch_scraper.py`:
    *   Mock Justwatch API responses. Test `fetch_new_releases` for correct parsing and date filtering.
2.  For `review_scraper.py`:
    *   Mock HTML content of review sites. Test `fetch_reviews_for_item` for robust parsing.
3.  For `preprocess_data.py`:
    *   Test `preprocess_raw_data` with sample raw movie/review data. Verify schema, cleaning logic, join correctness.
4.  For `gemini_enricher.py`:
    *   Mock Gemini API client. Test `enrich_with_gemini` for correct prompt construction and parsing of dummy LLM responses for each enrichment type (summary, score, tags, genre).
5.  For `validate_with_ge.py`:
    *   Test `validate_enriched_data` with dataframes that should pass and fail defined expectations.
6.  For `redshift_loader.py` (to be created in `mlops/scripts/loading/`):
    *   Test `load_df_to_redshift` by mocking `psycopg2` connection and verifying SQL statements generated.

**Phase 5: Infrastructure as Code (`infrastructure/`)**

1.  **`main.tf` (Root module):**
    *   Defines AWS provider, region.
    *   Calls modules for S3, IAM, Redshift, Airflow (MWAA or EC2-based setup).
2.  **S3 Module (`infrastructure/modules/s3/`):**
    *   Creates S3 buckets for raw data, processed data, DVC remote, Airflow DAGs/logs.
    *   Configures bucket policies, versioning, lifecycle rules.
3.  **IAM Module (`infrastructure/modules/iam/`):**
    *   Creates IAM roles for:
        *   Airflow Worker/Scheduler (permissions for S3, Redshift, Secrets Manager, CloudWatch Logs).
        *   Lambda functions (if any used by Airflow).
        *   Terraform execution role for GitHub Actions.
    *   Defines necessary IAM policies.
4.  **Redshift Module (`infrastructure/modules/redshift/`):**
    *   Provisions a Redshift cluster (e.g., `dc2.large` for dev/staging).
    *   Configures security groups, parameter groups.
    *   Manages admin user credentials (store in AWS Secrets Manager).
5.  **Airflow Module (`infrastructure/modules/airflow/`):**
    *   Provisions MWAA environment OR sets up EC2-based Airflow (VPC, EC2, RDS for metadata, Security Groups). Define requirements for MWAA (DAG S3 path, plugins S3 path, execution role).
6.  **Secrets Manager Module (`infrastructure/modules/secrets/`):**
    *   Creates placeholders for `GEMINI_API_KEY`, `REDSHIFT_PASSWORD_DEV/STAGING/PROD`. These would be manually populated or via a secure process.
7.  **Variable files (`.tfvars`) for each environment (dev, staging, prod):**
    *   Define environment-specific parameters (instance sizes, bucket name suffixes).

**Phase 6: Integration Tests (`mlops/tests/integration/`)**

1.  `test_data_ingestion_pipeline.py` (using `pytest`):
    *   This test will be run *after* Terraform deploys the Staging environment.
    *   It could use the Airflow API (or CLI) to:
        *   Trigger the `data_ingestion_trending_now` DAG in Staging (with specific test configurations, e.g., pointing to mock scraping targets or a very small, fixed set of URLs).
        *   Poll for DAG completion.
        *   Verify outputs:
            *   Check S3 for expected raw/processed Parquet files.
            *   Verify DVC tracking files (.dvc) were updated/pushed.
            *   Query the Staging Redshift to ensure data was loaded correctly and matches the expected schema and sample content.
            *   Check Airflow logs for errors.

**Phase 7: GitHub Actions for CI/CD (`.github/workflows/`)**

1.  **`ci.yml` (Continuous Integration):**
    *   Trigger: On push to `feature/*` branches, or on PR to `dev` and `main`.
    *   Jobs:
        *   `lint_and_format`: Runs `black` and `flake8` on Python code.
        *   `unit_tests`: Runs `pytest mlops/scripts/**/tests/`.
        *   `terraform_validate_and_lint`: Runs `terraform validate` and `tflint` on `infrastructure/` code.
2.  **`cd_staging.yml` (Continuous Delivery to Staging):**
    *   Trigger: On merge/push to `dev` branch.
    *   Environment: `staging` (can use GitHub Environments for manual approval if needed later for pipeline runs).
    *   Jobs:
        *   `checkout_code`
        *   `setup_aws_credentials` (using GitHub Actions Secrets for Terraform role).
        *   `terraform_plan_staging`: `terraform plan -var-file=environments/staging.tfvars`
        *   `terraform_apply_staging`: `terraform apply -auto-approve -var-file=environments/staging.tfvars` (creates/updates S3, IAM, Redshift, Airflow).
        *   `deploy_airflow_dag`: Copies `data_ingestion_dag.py` and `mlops/scripts` to Airflow DAGs S3 location for MWAA (or appropriate path for EC2 Airflow).
        *   `run_integration_tests`: Executes `pytest mlops/tests/integration/` (configured to target Staging resources).
        *   `terraform_destroy_staging` (IF using ephemeral staging): `terraform destroy -auto-approve -var-file=environments/staging.tfvars`
3.  **`cd_production.yml` (Continuous Delivery to Production):**
    *   Trigger: On merge/push to `main` branch (typically after successful `dev` branch merge and Staging validation).
    *   Environment: `production` (with GitHub Environments **manual approval gate**).
    *   Jobs (similar to staging, but targets production variables):
        *   `checkout_code`
        *   `setup_aws_credentials`
        *   `terraform_plan_production`
        *   `terraform_apply_production`
        *   `deploy_airflow_dag_production`
        *   (Optional) `run_smoke_tests_production` (a very lightweight version of integration tests).

---
