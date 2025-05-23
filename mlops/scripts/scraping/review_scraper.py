"""Scraper for fetching reviews for movies and TV shows using the Firecrawl direct API."""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

from ..utils.config_loader import load_config

logger = logging.getLogger(__name__)


# --- API Key Handling and Session Setup ---
def load_env_vars() -> str:
    """Load environment variables from .env file in project root.

    Returns:
        str: The Firecrawl API key from environment variables.

    Raises:
        FileNotFoundError: If .env file is not found.
        ValueError: If FIRECRAWL_API_KEY is not set in .env file.
    """
    # Get the project root directory (3 levels up from this script)
    project_root = Path(__file__).resolve().parent.parent.parent.parent 
    # Assuming this script is in mlops/scripts/scraping, .env is at project root
    env_path = project_root / ".env"

    if not env_path.exists():
        # Try one level higher if structure is different (e.g. running from mlops/scripts)
        project_root_alt = Path(__file__).resolve().parent.parent.parent
        env_path_alt = project_root_alt / ".env"
        if not env_path_alt.exists():
            msg = (
                f".env file not found at {env_path} or {env_path_alt}. "
                "Please create one with FIRECRAWL_API_KEY=your-api-key"
            )
            logger.error(msg)
            raise FileNotFoundError(msg)
        env_path = env_path_alt

    load_dotenv(env_path)
    logger.info(f"Loaded .env file from: {env_path}")

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        msg = "FIRECRAWL_API_KEY not found in environment variables."
        logger.error(msg)
        raise ValueError(msg)
    logger.info("FIRECRAWL_API_KEY loaded successfully.")
    return api_key


API_KEY = load_env_vars()
SESSION = requests.Session()
SESSION.headers.update(
    {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)
# --- End API Key Handling and Session Setup ---


def _get_domain_name(url: str) -> str:
    """Extract the domain name from a URL to use as a plausible review source name."""
    try:
        # Handle URLs without scheme
        if url and not url.startswith(("http://", "https://", "ftp://")):
            if url.startswith("www."):
                url = "http://" + url
            else:
                # Try to handle bare domains
                if "." in url and not url.startswith(".") and not url.endswith("."):
                    url = "http://" + url
                else:
                    return "Unknown Source"

        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            return "Unknown Source"
        return parsed_url.netloc.replace("www.", "")
    except Exception:
        logger.warning(f"Could not parse domain from URL: {url}")
        return "Unknown Source"


def _search_for_review_pages(
    item_title: str, item_detail_url: str, search_limit: int
) -> List[Dict[str, Any]]:
    """Search for review pages using Firecrawl's direct API."""
    search_query = f"{item_title} movie reviews"
    if "tv-show" in item_detail_url or "series" in item_detail_url.lower():
        search_query = f"{item_title} TV series reviews"

    logger.info(f"Searching for reviews with query: '{search_query}'")
    payload = {
        "query": search_query,
        "searchOptions": {"limit": search_limit},
        # "pageOptions": { "fetchTimeout": 15000 } # Optional
    }
    try:
        response = SESSION.post("https://api.firecrawl.dev/v1/search", json=payload)
        response.raise_for_status()
        search_results = response.json()

        if search_results and isinstance(search_results.get("data"), list):
            # Firecrawl search API returns a list of dicts with 'url', 'title', 'markdown', 'metadata'
            # We are primarily interested in 'url' and 'title'
            return [
                {"url": r.get("url"), "title": r.get("title", "Unknown Source")}
                for r in search_results["data"]
                if r.get("url") # Ensure URL is present
            ]
        
        logger.warning(
            f"Unexpected format or empty data from review search for '{item_title}'. Response: {search_results}"
        )
        return []
    except requests.exceptions.RequestException as e_req:
        logger.error(
            f"Request error during Firecrawl search for '{item_title}': {e_req}",
            exc_info=True,
        )
        return []
    except Exception as e_search:
        logger.error(
            f"Error processing Firecrawl search response for '{item_title}': {e_search}",
            exc_info=True,
        )
        return []


def _scrape_reviews_from_page(
    page_url: str,
    page_title: str,
    item_title: str,
    max_reviews_per_site: int,
    review_extract_prompt: str,
    review_extract_schema: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Scrape a single page for reviews using Firecrawl's direct API."""
    page_reviews: List[Dict[str, Any]] = []
    logger.info(f"Attempting to scrape reviews from: {page_url} (Title: {page_title})")

    payload = {
        "url": page_url,
        "extractorOptions": {
            "mode": "llm-extraction",
            "extractionPrompt": review_extract_prompt.format(
                max_reviews_per_site=max_reviews_per_site
            ),
            "extractionSchema": review_extract_schema,
        },
        # "pageOptions": { "waitFor": 3000 }, # Optional
        # "scrapeOptions": { "onlyMainContent": True } # Optional
    }
    try:
        response = SESSION.post("https://api.firecrawl.dev/v1/scrape", json=payload)
        response.raise_for_status()
        scraped_page_data = response.json()

        extracted_data = None
        if (
            scraped_page_data
            and isinstance(scraped_page_data.get("data"), dict)
            and isinstance(
                scraped_page_data["data"].get("llm_extraction"), list
            ) # Schema expects a list
        ):
            extracted_data = scraped_page_data["data"]["llm_extraction"]
        elif ( # Fallback for older or different structures if any
            scraped_page_data
            and isinstance(scraped_page_data.get("data"), dict)
            and isinstance(
                scraped_page_data["data"].get("extracted_data"), list
            )
        ):
             extracted_data = scraped_page_data["data"]["extracted_data"]


        if extracted_data:
            logger.info(
                f"Successfully extracted {len(extracted_data)} review items from {page_url}"
            )
            for review_data in extracted_data[:max_reviews_per_site]:
                if isinstance(review_data, dict) and review_data.get("review_text"):
                    full_review = {
                        "source_name": review_data.get("reviewer_name")
                        or _get_domain_name(page_url),
                        "review_text": review_data["review_text"].strip(),
                        "original_score": review_data.get("original_score"),
                        "review_url": page_url,
                    }
                    page_reviews.append(full_review)
                else:
                    logger.warning(
                        f"Skipping invalid review data from {page_url}: {review_data}"
                    )
        else:
            logger.warning(
                f"No reviews extracted or unexpected format from {page_url}. Response: {scraped_page_data}"
            )
    except requests.exceptions.RequestException as e_req:
        logger.error(
            f"Request error scraping review page {page_url} for '{item_title}': {e_req}",
            exc_info=True,
        )
    except Exception as e_scrape:
        logger.error(
            f"Error processing scrape response for review page {page_url} for '{item_title}': {e_scrape}",
            exc_info=True,
        )

    return page_reviews


def fetch_reviews_for_item(
    item_title: str,
    item_detail_url: str,  # Kept for context
    max_search_results_to_process: int = 3,  # Max search results to attempt to scrape
    max_reviews_per_site: int = 1,  # Max reviews to extract from a single site page
) -> List[Dict[str, Any]]:
    """Fetch reviews for a given movie/TV show using Firecrawl's direct API.

    Orchestrates searching for review pages and then scraping each page.
    """
    config = load_config()
    search_limit = config.get("scraping", {}).get("review_search_limit", 5)
    max_total_reviews = config.get("scraping", {}).get("max_total_reviews_per_item", 5)

    logger.info(f"Fetching reviews for: '{item_title}' (Source URL: {item_detail_url})")

    search_results = _search_for_review_pages(item_title, item_detail_url, search_limit)

    if not search_results:
        logger.info(f"No search results found for review query for '{item_title}'")
        return []

    logger.info(
        f"Found {len(search_results)} potential review pages for '{item_title}'. Processing top {max_search_results_to_process}."
    )

    review_extract_prompt = (
        "Extract up to {max_reviews_per_site} distinct reviews from this page. "
        "For each review, provide: the review text itself (review_text), "
        "any stated original score or rating (original_score, e.g., '8/10', '4 stars', 'A-'), "
        "and the name of the reviewer or publication if clearly identifiable (reviewer_name). "
        "Focus on actual review content, not summaries or metadata about the movie/show itself."
    )

    review_extract_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "reviewer_name": {
                    "type": "string",
                    "description": "Name of the reviewer or publication",
                },
                "review_text": {
                    "type": "string",
                    "description": "The full text of the review",
                },
                "original_score": {
                    "type": "string",
                    "description": "The score given in the review, as text",
                },
            },
            "required": ["review_text"],
        },
    }

    collected_reviews: List[Dict[str, Any]] = []
    for result in search_results[:max_search_results_to_process]:
        if len(collected_reviews) >= max_total_reviews:
            logger.info(
                f"Reached max total reviews ({max_total_reviews}) for {item_title}."
            )
            break

        page_url = result.get("url")
        page_title = result.get("title", "Unknown Page")

        if not page_url:
            logger.warning(f"Search result for '{item_title}' missing URL: {result}")
            continue

        reviews_from_page = _scrape_reviews_from_page(
            page_url,
            page_title,
            item_title,
            max_reviews_per_site,
            review_extract_prompt,
            review_extract_schema,
        )

        for review in reviews_from_page:
            if len(collected_reviews) < max_total_reviews:
                collected_reviews.append(review)
            else:
                break  # Break inner loop if max_total_reviews reached

    if not collected_reviews:
        logger.info(f"No reviews ultimately collected for '{item_title}'.")
    else:
        logger.info(
            f"Successfully collected {len(collected_reviews)} reviews for '{item_title}'."
        )

    return collected_reviews


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Ensure API_KEY is loaded (it's done globally at script start via load_env_vars()).
    # No need to load .env here explicitly as it's handled by the global API_KEY initialization.

    # The API_KEY is now global, so no need to pass it around or fetch from env here.
    # If API_KEY is not set, the script would have failed at `load_env_vars()`.
    logger.info(f"Using globally loaded FIRECRAWL_API_KEY for '{sample_movie_title}'.")
    
    sample_movie_title = "Inception"
    sample_movie_url = "https://www.justwatch.com/us/movie/inception"

    print(
        f"Fetching reviews for '{sample_movie_title}' using Firecrawl direct API..."
    )
    movie_reviews = fetch_reviews_for_item(
        sample_movie_title,
        sample_movie_url,
        max_search_results_to_process=2,
        max_reviews_per_site=1
    )

    if movie_reviews:
        print(
            f"\n--- Collected Reviews for {sample_movie_title} ({len(movie_reviews)}) ---"
        )
        for i, rev in enumerate(movie_reviews):
            print(f"Review {i + 1}:")
            print(f"  Source: {rev.get('source_name')}")
            print(f"  URL: {rev.get('review_url')}")
            print(f"  Score: {rev.get('original_score', 'N/A')}")
            print(f"  Text: {rev.get('review_text', '')[:200]}...")
            print("---")
    else:
        print(f"No reviews found for '{sample_movie_title}'.")

    sample_tv_show_title = "Breaking Bad"
    sample_tv_show_url = "https://www.justwatch.com/us/tv-show/breaking-bad"

    logger.info(f"Using globally loaded FIRECRAWL_API_KEY for '{sample_tv_show_title}'.")
    print(
        f"\nFetching reviews for '{sample_tv_show_title}' using Firecrawl direct API..."
    )
    tv_reviews = fetch_reviews_for_item(
        sample_tv_show_title,
        sample_tv_show_url,
        max_search_results_to_process=2,  # Try to scrape top 2 search results
        max_reviews_per_site=1  # Extract 1 review from each
    )

    if tv_reviews:
        print(
            f"\n--- Collected Reviews for {sample_tv_show_title} ({len(tv_reviews)}) ---"
        )
        for i, rev in enumerate(tv_reviews):
            print(f"Review {i + 1}:")
            print(f"  Source: {rev.get('source_name')}")
            print(f"  URL: {rev.get('review_url')}")
            print(f"  Score: {rev.get('original_score', 'N/A')}")
            print(f"  Text: {rev.get('review_text', '')[:200]}...")
            print("---")
    else:
        print(f"No reviews found for '{sample_tv_show_title}'.")
