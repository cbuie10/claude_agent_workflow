"""Shared test fixtures for all test modules."""

import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """Use a temporary Prefect database for the entire test session.

    autouse=True means every test gets this automatically.
    scope="session" means it's created once and reused across all tests.
    """
    with prefect_test_harness():
        yield
