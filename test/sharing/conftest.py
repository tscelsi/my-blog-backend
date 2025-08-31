import pytest

from sharing.resource_repository import CedarResourceInMemoryRepository


@pytest.fixture
def resource_repo():
    return CedarResourceInMemoryRepository()
