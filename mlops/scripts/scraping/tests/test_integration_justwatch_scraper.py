"""Integration tests for JustWatch scraper using real Firecrawl API."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from mlops.scripts.scraping.justwatch_scraper import JustWatchScraper

# Ensure logs are captured during tests
logging.basicConfig(level=logging.INFO)

# Skip all tests if FIRECRAWL_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("FIRECRAWL_API_KEY"),
    reason="FIRECRAWL_API_KEY environment variable not set",
)


@pytest.fixture
def firecrawl_api_key() -> Generator[str, None, None]:
    """Fixture to get Firecrawl API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        pytest.skip("FIRECRAWL_API_KEY environment variable not set")
    yield api_key


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Fixture to create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.mark.integration
def test_scraper_test_mode(firecrawl_api_key, temp_output_dir):
    """Test the scraper in test mode (limited to 2 items).

    This test verifies that:
    1. Test mode correctly limits to 2 items
    2. Basic data structure and required fields are present
    3. Data is saved correctly to files
    """
    # Initialize scraper in test mode
    scraper = JustWatchScraper(api_key=firecrawl_api_key, test_mode=True)

    # Get new releases
    releases = scraper.get_new_releases()

    # Basic validation
    assert isinstance(releases, list), "Expected a list of releases"
    assert len(releases) == 2, "Test mode should return exactly 2 items"

    # Validate structure of each release
    for release in releases:
        assert isinstance(release, dict), "Each release should be a dictionary"
        # Required fields
        assert "title" in release and isinstance(release["title"], str)
        assert "contentType" in release and release["contentType"].lower() in [
            "movie",
            "tv show",
        ]
        assert "detailUrl" in release and isinstance(release["detailUrl"], str)
        assert "streamingPlatforms" in release and isinstance(
            release["streamingPlatforms"], list
        )
        assert "genres" in release and isinstance(release["genres"], list)
        # Optional but expected fields
        if "synopsis" in release:
            assert isinstance(release["synopsis"], str)
        if "cast" in release:
            assert isinstance(release["cast"], list)
            for cast_member in release["cast"]:
                assert isinstance(cast_member, dict)
                assert "name" in cast_member
                assert "character" in cast_member

    # Test data saving
    scraper.save_data(releases, output_dir=str(temp_output_dir))
    saved_files = list(temp_output_dir.glob("*"))
    assert any(
        f.name.endswith(".json") for f in saved_files
    ), "JSON file should be created"
    assert any(
        f.name.endswith(".csv") for f in saved_files
    ), "CSV file should be created"
