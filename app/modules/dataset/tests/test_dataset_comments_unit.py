import types
from datetime import datetime
from unittest.mock import patch

import pytest
from flask import Flask

import app.modules.dataset.routes as routes


@pytest.mark.usefixtures("test_client")
class TestDatasetCommentsRoutesUnit:
    """Pruebas unitarias para las rutas de comentarios del módulo dataset."""

    def make_user(self, id=1, surname="Doe", name="John", email="user@example.com"):
        user = types.SimpleNamespace()
        user.id = id
        user.is_authenticated = True
        profile = types.SimpleNamespace(surname=surname, name=name)
        user.profile = profile
        user.email = email
        return user

    def _new_comment_mock(self, cid=1, content="c", parent_id=None, user=None):
        c = types.SimpleNamespace()
        c.id = cid
        c.content = content
        c.parent_id = parent_id
        c.created_at = datetime.utcnow()
        c.user = user
        return c

    def test_post_comment_success(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        dataset = types.SimpleNamespace(id=1, comments=[])
        user = self.make_user(id=10, surname="Garcia", name="Ana", email="ana@example.com")
        comment = self._new_comment_mock(cid=123, content="This is a test comment", parent_id=None, user=user)

        with app.test_request_context("/dataset/1/comment", method="POST", json={"content": "This is a test comment"}):
            with patch.object(routes, "dataset_service", autospec=True) as ds_svc:
                ds_svc.get_or_404.return_value = dataset
                routes.current_user = user
                with patch.object(routes, "comment_service", autospec=True) as c_svc:
                    c_svc.create.return_value = comment

                    resp = routes.post_comment.__wrapped__(1)
                    if isinstance(resp, tuple):
                        response_obj, status = resp
                    else:
                        response_obj = resp
                        status = getattr(resp, "status_code", 200)

                    assert status == 200
                    data = response_obj.get_json()
                    assert data["id"] == 123
                    assert data["content"] == "This is a test comment"
                    assert data["parent_id"] is None
                    # author_name puede ser "Garcia, Ana" o el email si no hay perfil
                    assert any(x in data.get("author_name", "") for x in ("Garcia, Ana", "ana@example.com"))

    def test_post_comment_empty_content(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        dataset = types.SimpleNamespace(id=1, comments=[])
        user = self.make_user()

        with app.test_request_context("/dataset/1/comment", method="POST", json={"content": "   "}):
            with patch.object(routes, "dataset_service", autospec=True) as ds_svc:
                ds_svc.get_or_404.return_value = dataset
                routes.current_user = user
                # Llamada debe devolver 400 por contenido vacío
                resp = routes.post_comment.__wrapped__(1)
                if isinstance(resp, tuple):
                    response_obj, status = resp
                else:
                    response_obj = resp
                    status = getattr(resp, "status_code", 200)
                assert status == 400
                data = response_obj.get_json()
                assert "Empty" in (data.get("error", "") + data.get("message", ""))

    def test_hide_comment_not_authorized(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        comment = types.SimpleNamespace(id=10, dataset_id=5, visible=True)
        dataset = types.SimpleNamespace(id=5, user_id=999)  # owner is 999
        with app.test_request_context(f"/dataset/comment/{comment.id}/hide", method="POST"):
            with patch.object(routes, "comment_service", autospec=True) as c_svc:
                c_svc.get_by_id.return_value = comment
                with patch.object(routes, "dataset_service", autospec=True) as ds_svc:
                    ds_svc.get_or_404.return_value = dataset
                    routes.current_user = self.make_user(id=1)  # different user

                    with pytest.raises(Exception) as exc:
                        routes.hide_comment.__wrapped__(comment.id)
                    # asegura que es un abort 403 / Forbidden
                    assert "403" in str(exc.value) or "Forbidden" in str(exc.value)

    def test_hide_comment_toggle_success(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        comment = types.SimpleNamespace(id=11, dataset_id=7, visible=True)
        dataset = types.SimpleNamespace(id=7, user_id=42)

        with app.test_request_context(f"/dataset/comment/{comment.id}/hide", method="POST"):
            with patch.object(routes, "comment_service", autospec=True) as c_svc:
                c_svc.get_by_id.return_value = comment

                # toggle implementation: update returns comment with flipped visible
                def fake_update(cid, visible):
                    comment.visible = visible
                    return comment

                c_svc.update.side_effect = lambda cid, visible: fake_update(cid, visible)
                c_svc.update_children_visibility.return_value = None

                with patch.object(routes, "dataset_service", autospec=True) as ds_svc:
                    ds_svc.get_or_404.return_value = dataset
                    routes.current_user = self.make_user(id=42)  # owner

                    resp = routes.hide_comment.__wrapped__(comment.id)
                    if isinstance(resp, tuple):
                        response_obj, status = resp
                    else:
                        response_obj = resp
                        status = getattr(resp, "status_code", 200)

                    data = response_obj.get_json()
                    assert status == 200
                    assert data["id"] == comment.id
                    assert data["visible"] is False

    def test_delete_comment_success(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        comment = types.SimpleNamespace(id=99, dataset_id=55)
        dataset = types.SimpleNamespace(id=55, user_id=2)

        with app.test_request_context(f"/dataset/comment/{comment.id}/delete", method="POST"):
            with patch.object(routes, "comment_service", autospec=True) as c_svc:
                c_svc.get_by_id.return_value = comment
                c_svc.delete.return_value = None

                with patch.object(routes, "dataset_service", autospec=True) as ds_svc:
                    ds_svc.get_or_404.return_value = dataset
                    routes.current_user = self.make_user(id=2)  # owner

                    resp = routes.delete_comment.__wrapped__(comment.id)
                    if isinstance(resp, tuple):
                        response_obj, status = resp
                    else:
                        response_obj = resp
                        status = getattr(resp, "status_code", 200)

                    data = response_obj.get_json()
                    assert status == 200
                    assert data["id"] == comment.id
                    assert data["deleted"] is True
