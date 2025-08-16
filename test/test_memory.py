from uuid import uuid4

import pytest

from entities.fragments.file import File
from entities.memory import Memory, MemorySplitError
from test import fixtures


def test_memory_eq():
    m = Memory(
        title="test",
        owner=fixtures.USER_ID,
        created_by=fixtures.USER_ID,
        fragments=[fixtures.create_file_fragment()],
    )
    m2 = Memory(
        title="test",
        owner=fixtures.USER_ID,
        created_by=fixtures.USER_ID,
        fragments=[fixtures.create_file_fragment()],
    )
    assert m != m2


def test_memory_hash():
    m = Memory(
        title="test",
        owner=fixtures.USER_ID,
        created_by=fixtures.USER_ID,
        fragments=[fixtures.create_file_fragment()],
    )
    m2 = Memory(
        title="test",
        owner=fixtures.USER_ID,
        created_by=fixtures.USER_ID,
        fragments=[fixtures.create_file_fragment()],
    )
    assert hash(m) == hash(m)
    assert hash(m) != hash(m2)


def test_memory_merge():
    m1 = fixtures.create_memory()
    m2 = fixtures.create_memory(fragment_name="A Test File 2")
    m1.merge(m2)
    assert len(m1.fragments) == 2
    assert isinstance(m1.fragments[0], File)
    assert isinstance(m1.fragments[1], File)
    assert m1.fragments[0].name == "A Test File"
    assert m1.fragments[1].name == "A Test File 2"


def test_memory_split():
    m = fixtures.create_memory()
    f1 = fixtures.create_file_fragment(id=uuid4(), name="A Test File")
    f2 = fixtures.create_file_fragment(id=uuid4(), name="A Test File 2")
    m.fragments = [f1, f2]
    old_m, split_m = m.split([f1.id])
    assert len(old_m.fragments) == 1
    assert len(split_m.fragments) == 1
    assert isinstance(old_m.fragments[0], File)
    assert isinstance(split_m.fragments[0], File)
    assert old_m.fragments[0].name == "A Test File 2"
    assert split_m.fragments[0].name == "A Test File"


def test_split_memory_when_id_not_exists():
    """If no fragments exist, raise ValueError."""
    m = fixtures.create_memory()
    f1 = fixtures.create_file_fragment(id=uuid4(), name="A Test File")
    f2 = fixtures.create_file_fragment(id=uuid4(), name="A Test File 2")
    m.fragments = [f1, f2]
    with pytest.raises(MemorySplitError):
        m.split([uuid4()])


def test_split_memory_when_some_exists():
    """Ignores the fragments that don't exist."""
    m = fixtures.create_memory()
    f1 = fixtures.create_file_fragment(id=uuid4(), name="A Test File")
    f2 = fixtures.create_file_fragment(id=uuid4(), name="A Test File 2")
    m.fragments = [f1, f2]
    old, new = m.split([uuid4(), f1.id])
    assert len(old.fragments) == 1
    assert len(new.fragments) == 1


def test_split_memory_when_old_becomes_empty():
    """If we're splitting the entire old memory, then we should raise as it
    would be a copy."""
    m = fixtures.create_memory()
    f1 = fixtures.create_file_fragment(id=uuid4(), name="A Test File")
    f2 = fixtures.create_file_fragment(id=uuid4(), name="A Test File 2")
    m.fragments = [f1, f2]
    with pytest.raises(MemorySplitError):
        m.split([f1.id, f2.id])
