"""Tests for the extract task."""

from unittest.mock import MagicMock, patch

from pipeline.tasks.extract import (
    extract_earthquake_data,
    extract_occ_wells_data,
    extract_weather_data,
)


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


def test_extract_weather_returns_dict():
    """extract_weather_data should return parsed JSON as a dict."""
    # Create a fake HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "latitude": 40.71,
        "longitude": -73.99,
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
            "temperature_2m": [32.5, 31.8],
            "relative_humidity_2m": [65, 68],
            "wind_speed_10m": [8.2, 7.5],
        },
    }
    mock_response.raise_for_status = MagicMock()

    # Replace httpx.get with our fake — so no real HTTP call is made
    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response):
        result = extract_weather_data.fn("https://fake-url.com")

    assert isinstance(result, dict)
    assert "hourly" in result
    assert "latitude" in result
    assert result["latitude"] == 40.71


def test_extract_weather_calls_correct_url():
    """Verify the task passes the URL through to httpx.get."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"hourly": {}}
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response) as mock_get:
        extract_weather_data.fn("https://api.open-meteo.com/v1/forecast")

    mock_get.assert_called_once_with("https://api.open-meteo.com/v1/forecast", timeout=30.0)


def test_extract_occ_wells_returns_csv_text():
    """extract_occ_wells_data should return CSV text as a string."""
    # Create a fake HTTP response with CSV text
    mock_response = MagicMock()
    mock_response.text = "API,WELL_NAME,WELL_NUM\n3500100002,PENN MUTUAL LIFE,#1\n"
    mock_response.raise_for_status = MagicMock()

    # Replace httpx.get with our fake — so no real HTTP call is made
    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response):
        result = extract_occ_wells_data.fn("https://fake-url.com/wells.csv")

    assert isinstance(result, str)
    assert "API,WELL_NAME,WELL_NUM" in result
    assert "3500100002" in result


def test_extract_occ_wells_calls_correct_url():
    """Verify the task passes the URL through to httpx.get with extended timeout."""
    mock_response = MagicMock()
    mock_response.text = "API\n3500100002\n"
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.tasks.extract.httpx.get", return_value=mock_response) as mock_get:
        extract_occ_wells_data.fn("https://oklahoma.gov/occ/wells.csv")

    mock_get.assert_called_once_with("https://oklahoma.gov/occ/wells.csv", timeout=120.0)
