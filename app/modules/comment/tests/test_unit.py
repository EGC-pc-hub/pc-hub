import pytest

from app import db
from app.modules.auth.models import User
from app.modules.comment.services import CommentService
from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.profile.models import UserProfile

comment_service = CommentService()


@pytest.fixture(scope="module")
def module_client(test_client):
    """
    Extiende el fixture base `test_client` con datos específicos del módulo (usuarios y perfiles).
    """
    test_client.application.config["ENABLE_2FA"] = False
    user_test1 = User(email="user1@example.com", password="test1234")
    db.session.add(user_test1)
    db.session.commit()
    user_test2 = User(email="user2@example.com", password="test1234")
    db.session.add(user_test2)
    db.session.commit()
    profile1 = UserProfile(user_id=user_test1.id, name="Name1", surname="Surname1")
    db.session.add(profile1)
    db.session.commit()
    profile2 = UserProfile(user_id=user_test2.id, name="Name2", surname="Surname2")
    db.session.add(profile2)
    db.session.commit()
    test_client.test_user1_id = user_test1.id
    test_client.test_user2_id = user_test2.id
    test_client.test_user1_email = user_test1.email
    test_client.test_user2_email = user_test2.email
    yield test_client


@pytest.fixture(scope="module")
def test_dataset(module_client):
    """
    Crea un dataset para pruebas y retorna su id.
    """
    user_id = getattr(module_client, "test_user2_id", None)
    assert user_id is not None, "Test user2 id not found; fixture did not create it."
    ds_meta = DSMetaData(
        title="Test Dataset",
        description="A dataset created for tests",
        publication_type=PublicationType.NONE,
        tags="test",
    )
    db.session.add(ds_meta)
    db.session.commit()
    dataset = DataSet(ds_meta_data_id=ds_meta.id, user_id=user_id)
    db.session.add(dataset)
    db.session.commit()
    return dataset.id


def test_sample_assertion(test_client):
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_create_comment_dataset(module_client, test_dataset):
    login_response = login(module_client, module_client.test_user2_email, "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."
    dataset_id = test_dataset
    comment_data = {
        "content": "This is a test comment.",
        "dataset_id": dataset_id,
    }
    response = module_client.post(f"/comment/dataset/{dataset_id}/create", json=comment_data)
    assert response.status_code == 201, "Comment creation failed."
    resp_json = response.json
    assert resp_json.get("comment", {}).get("content") == comment_data["content"], "Comment content does not match."


def test_reply_to_comment(module_client, test_dataset):
    login_response = login(module_client, module_client.test_user1_email, "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."
    dataset_id = test_dataset
    parent_comment_data = {
        "content": "This is a parent comment.",
        "dataset_id": dataset_id,
    }
    parent_response = module_client.post(f"/comment/dataset/{dataset_id}/create", json=parent_comment_data)
    assert parent_response.status_code == 201, "Parent comment creation failed."
    parent_comment_id = parent_response.json.get("comment", {}).get("id")
    reply_data = {"content": "This is a reply to the parent comment."}
    reply_response = module_client.post(f"/comment/parent/{parent_comment_id}/reply", json=reply_data)
    assert reply_response.status_code == 201, "Reply creation failed."
    resp_json = reply_response.json
    assert resp_json.get("comment", {}).get("content") == reply_data["content"], "Reply content does not match."


def test_get_comments_by_dataset(module_client, test_dataset):
    dataset_id = test_dataset
    comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="dataset comment 1",
    )
    comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="dataset comment 2",
    )
    comments = comment_service.get_comments_by_dataset(dataset_id) or []
    contents = [c.content for c in comments]
    assert any("dataset comment 1" == c for c in contents), "dataset comment 1 not found"
    assert any("dataset comment 2" == c for c in contents), "dataset comment 2 not found"


def test_get_replies_to_comment(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="parent comment",
    )
    comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=parent.id,
        content="reply one",
    )
    comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=parent.id,
        content="reply two",
    )
    replies = comment_service.get_comments_by_parent(parent.id) or []
    reply_contents = [r.content for r in replies]
    assert "reply one" in reply_contents
    assert "reply two" in reply_contents


def test_hidden_parent_replies_for_non_owners(module_client, test_dataset, test_client):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="to be hidden",
    )
    comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=parent.id,
        content="child reply",
    )
    comment_service.update(parent.id, visible=False)
    logout(test_client)
    response = test_client.get(f"/comment/parent/{parent.id}")
    assert response.status_code == 403, f"Expected 403 when accessing hidden parent replies, got {response.status_code}"


def test_cannot_reply_hidden_parent(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="will be hidden",
    )
    comment_service.update(parent.id, visible=False)
    login_response = login(module_client, module_client.test_user2_email, "test1234")
    assert login_response.status_code == 200
    reply_data = {"content": "attempt reply"}
    reply_response = module_client.post(f"/comment/parent/{parent.id}/reply", json=reply_data)
    assert (
        reply_response.status_code == 403
    ), f"Expected 403 when replying to hidden parent, got {reply_response.status_code}"


def test_owner_can_hide_and_unhide_comment(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="to toggle",
    )
    login_response = login(module_client, module_client.test_user2_email, "test1234")
    assert login_response.status_code == 200
    hide_resp = module_client.post(f"/dataset/comment/{parent.id}/hide")
    assert hide_resp.status_code == 200
    assert hide_resp.json.get("visible") is False
    refreshed = comment_service.get_by_id(parent.id)
    assert getattr(refreshed, "visible", True) is False
    unhide_resp = module_client.post(f"/dataset/comment/{parent.id}/hide")
    assert unhide_resp.status_code == 200
    assert unhide_resp.json.get("visible") is True


def test_non_owner_cannot_toggle_visibility(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="owner only toggle",
    )
    logout(module_client)
    login_response = login(module_client, module_client.test_user1_email, "test1234")
    assert login_response.status_code == 200
    resp = module_client.post(f"/dataset/comment/{parent.id}/hide")
    assert resp.status_code == 403, f"Expected 403 for non-owner toggle, got {resp.status_code}"


def test_owner_can_delete_comment(module_client, test_dataset):
    dataset_id = test_dataset
    comment = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="to delete",
    )
    logout(module_client)
    login_response = login(module_client, module_client.test_user2_email, "test1234")
    assert login_response.status_code == 200
    del_resp = module_client.post(f"/dataset/comment/{comment.id}/delete")
    assert del_resp.status_code == 200
    assert del_resp.json.get("deleted") is True
    assert comment_service.get_by_id(comment.id) is None


def test_non_owner_cannot_delete_comment(module_client, test_dataset):
    dataset_id = test_dataset
    comment = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="owner only delete",
    )
    logout(module_client)
    login_response = login(module_client, module_client.test_user1_email, "test1234")
    assert login_response.status_code == 200
    resp = module_client.post(f"/dataset/comment/{comment.id}/delete")
    assert resp.status_code == 403, f"Expected 403 for non-owner delete, got {resp.status_code}"


def test_routes_and_edge_cases(module_client, test_dataset, test_client, monkeypatch):
    dataset_id = test_dataset
    logout(module_client)
    login_resp = login(module_client, module_client.test_user2_email, "test1234")
    assert login_resp.status_code == 200
    monkeypatch.setattr("app.modules.comment.routes.render_template", lambda *a, **k: "OK")
    r = module_client.get("/comment")
    assert r.status_code == 200
    r2 = module_client.get(f"/comment/dataset/{dataset_id}")
    assert r2.status_code == 200
    r3 = test_client.get("/comment/parent/99999")
    assert r3.status_code == 404
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="visible parent",
    )
    logout(test_client)
    r4 = test_client.get(f"/comment/parent/{parent.id}")
    assert r4.status_code == 200
    login(module_client, module_client.test_user2_email, "test1234")
    bad = module_client.post(f"/comment/dataset/{dataset_id}/create", json={"content": "   "})
    assert bad.status_code == 400
    login(module_client, module_client.test_user2_email, "test1234")
    r5 = module_client.post("/comment/parent/99999/reply", json={"content": "x"})
    assert r5.status_code == 404


def test_update_children_visibility_and_repr(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="parent for propagation",
    )
    child1 = comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=parent.id,
        content="child1",
    )
    child2 = comment_service.create(
        user_id=module_client.test_user2_id,
        dataset_id=dataset_id,
        parent_id=parent.id,
        content="child2",
    )
    grandchild = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=child1.id,
        content="grandchild",
    )
    assert getattr(child1, "visible", True) is True
    assert getattr(child2, "visible", True) is True
    assert getattr(grandchild, "visible", True) is True
    updated = comment_service.update_children_visibility(parent.id, False)
    assert updated >= 2
    c1 = comment_service.get_by_id(child1.id)
    c2 = comment_service.get_by_id(child2.id)
    assert getattr(c1, "visible", True) is False
    assert getattr(c2, "visible", True) is False
    _ = repr(c1)
    comment_service.update_children_visibility(parent.id, True)
    refreshed = comment_service.get_by_id(child1.id)
    assert getattr(refreshed, "visible", False) is True


def test_count_and_seeder(module_client, test_dataset, monkeypatch):
    """Cover count_comments_by_dataset and run the seeder for coverage."""
    dataset_id = test_dataset

    # Create a couple of comments
    comment_service.create(user_id=module_client.test_user1_id, dataset_id=dataset_id, parent_id=None, content="count1")
    comment_service.create(user_id=module_client.test_user2_id, dataset_id=dataset_id, parent_id=None, content="count2")

    count = comment_service.count_comments_by_dataset(dataset_id)
    assert isinstance(count, int) and count >= 2

    # Run seeder (should return None without raising foreign-key insertion errors in test DB)
    from app.modules.comment.seeders import CommentSeeder

    # Patch CommentSeeder.seed to be a no-op for tests so it doesn't attempt to insert data
    monkeypatch.setattr("app.modules.comment.seeders.CommentSeeder.seed", lambda self, data: [])

    s = CommentSeeder()
    assert s.run() is None


def test_create_reply_server_error(module_client, test_dataset, monkeypatch):
    dataset_id = test_dataset
    login(module_client, module_client.test_user2_email, "test1234")
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="p",
    )
    monkeypatch.setattr("app.modules.comment.routes.comment_service", comment_service)
    monkeypatch.setattr(
        comment_service,
        "create",
        lambda *a, **k: (_ for _ in ()).throw(Exception("boom")),
    )
    r = module_client.post(f"/comment/dataset/{dataset_id}/create", json={"content": "ok"})
    assert r.status_code == 500
    rr = module_client.post(f"/comment/parent/{parent.id}/reply", json={"content": "ok"})
    assert rr.status_code == 500


def test_owner_access_hidden_parent(module_client, test_dataset, monkeypatch):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="hidden",
    )
    comment_service.update(parent.id, visible=False)
    login(module_client, module_client.test_user2_email, "test1234")
    monkeypatch.setattr("app.modules.comment.routes.render_template", lambda *a, **k: "OK")
    r = module_client.get(f"/comment/parent/{parent.id}")
    assert r.status_code == 200


def test_reply_validation_empty_content(module_client, test_dataset):
    dataset_id = test_dataset
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="p",
    )
    login(module_client, module_client.test_user2_email, "test1234")
    r = module_client.post(f"/comment/parent/{parent.id}/reply", json={"content": "   "})
    assert r.status_code == 400


def test_form_validation_branches(module_client, test_dataset, monkeypatch):
    dataset_id = test_dataset

    class DummyForm:
        def validate_on_submit(self):
            return False

        @property
        def errors(self):
            return {"content": ["Invalid"]}

    monkeypatch.setattr("app.modules.comment.routes.CommentForm", DummyForm)
    login(module_client, module_client.test_user2_email, "test1234")
    r = module_client.post(f"/comment/dataset/{dataset_id}/create", data={})
    assert r.status_code == 400
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="p",
    )
    rr = module_client.post(f"/comment/parent/{parent.id}/reply", data={})
    assert rr.status_code == 400


def test_form_success_branches(module_client, test_dataset, monkeypatch):
    dataset_id = test_dataset

    class ContentField:
        def __init__(self, data):
            self.data = data

    class DummyFormTrue:
        def __init__(self):
            self.content = ContentField("created via form")

        def validate_on_submit(self):
            return True

    monkeypatch.setattr("app.modules.comment.routes.CommentForm", DummyFormTrue)
    login(module_client, module_client.test_user2_email, "test1234")
    r = module_client.post(f"/comment/dataset/{dataset_id}/create", data={})
    assert r.status_code == 201
    parent = comment_service.create(
        user_id=module_client.test_user1_id,
        dataset_id=dataset_id,
        parent_id=None,
        content="p",
    )
    rr = module_client.post(f"/comment/parent/{parent.id}/reply", data={})
    assert rr.status_code == 201
