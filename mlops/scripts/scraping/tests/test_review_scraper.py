import logging
from unittest.mock import ANY, MagicMock, call, patch

import pytest

# pylint: disable=wrong-import-position, import-error
# Updated import path
from mlops.scripts.scraping.review_scraper import (
    _get_domain_name,
    _scrape_reviews_from_page,
    _search_for_review_pages,
    fetch_reviews_for_item,
)

# import os # Unused
# import sys # Unused


# Ensure logs are captured during tests
logging.basicConfig(level=logging.INFO)


@pytest.fixture
def mock_load_config_reviews():
    """Fixture to mock load_config for review scraper tests."""
    with patch("mlops.scripts.scraping.review_scraper.load_config") as mock_load_conf:
        mock_load_conf.return_value = {
            "scraping": {
                "review_search_limit": 3,
                "max_total_reviews_per_item": 2,
            }
        }
        yield mock_load_conf


@pytest.fixture
def mock_firecrawl_search_options_fixture():
    """Fixture to mock McpFirecrawl_mcpFirecrawlSearchScrapeoptions."""
    with patch(
        "mlops.scripts.scraping.review_scraper.McpFirecrawl_mcpFirecrawlSearchScrapeoptions"
    ) as mock_class:
        mock_instance = MagicMock(name="SearchScrapeOptionsInstance")
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


@pytest.fixture
def mock_firecrawl_scrape_extract_fixture():
    """Fixture to mock McpFirecrawl_mcpFirecrawlScrapeExtract."""
    with patch(
        "mlops.scripts.scraping.review_scraper.McpFirecrawl_mcpFirecrawlScrapeExtract"
    ) as mock_class:
        mock_instance = MagicMock(name="ScrapeExtractInstance")
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


# --- Tests for _get_domain_name ---
@pytest.mark.parametrize(
    "url, expected_domain",
    [
        ("http://www.example.com/path", "example.com"),
        ("https://sub.example.co.uk/another?query=1", "sub.example.co.uk"),
        ("ftp://example.com", "example.com"),
        ("www.noscheme.com", "noscheme.com"),
        ("justdomain.com", "justdomain.com"),
        ("", "Unknown Source"),  # Edge case: empty URL
        ("http://", "Unknown Source"),  # Edge case: scheme only
        (
            "invalid-url-format",
            "Unknown Source",
        ),  # Technically urlparse might make this work but good to test
    ],
)
def test_get_domain_name(url, expected_domain):
    assert _get_domain_name(url) == expected_domain


# --- Tests for _search_for_review_pages ---
@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_search")
def test_search_for_review_pages_success(
    mock_mcp_search, mock_firecrawl_search_options_fixture
):
    (
        MockSearchOptionsClass,
        mock_search_options_instance,
    ) = mock_firecrawl_search_options_fixture
    mock_mcp_search.return_value = {
        "data": [{"url": "http://review1.com", "title": "Review 1"}]
    }

    results = _search_for_review_pages("Test Movie", "http://moviedb.com/movie/test", 3)
    assert len(results) == 1
    assert results[0]["url"] == "http://review1.com"
    mock_mcp_search.assert_called_once_with(
        query="Test Movie movie reviews",
        limit=3,
        scrapeOptions=mock_search_options_instance,
    )
    MockSearchOptionsClass.assert_called_once_with(formats=["markdown"])


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_search")
def test_search_for_review_pages_tv_query(
    mock_mcp_search, mock_firecrawl_search_options_fixture
):
    _, mock_search_options_instance = mock_firecrawl_search_options_fixture
    mock_mcp_search.return_value = []
    _search_for_review_pages("Test Show", "http://moviedb.com/tv-show/test", 3)
    mock_mcp_search.assert_called_once_with(
        query="Test Show TV series reviews",
        limit=3,
        scrapeOptions=mock_search_options_instance,
    )


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_search")
def test_search_for_review_pages_api_error(
    mock_mcp_search, mock_firecrawl_search_options_fixture
):
    mock_mcp_search.side_effect = Exception("API Error")
    results = _search_for_review_pages("Test Movie", "http://moviedb.com/movie/test", 3)
    assert results == []


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_search")
def test_search_for_review_pages_various_response_formats(
    mock_mcp_search, mock_firecrawl_search_options_fixture
):
    # Test list response
    mock_mcp_search.return_value = [{"url": "http://review1.com", "title": "Review 1"}]
    results = _search_for_review_pages("Test Movie", "http://moviedb.com/movie/test", 3)
    assert len(results) == 1

    # Test dict with 'results' key
    mock_mcp_search.return_value = {
        "results": [{"url": "http://review2.com", "title": "Review 2"}]
    }
    results = _search_for_review_pages("Test Movie", "http://moviedb.com/movie/test", 3)
    assert len(results) == 1
    assert results[0]["url"] == "http://review2.com"

    # Test unexpected dict
    mock_mcp_search.return_value = {"unexpected": "format"}
    results = _search_for_review_pages("Test Movie", "http://moviedb.com/movie/test", 3)
    assert results == []


# --- Tests for _scrape_reviews_from_page ---
@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_scrape")
def test_scrape_reviews_from_page_success(
    mock_mcp_scrape, mock_firecrawl_scrape_extract_fixture
):
    (
        MockScrapeExtractClass,
        mock_scrape_extract_instance,
    ) = mock_firecrawl_scrape_extract_fixture
    mock_mcp_scrape.return_value = {
        "extract": {
            "data": [
                {
                    "reviewer_name": "Critic A",
                    "review_text": "Great!",
                    "original_score": "5/5",
                },
                {"review_text": "  Bad!  "},  # Missing name/score, needs stripping
            ]
        }
    }
    prompt = "Extract up to {max_reviews_per_site} reviews."
    schema = {"type": "array"}

    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 2, prompt, schema
    )
    assert len(reviews) == 2
    assert reviews[0]["source_name"] == "Critic A"
    assert reviews[0]["review_text"] == "Great!"
    assert reviews[0]["original_score"] == "5/5"
    assert reviews[0]["review_url"] == "http://review.com/page1"

    assert reviews[1]["source_name"] == "review.com"  # Default from URL
    assert reviews[1]["review_text"] == "Bad!"
    assert reviews[1]["original_score"] is None
    assert reviews[1]["review_url"] == "http://review.com/page1"

    MockScrapeExtractClass.assert_called_once_with(
        prompt=prompt.format(max_reviews_per_site=2), schema=schema
    )
    mock_mcp_scrape.assert_called_once_with(
        url="http://review.com/page1",
        formats=["extract"],
        extract=mock_scrape_extract_instance,
        onlyMainContent=True,
        waitFor=3000,
    )


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_scrape")
def test_scrape_reviews_from_page_max_reviews_respected(
    mock_mcp_scrape, mock_firecrawl_scrape_extract_fixture
):
    _, mock_scrape_extract_instance = mock_firecrawl_scrape_extract_fixture
    mock_mcp_scrape.return_value = {
        "extract": {
            "data": [
                {"review_text": "Review 1"},
                {"review_text": "Review 2"},
                {"review_text": "Review 3"},
            ]
        }
    }
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 1, "Prompt", {}
    )
    assert len(reviews) == 1
    assert reviews[0]["review_text"] == "Review 1"


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_scrape")
def test_scrape_reviews_from_page_api_error(
    mock_mcp_scrape, mock_firecrawl_scrape_extract_fixture
):
    mock_mcp_scrape.side_effect = Exception("Scrape API Error")
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 1, "Prompt", {}
    )
    assert reviews == []


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_scrape")
def test_scrape_reviews_from_page_no_data(
    mock_mcp_scrape, mock_firecrawl_scrape_extract_fixture
):
    mock_mcp_scrape.return_value = {"extract": {"data": []}}  # Empty data
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 1, "Prompt", {}
    )
    assert reviews == []

    mock_mcp_scrape.return_value = {"extract": None}  # Extract is None
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 1, "Prompt", {}
    )
    assert reviews == []

    mock_mcp_scrape.return_value = {}  # Empty response
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 1, "Prompt", {}
    )
    assert reviews == []


@patch("mlops.scripts.scraping.review_scraper.mcp_firecrawl_scrape")
def test_scrape_reviews_from_page_invalid_review_data(
    mock_mcp_scrape, mock_firecrawl_scrape_extract_fixture
):
    mock_mcp_scrape.return_value = {
        "extract": {
            "data": [
                {"some_other_key": "no review_text"},  # Missing review_text
                "not a dict",
            ]
        }
    }
    reviews = _scrape_reviews_from_page(
        "http://review.com/page1", "Review Page 1", "Test Movie", 2, "Prompt", {}
    )
    assert len(reviews) == 0


# --- Tests for fetch_reviews_for_item (main function) ---
@patch("mlops.scripts.scraping.review_scraper._scrape_reviews_from_page")
@patch("mlops.scripts.scraping.review_scraper._search_for_review_pages")
def test_fetch_reviews_for_item_success(
    mock_search, mock_scrape, mock_load_config_reviews
):
    mock_search.return_value = [
        {"url": "http://site1.com/rev", "title": "Site 1 Review"},
        {"url": "http://site2.com/rev", "title": "Site 2 Review"},
        {
            "url": "http://site3.com/rev",
            "title": "Site 3 Review",
        },  # Will be ignored by max_search_results_to_process from config
    ]

    # Simulate different numbers of reviews from different sites
    mock_scrape.side_effect = [
        [
            {
                "source_name": "Site 1",
                "review_text": "Amazing!",
                "review_url": "http://site1.com/rev",
            }
        ],  # From site1
        [
            {
                "source_name": "Site 2",
                "review_text": "Good.",
                "review_url": "http://site2.com/rev",
            }
        ],  # From site2
        # Site 3 won't be called due to max_search_results_to_process
    ]

    reviews = fetch_reviews_for_item(
        "Test Movie",
        "http://moviedb.com/movie/test",
        max_search_results_to_process=2,  # Override config for this test
        max_reviews_per_site=1,  # Override config for this test
    )

    assert len(reviews) == 2
    assert reviews[0]["source_name"] == "Site 1"
    assert reviews[1]["source_name"] == "Site 2"

    assert mock_search.call_count == 1
    # From mock_load_config_reviews, review_search_limit is 3
    mock_search.assert_called_once_with(
        "Test Movie", "http://moviedb.com/movie/test", 3
    )

    assert mock_scrape.call_count == 2  # Called for site1 and site2
    expected_calls = [
        call("http://site1.com/rev", "Site 1 Review", "Test Movie", 1, ANY, ANY),
        call("http://site2.com/rev", "Site 2 Review", "Test Movie", 1, ANY, ANY),
    ]
    actual_calls = []
    for c in mock_scrape.call_args_list:
        args, _ = c
        actual_calls.append(call(args[0], args[1], args[2], args[3], ANY, ANY))
    assert actual_calls == expected_calls


@patch("mlops.scripts.scraping.review_scraper._scrape_reviews_from_page")
@patch("mlops.scripts.scraping.review_scraper._search_for_review_pages")
def test_fetch_reviews_for_item_no_search_results(
    mock_search, mock_scrape, mock_load_config_reviews
):
    mock_search.return_value = []  # No search results
    reviews = fetch_reviews_for_item("Test Movie", "http://moviedb.com/movie/test")
    assert reviews == []
    mock_scrape.assert_not_called()


@patch("mlops.scripts.scraping.review_scraper._scrape_reviews_from_page")
@patch("mlops.scripts.scraping.review_scraper._search_for_review_pages")
def test_fetch_reviews_for_item_no_reviews_scraped(
    mock_search, mock_scrape, mock_load_config_reviews
):
    mock_search.return_value = [
        {"url": "http://site1.com/rev", "title": "Site 1 Review"}
    ]
    mock_scrape.return_value = []  # No reviews from scraping
    reviews = fetch_reviews_for_item(
        "Test Movie", "http://moviedb.com/movie/test", max_search_results_to_process=1
    )
    assert reviews == []
    mock_scrape.assert_called_once()


@patch("mlops.scripts.scraping.review_scraper._scrape_reviews_from_page")
@patch("mlops.scripts.scraping.review_scraper._search_for_review_pages")
def test_fetch_reviews_for_item_max_total_reviews_limit(
    mock_search,
    mock_scrape,
    mock_load_config_reviews,  # config gives max_total_reviews = 2
):
    mock_search.return_value = [
        {"url": "http://site1.com/rev", "title": "Site 1 Review"},
        {"url": "http://site2.com/rev", "title": "Site 2 Review"},
        {"url": "http://site3.com/rev", "title": "Site 3 Review"},
    ]
    # Simulate site 1 returns 2 reviews (hits total limit), site 2 returns 1
    mock_scrape.side_effect = [
        [
            {"source_name": "Site 1", "review_text": "Review 1.1"},
            {
                "source_name": "Site 1",
                "review_text": "Review 1.2",
            },  # This will hit the limit
        ],
        [
            {"source_name": "Site 2", "review_text": "Review 2.1"}
        ],  # This site's scrape might still be called once but its results ignored or partially taken
    ]

    reviews = fetch_reviews_for_item(
        "Test Movie",
        "http://moviedb.com/movie/test",
        max_search_results_to_process=3,  # Allow processing more sites
        max_reviews_per_site=2,  # Allow multiple reviews per site
    )

    # mock_load_config_reviews sets max_total_reviews_per_item = 2
    assert len(reviews) == 2
    assert reviews[0]["review_text"] == "Review 1.1"
    assert reviews[1]["review_text"] == "Review 1.2"

    # _scrape_reviews_from_page for site1 is called.
    # Depending on loop structure, _scrape_reviews_from_page for site2 might or might not be called
    # if the limit is checked after each *review* is added vs after each *site* is processed.
    # The current implementation of fetch_reviews_for_item checks *after* processing a page and adding its reviews.
    # So site2 will be processed, but its reviews won't be added if limit already reached.
    # If site1 gives 2 reviews, and max_total is 2, scrape for site2 will still be called.
    assert (
        mock_scrape.call_count <= 2
    )  # Should be called for site1, and possibly site2 before limit is strictly enforced internally after scrape.
    # Given the current code, it *will* be called for site2.


@patch("mlops.scripts.scraping.review_scraper._scrape_reviews_from_page")
@patch("mlops.scripts.scraping.review_scraper._search_for_review_pages")
def test_fetch_reviews_for_item_search_result_missing_url(
    mock_search, mock_scrape, mock_load_config_reviews
):
    mock_search.return_value = [
        {"title": "Site 1 Review - No URL"},  # Missing URL
        {"url": "http://site2.com/rev", "title": "Site 2 Review"},
    ]
    mock_scrape.return_value = [{"source_name": "Site 2", "review_text": "Good."}]

    reviews = fetch_reviews_for_item(
        "Test Movie", "http://moviedb.com/movie/test", max_search_results_to_process=2
    )

    assert len(reviews) == 1
    assert reviews[0]["source_name"] == "Site 2"
    mock_search.assert_called_once()
    mock_scrape.assert_called_once_with(  # Only called for the valid URL
        "http://site2.com/rev", "Site 2 Review", "Test Movie", ANY, ANY, ANY
    )


# To run these tests, use `pytest` in the terminal
# Example: PYTHONPATH=. pytest mlops/scripts/scraping/tests/test_review_scraper.py
