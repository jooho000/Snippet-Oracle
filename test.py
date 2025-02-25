import data
import mock_data
import pytest

# Fixtures


@pytest.fixture
def user():
    username = mock_data.username()
    data.create_user(username, "N/A")
    user = data.get_user_by_name(username)
    yield user
    data.delete_user(user["id"])


@pytest.fixture
def snippet(user):
    id = data.create_snippet(
        "Test Snippet", mock_data.code(), user["id"], is_public=True
    )
    snippet = data.get_snippet(id)
    yield snippet
    data.delete_snippet(id, user["id"])


@pytest.fixture
def parent_child(user):
    parent_id = data.create_snippet(
        "Parent Snippet", mock_data.code(), user["id"], is_public=True
    )
    child_id = data.create_snippet(
        "Child Snippet",
        mock_data.code(),
        user["id"],
        is_public=True,
        parent_snippet_id=parent_id,
    )
    parent = data.get_snippet(parent_id)
    child = data.get_snippet(child_id)
    yield (user, parent, child)
    data.delete_snippet(parent_id, user["id"])
    data.delete_snippet(child_id, user["id"])


# Tests


def test_parent_snippet_isNotNull(parent_child):
    _, parent, child = parent_child
    assert child["parent_snippet_id"] == parent["id"]


def test_delete_parent_snippet_isNull(parent_child):
    user, parent, child = parent_child
    data.delete_snippet(parent["id"], user["id"])
    child1 = data.get_snippet(child["id"], user["id"])
    assert data.get_snippet(parent["id"], user["id"]) is None
    assert child1["parent_snippet_id"] is None


def test_single_like(user, snippet):
    initial_likes = data.get_likes(snippet["id"])
    assert not data.is_liked(snippet["id"], user["id"])
    assert data.add_like(snippet["id"], user["id"])
    assert data.is_liked(snippet["id"], user["id"])
    new_likes = data.get_likes(snippet["id"])
    assert new_likes == initial_likes + 1


def test_duplicate_likes(user, snippet):
    initial_likes = data.get_likes(snippet["id"])
    assert not data.is_liked(snippet["id"], user["id"])

    assert data.add_like(snippet["id"], user["id"])
    assert data.is_liked(snippet["id"], user["id"])

    assert not data.add_like(snippet["id"], user["id"])
    assert data.is_liked(snippet["id"], user["id"])
    assert data.get_likes(snippet["id"]) == initial_likes + 1


def test_remove_like(user, snippet):
    initial_likes = data.get_likes(snippet["id"])

    assert data.add_like(snippet["id"], user["id"])
    assert data.get_likes(snippet["id"]) == initial_likes + 1

    for _ in range(2):
        data.remove_like(snippet["id"], user["id"])
        assert not data.is_liked(snippet["id"], user["id"])
        assert data.get_likes(snippet["id"]) == initial_likes
