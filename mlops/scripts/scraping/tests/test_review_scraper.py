import pytest
from unittest.mock import patch, MagicMock, call
import requests # For requests.exceptions.RequestException
import logging # To configure logger for tests if needed
import os # For integration test API key check

# Assuming review_scraper is in mlops.scripts.scraping
# This structure assumes that the 'tests' directory is at the same level as 'mlops'
# or that PYTHONPATH is configured appropriately.
# If ModuleNotFoundError occurs, the path needs adjustment based on execution context.
try:
    from mlops.scripts.scraping.review_scraper import (
        _search_for_review_pages,
        _scrape_reviews_from_page,
        fetch_reviews_for_item,
        _get_domain_name,
        review_extract_schema, 
        review_extract_prompt,
        API_KEY as SCRAPER_API_KEY # Import the API_KEY loaded by the scraper module
    )
except ModuleNotFoundError as e:
    # Attempting a common alternative for running tests within a project structure
    # where 'mlops' is a top-level directory accessible via Python's path.
    # This often happens if tests are run from the project root.
    try:
        # This assumes 'generative-ai-gallery' is the project root and is in PYTHONPATH
        from generative_ai_gallery.mlops.scripts.scraping.review_scraper import (
            _search_for_review_pages,
            _scrape_reviews_from_page,
            fetch_reviews_for_item,
            _get_domain_name,
            review_extract_schema,
            review_extract_prompt,
            API_KEY as SCRAPER_API_KEY
        )
    except ModuleNotFoundError:
        print(f"Initial ModuleNotFoundError: {e}")
        print("Alternative import also failed. Ensure your PYTHONPATH is correctly set up to find 'mlops.scripts.scraping.review_scraper'.")
        print("For example, if 'generative-ai-gallery' is your project root, export PYTHONPATH=$PYTHONPATH:/path/to/generative-ai-gallery")
        raise

# Configure logging to be quiet during tests unless specifically testing logging.
# This prevents application logs from cluttering test output.
# If you need to assert log messages, you can use mock_logger.
logging.basicConfig(level=logging.INFO) # Set to INFO to see print statements from tests
logger = logging.getLogger(__name__)

# --- Unit Tests (with mocks) ---

# Common patches for most unit tests. 
# We can apply them individually or explore pytest fixtures for these later if preferred.
COMMON_UNIT_TEST_PATCHES = [
    patch('mlops.scripts.scraping.review_scraper.API_KEY', 'test_api_key_for_scraper_tests'),
    patch('mlops.scripts.scraping.review_scraper.load_config'),
    patch('mlops.scripts.scraping.review_scraper.SESSION')
]

# Helper to apply multiple decorators
def apply_patches(patches):
    def decorator(func):
        for p in reversed(patches): # Apply patches in reverse order so arguments line up as expected
            func = p(func)
        return func
    return decorator

@apply_patches(COMMON_UNIT_TEST_PATCHES)
def test_get_domain_name(mock_session, mock_load_config): 
    assert _get_domain_name("http://www.example.com/page") == "example.com"
    assert _get_domain_name("https://sub.example.co.uk/path?q=1") == "sub.example.co.uk"
    assert _get_domain_name("ftp://example.com") == "example.com"
    assert _get_domain_name("www.nohttp.com") == "nohttp.com"
    assert _get_domain_name("bare.domain.com/path") == "bare.domain.com"
    assert _get_domain_name("http://localhost:8000") == "localhost:8000"
    assert _get_domain_name("invalid-url") == "Unknown Source"
    assert _get_domain_name("") == "Unknown Source"
    assert _get_domain_name("http://") == "Unknown Source" 
    assert _get_domain_name("...") == "Unknown Source"


@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger') 
def test_search_for_review_pages_success(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"url": "http://example.com/review1", "title": "Review 1", "markdown": "", "metadata": {}},
            {"url": "http://example.com/review2", "title": "Review 2", "markdown": "", "metadata": {}}
        ]
    }
    mock_session.post.return_value = mock_response

    results = _search_for_review_pages("Test Movie", "http://moviedetail.com/movie", search_limit=2)

    assert len(results) == 2
    assert results[0]['url'] == "http://example.com/review1"
    assert results[1]['title'] == "Review 2"
    mock_session.post.assert_called_once_with(
        "https://api.firecrawl.dev/v1/search",
        json={
            "query": "Test Movie movie reviews",
            "searchOptions": {"limit": 2},
        }
    )
    mock_scraper_logger.info.assert_any_call("Searching for reviews with query: 'Test Movie movie reviews'")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_search_for_review_pages_tv_show_query(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_session.post.return_value = mock_response

    _search_for_review_pages("Test Show", "http://details.com/tv-show/test-show", 1)
    
    mock_session.post.assert_called_once_with(
        "https://api.firecrawl.dev/v1/search",
        json={
            "query": "Test Show TV series reviews", 
            "searchOptions": {"limit": 1},
        }
    )

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_search_for_review_pages_api_error(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_session.post.side_effect = requests.exceptions.RequestException("API down")

    results = _search_for_review_pages("Test Movie", "http://moviedetail.com/movie", 2)
    assert results == []
    mock_scraper_logger.error.assert_called_once()
    assert "Request error during Firecrawl search" in mock_scraper_logger.error.call_args[0][0]

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_search_for_review_pages_no_data_or_unexpected_format(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": None} 
    mock_session.post.return_value = mock_response

    results = _search_for_review_pages("Test Movie", "http://moviedetail.com/movie", 2)
    assert results == []
    mock_scraper_logger.warning.assert_called_once()
    assert "Unexpected format or empty data" in mock_scraper_logger.warning.call_args[0][0]

    mock_scraper_logger.reset_mock() 
    mock_response.json.return_value = {} 
    results = _search_for_review_pages("Test Movie", "http://moviedetail.com/movie", 2)
    assert results == []
    mock_scraper_logger.warning.assert_called_once()


@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_scrape_reviews_from_page_success(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "llm_extraction": [
                {"reviewer_name": "Critic A", "review_text": "Great movie!", "original_score": "5/5"},
                {"review_text": "Not bad.", "reviewer_name": None, "original_score": None} 
            ]
        }
    }
    mock_session.post.return_value = mock_response

    current_review_extract_prompt = review_extract_prompt 
    current_review_extract_schema = review_extract_schema

    results = _scrape_reviews_from_page(
        "http://example.com/review1", "Review 1 Title", "Test Movie", 
        max_reviews_per_site=2,
        review_extract_prompt=current_review_extract_prompt,
        review_extract_schema=current_review_extract_schema
    )

    assert len(results) == 2
    assert results[0]['review_text'] == "Great movie!"
    assert results[0]['source_name'] == "Critic A"
    assert results[1]['source_name'] == "example.com" 

    expected_payload_prompt = current_review_extract_prompt.format(max_reviews_per_site=2)
    mock_session.post.assert_called_once_with(
        "https://api.firecrawl.dev/v1/scrape",
        json={
            "url": "http://example.com/review1",
            "extractorOptions": {
                "mode": "llm-extraction",
                "extractionPrompt": expected_payload_prompt,
                "extractionSchema": current_review_extract_schema,
            }
        }
    )
    mock_scraper_logger.info.assert_any_call("Successfully extracted 2 review items from http://example.com/review1")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_scrape_reviews_from_page_api_error(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_session.post.side_effect = requests.exceptions.RequestException("Scrape API down")

    results = _scrape_reviews_from_page("url", "title", "item", 1, "prompt", {})
    assert results == []
    mock_scraper_logger.error.assert_called_once()
    assert "Request error scraping review page" in mock_scraper_logger.error.call_args[0][0]

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_scrape_reviews_from_page_no_llm_extraction(mock_scraper_logger, mock_session, mock_load_config_global):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"llm_extraction": []}} 
    mock_session.post.return_value = mock_response
    
    results = _scrape_reviews_from_page("url", "title", "item", 1, "prompt", {})
    assert results == []
    mock_scraper_logger.warning.assert_any_call("No reviews extracted or unexpected format from url. Response: {'data': {'llm_extraction': []}}")

    mock_scraper_logger.reset_mock()
    mock_response.json.return_value = {"data": {}} 
    results = _scrape_reviews_from_page("url", "title", "item", 1, "prompt", {})
    assert results == []
    mock_scraper_logger.warning.assert_any_call("No reviews extracted or unexpected format from url. Response: {'data': {}}")
    
    mock_scraper_logger.reset_mock()
    mock_response.json.return_value = {"data": {"llm_extraction": [{"invalid": "data"}]}} 
    results = _scrape_reviews_from_page("url", "title", "item", 1, "prompt", {})
    assert results == []
    mock_scraper_logger.warning.assert_any_call("Skipping invalid review data from url: {'invalid': 'data'}")


@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper._search_for_review_pages')
@patch('mlops.scripts.scraping.review_scraper._scrape_reviews_from_page')
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_fetch_reviews_for_item_success(mock_scraper_logger, mock_scrape, mock_search, mock_session_global, mock_load_config_global):
    config_values = {
        ("scraping", {}): {"review_search_limit": 5, "max_total_reviews_per_item": 3},
        "review_search_limit": 5,
        "max_total_reviews_per_item": 3,
    }
    mock_load_config_global.return_value.get.side_effect = lambda k1, k2_default=None: \
        config_values.get(k1, {}).get(k2_default) if isinstance(k1, str) and isinstance(config_values.get(k1), dict) \
        else config_values.get((k1, k2_default), k2_default if k2_default is not None else 5)


    mock_search.return_value = [
        {"url": "http://site1.com/rev", "title": "Review Site 1"},
        {"url": "http://site2.com/rev", "title": "Review Site 2"}
    ]
    mock_scrape.side_effect = [
        [{"source_name": "Critic A", "review_text": "Amazing!", "review_url": "http://site1.com/rev"}],
        [{"source_name": "Critic B", "review_text": "Good.", "review_url": "http://site2.com/rev"}]
    ]

    results = fetch_reviews_for_item(
        "Test Movie", "http://details.com", 
        max_search_results_to_process=2, 
        max_reviews_per_site=1
    )

    assert len(results) == 2
    assert results[0]['source_name'] == "Critic A"
    assert results[1]['review_text'] == "Good."
    
    mock_search.assert_called_once_with("Test Movie", "http://details.com", 5) 
    
    expected_scrape_calls = [
        call("http://site1.com/rev", "Review Site 1", "Test Movie", 1, review_extract_prompt, review_extract_schema),
        call("http://site2.com/rev", "Review Site 2", "Test Movie", 1, review_extract_prompt, review_extract_schema)
    ]
    mock_scrape.assert_has_calls(expected_scrape_calls)
    assert mock_scrape.call_count == 2
    mock_scraper_logger.info.assert_any_call("Successfully collected 2 reviews for 'Test Movie'.")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper._search_for_review_pages')
@patch('mlops.scripts.scraping.review_scraper._scrape_reviews_from_page')
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_fetch_reviews_for_item_no_search_results(mock_scraper_logger, mock_scrape, mock_search, mock_session_global, mock_load_config_global):
    mock_load_config_global.return_value.get.return_value = 5 
    mock_search.return_value = []

    results = fetch_reviews_for_item("Test Movie", "http://details.com")
    
    assert results == []
    mock_search.assert_called_once()
    mock_scrape.assert_not_called()
    mock_scraper_logger.info.assert_any_call("No search results found for review query for 'Test Movie'")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper._search_for_review_pages')
@patch('mlops.scripts.scraping.review_scraper._scrape_reviews_from_page')
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_fetch_reviews_for_item_search_but_no_scrape_results(mock_scraper_logger, mock_scrape, mock_search, mock_session_global, mock_load_config_global):
    mock_load_config_global.return_value.get.return_value = 5 
    mock_search.return_value = [{"url": "http://site1.com/rev", "title": "Review Site 1"}]
    mock_scrape.return_value = [] 

    results = fetch_reviews_for_item("Test Movie", "http://details.com", max_search_results_to_process=1)
    
    assert results == []
    mock_search.assert_called_once()
    mock_scrape.assert_called_once()
    mock_scraper_logger.info.assert_any_call("No reviews ultimately collected for 'Test Movie'.")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper._search_for_review_pages')
@patch('mlops.scripts.scraping.review_scraper._scrape_reviews_from_page')
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_fetch_reviews_for_item_max_total_reviews_limit_hit(mock_scraper_logger, mock_scrape, mock_search, mock_session_global, mock_load_config_global):
    config_values = {
        ("scraping", {}): {"review_search_limit": 5, "max_total_reviews_per_item": 1}, 
        "review_search_limit": 5,
        "max_total_reviews_per_item": 1,
    }
    mock_load_config_global.return_value.get.side_effect = lambda k1, k2_default=None: \
        config_values.get(k1, {}).get(k2_default) if isinstance(k1, str) and isinstance(config_values.get(k1), dict) \
        else config_values.get((k1, k2_default), k2_default if k2_default is not None else (5 if k1 == "review_search_limit" else 1))


    mock_search.return_value = [
        {"url": "http://site1.com/rev", "title": "Review Site 1"},
        {"url": "http://site2.com/rev", "title": "Review Site 2"} 
    ]
    mock_scrape.return_value = [{"source_name": "Critic A", "review_text": "Amazing!", "review_url": "http://site1.com/rev"}]
    
    results = fetch_reviews_for_item(
        "Test Movie", "http://details.com", 
        max_search_results_to_process=2, 
        max_reviews_per_site=1 
    )

    assert len(results) == 1 
    assert results[0]['source_name'] == "Critic A"
    
    mock_search.assert_called_once()
    mock_scrape.assert_called_once() 
    mock_scraper_logger.info.assert_any_call("Reached max total reviews (1) for Test Movie.")
    mock_scraper_logger.info.assert_any_call("Successfully collected 1 reviews for 'Test Movie'.")

@apply_patches(COMMON_UNIT_TEST_PATCHES)
@patch('mlops.scripts.scraping.review_scraper._search_for_review_pages')
@patch('mlops.scripts.scraping.review_scraper._scrape_reviews_from_page')
@patch('mlops.scripts.scraping.review_scraper.logger')
def test_fetch_reviews_for_item_max_reviews_per_site_respected_in_scrape_call(mock_scraper_logger, mock_scrape, mock_search, mock_session_global, mock_load_config_global):
    config_values = {
        ("scraping", {}): {"review_search_limit": 5, "max_total_reviews_per_item": 10}, 
        "review_search_limit": 5,
        "max_total_reviews_per_item": 10,
    }
    mock_load_config_global.return_value.get.side_effect = lambda k1, k2_default=None: \
        config_values.get(k1, {}).get(k2_default) if isinstance(k1, str) and isinstance(config_values.get(k1), dict) \
        else config_values.get((k1, k2_default), k2_default if k2_default is not None else 10)

    mock_search.return_value = [{"url": "http://site1.com/rev", "title": "Review Site 1"}]
    
    mock_scrape.return_value = [
        {"source_name": "Critic A", "review_text": "Review 1/Site1", "review_url": "http://site1.com/rev"}
    ]

    fetch_reviews_for_item(
        "Test Movie", "http://details.com", 
        max_search_results_to_process=1, 
        max_reviews_per_site=1 
    )
    
    mock_scrape.assert_called_once_with(
        "http://site1.com/rev", "Review Site 1", "Test Movie", 
        1, 
        review_extract_prompt, review_extract_schema
    )

# --- Integration Test (makes real API calls) ---

def test_fetch_reviews_for_item_integration():
    # SCRAPER_API_KEY is imported from review_scraper module where it's loaded by load_env_vars()
    if not SCRAPER_API_KEY: # or os.getenv("FIRECRAWL_API_KEY")
        pytest.skip("FIRECRAWL_API_KEY not set in environment (checked via review_scraper.API_KEY), skipping integration test.", allow_module_level=True)

    item_title = "Inception"
    item_detail_url = "https://www.justwatch.com/us/movie/inception" # Contextual

    logger.info(f"Running integration test for '{item_title}'. This will make live API calls.")
    
    reviews = []
    try:
        reviews = fetch_reviews_for_item(
            item_title=item_title,
            item_detail_url=item_detail_url,
            max_search_results_to_process=1, 
            max_reviews_per_site=1
        )
    except Exception as e:
        pytest.fail(f"fetch_reviews_for_item raised an exception during integration test: {e}")

    assert isinstance(reviews, list), "fetch_reviews_for_item should return a list."

    if not reviews:
        logger.warning(f"Warning: No reviews found for '{item_title}' during integration test. This might be okay if the API returned no results, or if the first search result had no extractable reviews.")
    else:
        logger.info(f"Found {len(reviews)} review(s) for '{item_title}'.")
        for review in reviews:
            assert isinstance(review, dict), "Each review should be a dictionary."
            assert "source_name" in review
            assert "review_text" in review
            assert "review_url" in review
            assert review.get("source_name"), "Source name should not be empty if present." # Source name can be from domain
            assert review.get("review_text"), "Review text should not be empty."
            assert review.get("review_url"), "Review URL should not be empty."
            logger.info(f"  Review from {review['source_name']}: {review['review_text'][:100]}...")
