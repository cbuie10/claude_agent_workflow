"""Tests for the extract task."""

from unittest.mock import MagicMock, patch

from pipeline.tasks.extract import extract_earthquake_data


def test_extract_returns_dict():
    """extract_earthquake_data should return parsed JSON as a dict."""
    # Create a fake HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "test1",
                "properties": {"mag": 2.5},
                "geometry": {"coordinates": [-122, 37, 10]},
            }
        ],
    }
    mock_response.raise_for_status = MagicMock()

    # Replace httpx.get with our fake — so no real HTTP call is made
    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response):
        result = extract_earthquake_data.fn("https://fake-url.com")

    assert isinstance(result, dict)
    assert "features" in result
    assert len(result["features"]) == 1


def test_extract_calls_correct_url():
    """Verify the task passes the URL through to httpx.get."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response) as mock_get:
        extract_earthquake_data.fn("https://my-custom-url.com/data")

    mock_get.assert_called_once_with("https://my-custom-url.com/data", timeout=30.0)
