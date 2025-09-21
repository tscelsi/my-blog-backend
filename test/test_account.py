# when owner removes an editor, and editor has memory pinned
# when owner removes a reader, and reader has memory pinned
# when pin called on inacessible memory (authorisation should do this part)
from uuid import uuid4

from account_management import services
from account_management.account_repository import InMemoryAccountRepository
from test import fixtures


async def test_pin_memory_when_accessible_by_acc():
    user = fixtures.create_user()
    account = fixtures.create_account_with_user(user)
    memory_id = uuid4()
    account_repo = InMemoryAccountRepository([account])

    await services.pin_memory(user, memory_id, account_repo)
    assert len(account.memories_pinned) == 1
    await services.unpin_memory(user, memory_id, account_repo)
    assert len(account.memories_pinned) == 0
