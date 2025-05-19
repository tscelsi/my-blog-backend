from test.fixtures import create_file_fragment, create_text_fragment
from uuid import uuid4

import pytest
from pydantic import ValidationError

from fragments.base import FragmentType
from fragments.file import Audio, File, FileFragmentFactory, FileFragmentStatus


def test_fragment_init():
    f = create_file_fragment(name="a test file")
    assert isinstance(f, File)
    assert f.status == FileFragmentStatus.UPLOADING


def test_file_fragment_eq():
    f = create_file_fragment(id=uuid4(), name="a test file")
    f2 = create_file_fragment(id=uuid4(), name="a different test file")
    assert f == f
    assert f != f2


def test_text_fragment_eq():
    f = create_text_fragment(id=uuid4(), content="a test text")
    f2 = create_text_fragment(id=uuid4(), content="a different test text")
    assert f == f
    assert f != f2


def test_fragment_hash():
    f = create_file_fragment(id=uuid4(), name="a test file")
    f2 = create_file_fragment(id=uuid4(), name="a different test file")
    assert hash(f) == hash(f)
    assert hash(f) != hash(f2)


def test_fragment_update_to_error_state():
    f = create_file_fragment()
    f.set_upload_progress_error()
    assert f.status == FileFragmentStatus.ERROR
    assert f.upload_progress == 0
    f.set_upload_succeeded()
    assert f.upload_progress == 100


def test_fragment_factory():
    f1 = FileFragmentFactory.create_file_fragment(
        name="a test file", type=FragmentType.AUDIO
    )
    assert f1.type == FragmentType.AUDIO
    assert isinstance(f1, File)
    assert isinstance(f1, Audio)
    f2 = FileFragmentFactory.create_file_fragment(
        name="a test file", type=FragmentType.FILE
    )
    assert f2.type == FragmentType.FILE
    assert isinstance(f2, File)
    with pytest.raises(ValidationError):
        f2.type = FragmentType.AUDIO  # can't edit frozen field
