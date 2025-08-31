from uuid import uuid4

import pytest

from sharing.exceptions import ResourceNotFoundError
from sharing.permissions_manager import PermissionsManager
from sharing.resource_repository import AbstractResourceRepository


def test_manager_returns_none_if_no_resources(
    resource_repo: AbstractResourceRepository,
):
    manager = PermissionsManager(resource_repo)
    with pytest.raises(ResourceNotFoundError):
        manager.get_resource(f'Memory::"{uuid4()}"')
