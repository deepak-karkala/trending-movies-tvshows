"""Scraper for fetching reviews for movies and TV shows using Firecrawl search and scrape."""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..utils.config_loader import load_config

# Imports for Firecrawl tools and their arguments
from .default_api import (
    McpFirecrawl_mcpFirecrawlScrapeExtract,
    McpFirecrawl_mcpFirecrawlSearchScrapeoptions,
    mcp_firecrawl_scrape,
    mcp_firecrawl_search,
)

logger = logging.getLogger(__name__)


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
    """Search for review pages using Firecrawl."""
    search_query = f"{item_title} movie reviews"
    if "tv-show" in item_detail_url or "series" in item_detail_url.lower():
        search_query = f"{item_title} TV series reviews"

    logger.info(f"Searching for reviews with query: '{search_query}'")
    try:
        search_results_response = mcp_firecrawl_search(
            query=search_query,
            limit=search_limit,
            scrapeOptions=McpFirecrawl_mcpFirecrawlSearchScrapeoptions(
                formats=["markdown"]  # Not strictly needed if only using URLs
            ),
        )

        if isinstance(search_results_response, list):
            return search_results_response
        if isinstance(search_results_response, dict) and isinstance(
            search_results_response.get("data"), list
        ):
            return search_results_response["data"]
        if isinstance(search_results_response, dict) and isinstance(
            search_results_response.get("results"), list
        ):
            return search_results_response["results"]

        logger.warning(
            f"Unexpected format from review search for '{item_title}'. Response: {search_results_response}"
        )
        return []
    except Exception as e_search:
        logger.error(
            f"Error during Firecrawl search for '{item_title}': {e_search}",
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
    """Scrape a single page for reviews using Firecrawl."""
    page_reviews: List[Dict[str, Any]] = []
    logger.info(f"Attempting to scrape reviews from: {page_url} (Title: {page_title})")
    try:
        scraped_page_response = mcp_firecrawl_scrape(
            url=page_url,
            formats=["extract"],
            extract=McpFirecrawl_mcpFirecrawlScrapeExtract(
                prompt=review_extract_prompt.format(
                    max_reviews_per_site=max_reviews_per_site
                ),
                schema=review_extract_schema,
            ),
            onlyMainContent=True,
            waitFor=3000,  # Shorter wait for review pages
        )

        extracted_data = None
        if isinstance(scraped_page_response, dict):
            if (
                "extract" in scraped_page_response
                and isinstance(scraped_page_response.get("extract"), dict)
                and isinstance(scraped_page_response["extract"].get("data"), list)
            ):
                extracted_data = scraped_page_response["extract"]["data"]
            elif "data" in scraped_page_response and isinstance(
                scraped_page_response.get("data"), list
            ):
                extracted_data = scraped_page_response["data"]

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
                f"No reviews extracted or unexpected format from {page_url}. Response: {scraped_page_response}"
            )
    except Exception as e_scrape:
        logger.error(
            f"Error scraping review page {page_url} for '{item_title}': {e_scrape}",
            exc_info=True,
        )

    return page_reviews


def fetch_reviews_for_item(
    item_title: str,
    item_detail_url: str,  # Kept for context
    max_search_results_to_process: int = 3,  # Max search results to attempt to scrape
    max_reviews_per_site: int = 1,  # Max reviews to extract from a single site page
    firecrawl_api_key: Optional[str] = None,  # For MCP tool consistency
) -> List[Dict[str, Any]]:
    """Fetch reviews for a given movie/TV show using Firecrawl search and scrape.

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

    # Load .env for API keys if testing locally and MCP doesn't handle it
    # from dotenv import load_dotenv
    # project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # load_dotenv(os.path.join(project_root, '.env'))

    api_key = os.getenv("FIRECRAWL_API_KEY", "dummy_api_key_if_mcp_handles_auth")
    if api_key == "dummy_api_key_if_mcp_handles_auth":
        logger.info("FIRECRAWL_API_KEY not set in env. Assuming MCP tool handles auth.")

    sample_movie_title = "Inception"
    sample_movie_url = "https://www.justwatch.com/us/movie/inception"

    print(
        f"Fetching reviews for '{sample_movie_title}' using Firecrawl Search & Scrape..."
    )
    movie_reviews = fetch_reviews_for_item(
        sample_movie_title,
        sample_movie_url,
        max_search_results_to_process=2,
        max_reviews_per_site=1,
        firecrawl_api_key=api_key,
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

    print(
        f"\nFetching reviews for '{sample_tv_show_title}' using Firecrawl Search & Scrape..."
    )
    tv_reviews = fetch_reviews_for_item(
        sample_tv_show_title,
        sample_tv_show_url,
        max_search_results_to_process=2,  # Try to scrape top 2 search results
        max_reviews_per_site=1,  # Extract 1 review from each
        firecrawl_api_key=api_key,
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
