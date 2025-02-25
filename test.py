import data
import pytest

# Fixtures

@pytest.fixture
def db():
    db = data.Data()
    db.generate_embeddings = False
    yield db
    db.close()


@pytest.fixture
def author(db):
    username = "Author"
    db.create_user(username, "N/A")
    user = db.get_user_by_name(username)
    yield user
    db.delete_user(user["id"])


@pytest.fixture
def user(db):
    username = "Other"
    db.create_user(username, "N/A")
    user = db.get_user_by_name(username)
    yield user
    db.delete_user(user["id"])


@pytest.fixture
def snippet(db, author):
    id = db.create_snippet(
        "Snippet", "Snippet Code", author["id"], is_public=True
    )
    snippet = db.get_snippet(id)
    yield snippet
    db.delete_snippet(id, author["id"])


@pytest.fixture
def child_snippet(db, author, snippet):
    id = db.create_snippet(
        "Child Snippet",
        "Child Code",
        author["id"],
        is_public=True,
        parent_snippet_id=snippet["id"],
    )
    yield db.get_snippet(id)
    db.delete_snippet(id, author["id"])


# Tests


def test_parent_snippet_isNotNull(snippet, child_snippet):
    assert child_snippet["parent_snippet_id"] == snippet["id"]


def test_delete_parent_snippet_isNull(db, author, snippet, child_snippet):
    db.delete_snippet(snippet["id"], author["id"])
    child_snippet = db.get_snippet(child_snippet["id"], author["id"])
    assert db.get_snippet(snippet["id"], author["id"]) is None
    assert child_snippet["parent_snippet_id"] is None


def test_single_like(db, user, snippet):
    initial_likes = db.get_likes(snippet["id"])
    assert not db.is_liked(snippet["id"], user["id"])
    assert db.add_like(snippet["id"], user["id"])
    assert db.is_liked(snippet["id"], user["id"])
    new_likes = db.get_likes(snippet["id"])
    assert new_likes == initial_likes + 1


def test_duplicate_likes(db, user, snippet):
    initial_likes = db.get_likes(snippet["id"])
    assert not db.is_liked(snippet["id"], user["id"])

    assert db.add_like(snippet["id"], user["id"])
    assert db.is_liked(snippet["id"], user["id"])

    assert not db.add_like(snippet["id"], user["id"])
    assert db.is_liked(snippet["id"], user["id"])
    assert db.get_likes(snippet["id"]) == initial_likes + 1


def test_remove_like(db, user, snippet):
    initial_likes = db.get_likes(snippet["id"])

    assert db.add_like(snippet["id"], user["id"])
    assert db.get_likes(snippet["id"]) == initial_likes + 1

    for _ in range(2):
        db.remove_like(snippet["id"], user["id"])
        assert not db.is_liked(snippet["id"], user["id"])
        assert db.get_likes(snippet["id"]) == initial_likes
