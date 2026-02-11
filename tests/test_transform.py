"""Tests for the transform task."""

from pipeline.tasks.transform import transform_earthquake_data

# Sample GeoJSON that mimics real USGS data
SAMPLE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "id": "us7000abc1",
            "properties": {
                "mag": 4.5,
                "place": "10km NW of Somewhere",
                "time": 1700000000000,  # epoch milliseconds
                "magType": "ml",
                "type": "earthquake",
                "title": "M 4.5 - 10km NW of Somewhere",
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000abc1",
                "felt": 12,
                "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-122.5, 37.8, 8.2]},
        },
        {
            "id": "us7000abc2",
            "properties": {
                "mag": 0.5,
                "place": "Tiny quake",
                "time": 1700000100000,
                "magType": "ml",
                "type": "earthquake",
                "title": "M 0.5",
                "url": "https://example.com",
                "felt": None,
                "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-118.0, 34.0, 5.0]},
        },
    ],
}


def test_transform_returns_list():
    """Should return a list of row dicts."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    assert isinstance(result, list)
    assert len(result) == 2


def test_transform_flattens_fields():
    """Should correctly flatten nested GeoJSON into flat row dicts."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    row = result[0]
    assert row["id"] == "us7000abc1"
    assert row["magnitude"] == 4.5
    assert row["place"] == "10km NW of Somewhere"
    assert row["longitude"] == -122.5
    assert row["latitude"] == 37.8
    assert row["depth_km"] == 8.2
    assert row["magnitude_type"] == "ml"
    assert row["felt"] == 12


def test_transform_converts_timestamp():
    """Should convert epoch milliseconds to a datetime."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    occurred_at = result[0]["occurred_at"]
    assert occurred_at.year == 2023
    assert occurred_at.month == 11


def test_transform_filters_by_min_magnitude():
    """Should exclude events below min_magnitude."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON, min_magnitude=2.0)
    assert len(result) == 1
    assert result[0]["id"] == "us7000abc1"


def test_transform_handles_empty_features():
    """Should return an empty list when there are no features."""
    result = transform_earthquake_data.fn({"features": []})
    assert result == []


def test_transform_skips_null_magnitude():
    """Should skip features where magnitude is None."""
    data = {
        "features": [
            {
                "id": "null_mag",
                "properties": {"mag": None, "place": "Unknown", "time": 1700000000000},
                "geometry": {"coordinates": [0, 0, 0]},
            }
        ]
    }
    result = transform_earthquake_data.fn(data)
    assert result == []
