import data
import pytest


@pytest.fixture
def parent_child():
    data.create_user("test_user", "N/A")
    temp_user = data.get_user_by_name("test_user")
    parent = data.create_snippet("Test1", "1234", temp_user["id"], is_public=True)
    child = data.create_snippet(
        "Test2", "1234", temp_user["id"], is_public=True, parent_id=parent
    )
    parent_Data = data.get_snippet(parent)
    child_Data = data.get_snippet(child)
    yield (temp_user, parent_Data, child_Data)
    data.delete_snippet(parent, temp_user["id"])
    data.delete_snippet(child, temp_user["id"])
    data.delete_user(temp_user["id"])


def test_parent_snippet_isNotNull(parent_child):
    user, parent, child = parent_child
    assert child["parent_snippet_id"] == parent["id"]


def test_delete_parent_snippet_isNull(parent_child):
    user, parent, child = parent_child
    data.delete_snippet(parent["id"], user["id"])
    child1 = data.get_snippet(child["id"], user["id"])
    assert data.get_snippet(parent["id"], user["id"]) is None
    assert child1["parent_snippet_id"] is None
