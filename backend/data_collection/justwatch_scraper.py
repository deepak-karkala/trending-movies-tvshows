"""Script to scrape and collect movie and TV show data from JustWatch."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def load_env_vars():
    """Load environment variables from .env file in project root.

    Returns:
        str: The Firecrawl API key from environment variables.

    Raises:
        FileNotFoundError: If .env file is not found.
        ValueError: If FIRECRAWL_API_KEY is not set in .env file.
    """
    # Get the project root directory (3 levels up from this script)
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"

    if not env_path.exists():
        msg = (
            f".env file not found at {env_path}. "
            "Please create one with FIRECRAWL_API_KEY=your-api-key"
        )
        raise FileNotFoundError(msg)

    load_dotenv(env_path)

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY not found in environment variables")

    return api_key


def setup_logging():
    """Set up logging configuration with file and console handlers.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"scraper_{timestamp}.log"

    # File handler setup
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_formatter = logging.Formatter(file_fmt)
    file_handler.setFormatter(file_formatter)

    # Console handler setup
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = "%(levelname)s: %(message)s"
    console_formatter = logging.Formatter(console_fmt)
    console_handler.setFormatter(console_formatter)

    # Root logger setup
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


class JustWatchScraper:
    """Scraper class for extracting movie and TV show data from JustWatch."""

    def __init__(self, api_key: str, test_mode: bool = False, max_retries: int = 3):
        """Initialize the JustWatch scraper.

        Args:
            api_key: Firecrawl API key for authentication.
            test_mode: If True, only process 2 items for testing.
            max_retries: Maximum number of retry attempts for failed requests.
        """
        self.api_key = api_key
        self.base_url = "https://www.justwatch.com/us"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.test_mode = test_mode

        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get_detailed_content(self, url: str) -> Dict:
        """Get detailed information about a specific content item.

        Args:
            url: URL of the content detail page.

        Returns:
            Dict containing detailed information about the content item.
        """
        try:
            # Enhanced genre extraction by looking for specific HTML elements
            prompt = (
                "Extract detailed information about this movie/TV show. "
                "Include:\n"
                "- Title\n"
                "- Content type (movie/TV show)\n"
                "- All available streaming platforms\n"
                "- Release date\n"
                "- Genres(CRITICAL: Look for genre tags in these locations:\n"
                "  1. Genre section/tags near the top of the page\n"
                "  2. Genre links in the movie/show details\n"
                "  3. Genre information in the metadata section\n"
                "  4. Any additional genre classifications in the page)\n"
                "- Rating (IMDb, Rotten Tomatoes if available)\n"
                "- Full synopsis/description\n"
                "- Cast members with character names\n"
                "- Director(s)\n"
                "- Duration/runtime\n"
                "- Maturity rating\n"
                "- Original language\n"
                "- Production country\n\n"
                "For genres specifically:\n"
                "1. Check all sections of the page\n"
                "2. Include both primary and secondary genre classifications\n"
                "3. Look for genre-related keywords in the synopsis\n"
                "4. Check for genre tags in recommendations section"
            )

            response = self.session.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers=self.headers,
                json={
                    "url": url,
                    "formats": ["json"],
                    "waitFor": 5000,
                    "jsonOptions": {
                        "prompt": prompt,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "contentType": {"type": "string"},
                                "streamingPlatforms": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "releaseDate": {"type": "string"},
                                "genres": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Genre",
                                },
                                "imdbRating": {"type": "string"},
                                "rottenTomatoesRating": {"type": "string"},
                                "synopsis": {"type": "string"},
                                "cast": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "character": {"type": "string"},
                                        },
                                    },
                                },
                                "directors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "duration": {"type": "string"},
                                "maturityRating": {"type": "string"},
                                "language": {"type": "string"},
                                "country": {"type": "string"},
                                "yearReleased": {"type": "string"},
                            },
                            "required": ["title", "genres"],
                        },
                    },
                },
            )

            result = response.json()
            if result.get("success") and result.get("data", {}).get("json"):
                extracted_data = result["data"]["json"]
                debug_msg = (
                    f"Extracted data for "
                    f"{extracted_data.get('title', 'Unknown')}:"
                    f"\n{json.dumps(extracted_data, indent=2)}"
                )
                logger.debug(debug_msg)

                # Validate genre extraction
                if not extracted_data.get("genres"):
                    title = extracted_data.get("title", "Unknown")
                    logger.warning(
                        f"No genres found for {title}. "
                        "Attempting secondary extraction..."
                    )
                    # Could implement additional genre extraction methods here

                return extracted_data

            logger.warning(f"No data extracted from {url}")
            return {}

        except Exception as e:
            error_msg = "Error getting detailed content for " f"{url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {}

    def get_new_releases(self) -> List[Dict]:
        """Get list of new releases from JustWatch.

        Returns:
            List of dictionaries containing movie/show information.
        """
        try:
            logger.info("Starting new releases extraction")
            prompt = (
                "Extract information about all movies and TV shows listed on "
                "this page. For each item include:\n"
                "- Title\n"
                "- Content type (movie/TV show)\n"
                "- Streaming platforms where it's available\n"
                "- Release date or episode information\n"
                "- The URL to its detail page\n"
                "- Any genre information visible on the main page"
            )

            response = self.session.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers=self.headers,
                json={
                    "url": f"{self.base_url}/new",
                    "formats": ["json"],
                    "waitFor": 5000,
                    "jsonOptions": {
                        "prompt": prompt,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "contentType": {"type": "string"},
                                            "streamingPlatforms": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "releaseDate": {"type": "string"},
                                            "detailUrl": {"type": "string"},
                                            "genres": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                        },
                                    },
                                }
                            },
                        },
                    },
                },
            )

            result = response.json()
            has_items = result.get("success") and result.get("data", {}).get(
                "json", {}
            ).get("items")
            if not has_items:
                logger.warning("No items found in new releases")
                return []

            items = result["data"]["json"]["items"]
            total_items = len(items)
            logger.info(f"Found {total_items} items in new releases")

            if self.test_mode:
                items = items[:2]
                test_msg = (
                    "Test mode: Processing only first 2 items " f"out of {total_items}"
                )
                logger.info(test_msg)

            detailed_items = []

            for idx, item in enumerate(items, 1):
                logger.info(f"Processing item {idx}/{len(items)}: " f"{item['title']}")
                if "detailUrl" in item:
                    detail_url = (
                        item["detailUrl"]
                        if item["detailUrl"].startswith("http")
                        else urljoin(self.base_url, item["detailUrl"])
                    )
                    logger.debug(f"Fetching details from: {detail_url}")
                    detailed_info = self._get_detailed_content(detail_url)
                    if detailed_info:
                        merged_item = {**item, **detailed_info}
                        detailed_items.append(merged_item)
                        logger.info(f"Successfully processed {item['title']}")
                    else:
                        msg = (
                            f"Could not get detailed info for "
                            f"{item['title']}, using basic info only"
                        )
                        logger.warning(msg)
                        detailed_items.append(item)
                else:
                    logger.warning("No detail URL found for " f"{item['title']}")
                    detailed_items.append(item)
                time.sleep(1)  # Rate limiting

            logger.info(f"Completed processing {len(detailed_items)} items")
            return detailed_items

        except Exception as e:
            error_msg = "Error getting new releases: " f"{str(e)}"
            logger.error(error_msg, exc_info=True)
            return []

    def save_data(self, data: List[Dict], output_dir: str = None):
        """Save scraped data to JSON and CSV files.

        Args:
            data: List of dictionaries containing movie/show information.
            output_dir: Optional directory path to save the files.
                       If None, saves to project's data/raw directory.
        """
        try:
            if output_dir is None:
                # Use the root data directory
                output_dir = (
                    Path(__file__).resolve().parent.parent.parent / "data" / "raw"
                )
            else:
                output_dir = Path(output_dir).resolve()

            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving data to: {output_dir}")

            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save raw JSON
            json_path = output_dir / f"justwatch_data_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved JSON data to: {json_path}")

            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(data)
            csv_path = output_dir / f"justwatch_data_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved CSV data to: {csv_path}")

            # Log data statistics
            logger.info(f"Saved {len(data)} items")
            if len(data) > 0:
                logger.info("Fields captured: " f"{', '.join(data[0].keys())}")
                genres_found = sum(1 for item in data if item.get("genres"))
                logger.info(f"Items with genres: {genres_found}/{len(data)}")

        except Exception as e:
            logger.error(f"Error saving data: {str(e)}", exc_info=True)
            raise


def main():
    """Run the JustWatch scraper to collect movie and TV show data."""
    try:
        # Load API key from environment variables
        api_key = load_env_vars()

        # Get test mode from environment or default to False
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        logger.info("Initializing JustWatch scraper")
        scraper = JustWatchScraper(api_key=api_key, test_mode=test_mode)

        logger.info("Starting data collection")
        data = scraper.get_new_releases()

        if data:
            scraper.save_data(data)
            logger.info("Data collection completed successfully")
        else:
            logger.error("No data collected")

    except Exception as e:
        logger.error(f"Script failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
