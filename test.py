import data
import pytest

# Fixtures


@pytest.fixture
def author():
    username = "Author"
    data.create_user(username, "N/A")
    user = data.get_user_by_name(username)
    yield user
    data.delete_user(user["id"])


@pytest.fixture
def user():
    username = "Other"
    data.create_user(username, "N/A")
    user = data.get_user_by_name(username)
    yield user
    data.delete_user(user["id"])


@pytest.fixture
def snippet(author):
    id = data.create_snippet(
        "Snippet", "Snippet Code", author["id"], is_public=True
    )
    snippet = data.get_snippet(id)
    yield snippet
    data.delete_snippet(id, author["id"])


@pytest.fixture
def child_snippet(author, snippet):
    id = data.create_snippet(
        "Child Snippet",
        "Child Code",
        author["id"],
        is_public=True,
        parent_snippet_id=snippet["id"],
    )
    yield data.get_snippet(id)
    data.delete_snippet(id, author["id"])


# Tests


def test_parent_snippet_isNotNull(snippet, child_snippet):
    assert child_snippet["parent_snippet_id"] == snippet["id"]


def test_delete_parent_snippet_isNull(author, snippet, child_snippet):
    data.delete_snippet(snippet["id"], author["id"])
    child_snippet = data.get_snippet(child_snippet["id"], author["id"])
    assert data.get_snippet(snippet["id"], author["id"]) is None
    assert child_snippet["parent_snippet_id"] is None


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
