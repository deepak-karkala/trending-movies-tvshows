"""Unit tests for JustWatch scraper."""

import logging
import os
import tempfile
from unittest.mock import MagicMock

from mlops.scripts.scraping.justwatch_scraper import JustWatchScraper

# Ensure logs are captured during tests
logging.basicConfig(level=logging.INFO)


def test_justwatch_scraper():
    """Test the JustWatch scraper with test mode enabled."""
    api_key = "test-api-key"  # We'll mock the API calls

    # Create scraper instance with test mode
    scraper = JustWatchScraper(api_key=api_key, test_mode=True)

    # Mock the session
    mock_session = MagicMock()
    scraper.session = mock_session  # Replace the session directly

    # Configure mock response for new releases
    mock_new_releases_response = MagicMock()
    mock_new_releases_response.json.return_value = {
        "success": True,
        "data": {
            "json": {
                "items": [
                    {
                        "title": "Test Movie 1",
                        "contentType": "Movie",
                        "streamingPlatforms": ["Netflix"],
                        "releaseDate": "2024",
                        "detailUrl": "/us/movie/test-movie-1",
                        "genres": ["Action"],
                    },
                    {
                        "title": "Test Show 2",
                        "contentType": "TV Show",
                        "streamingPlatforms": ["Prime Video"],
                        "releaseDate": "2024",
                        "detailUrl": "/us/show/test-show-2",
                        "genres": ["Drama"],
                    },
                ]
            }
        },
    }

    # Configure mock response for first item's detailed content
    mock_detail_response_1 = MagicMock()
    mock_detail_response_1.json.return_value = {
        "success": True,
        "data": {
            "json": {
                "title": "Test Movie 1",
                "contentType": "Movie",
                "streamingPlatforms": ["Netflix"],
                "releaseDate": "2024",
                "genres": ["Action", "Adventure"],
                "imdbRating": "7.5",
                "rottenTomatoesRating": "85%",
                "synopsis": "A test movie synopsis",
                "cast": [{"name": "Actor 1", "character": "Character 1"}],
                "directors": ["Director 1"],
                "duration": "2h 30min",
                "maturityRating": "PG-13",
                "language": "English",
                "country": "USA",
                "yearReleased": "2024",
            }
        },
    }

    # Configure mock response for second item's detailed content
    mock_detail_response_2 = MagicMock()
    mock_detail_response_2.json.return_value = {
        "success": True,
        "data": {
            "json": {
                "title": "Test Show 2",
                "contentType": "TV Show",
                "streamingPlatforms": ["Prime Video"],
                "releaseDate": "2024",
                "genres": ["Drama", "Thriller"],
                "imdbRating": "8.0",
                "rottenTomatoesRating": "90%",
                "synopsis": "A test show synopsis",
                "cast": [{"name": "Actor 2", "character": "Character 2"}],
                "directors": ["Director 2"],
                "duration": "45min",
                "maturityRating": "TV-MA",
                "language": "English",
                "country": "USA",
                "yearReleased": "2024",
            }
        },
    }

    # Set up the post method to return our mock responses
    mock_session.post.side_effect = [
        mock_new_releases_response,  # First call for new releases
        mock_detail_response_1,  # Second call for first item's details
        mock_detail_response_2,  # Third call for second item's details
    ]

    # Get new releases
    releases = scraper.get_new_releases()

    # Verify the results
    assert len(releases) == 2, "Test mode should return exactly 2 items"
    assert releases[0]["title"] == "Test Movie 1"
    assert releases[1]["title"] == "Test Show 2"
    assert releases[0]["contentType"] == "Movie"
    assert releases[1]["contentType"] == "TV Show"
    assert "genres" in releases[0]
    assert "genres" in releases[1]
    assert isinstance(releases[0]["streamingPlatforms"], list)
    assert isinstance(releases[1]["streamingPlatforms"], list)
    assert releases[0]["synopsis"] == "A test movie synopsis"
    assert releases[1]["synopsis"] == "A test show synopsis"

    # Verify API calls
    assert mock_session.post.call_count >= 2

    # Test data saving
    with tempfile.TemporaryDirectory() as tmp_dir:
        scraper.save_data(releases, output_dir=tmp_dir)
        # Verify files were created
        files = os.listdir(tmp_dir)
        assert any(f.endswith(".json") for f in files)
        assert any(f.endswith(".csv") for f in files)


# Removed if __name__ == '__main__': unittest.main() as pytest handles test discovery
