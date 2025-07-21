import pytest


@pytest.fixture
def sample_data():
    return {"username": "alice", "password": "secret"}
