import os
from unittest.mock import patch

import pytest


@pytest.mark.usefixtures("test_client")
class TestAuthGithubRoutes:
    def test_github_status_without_token(self, test_client):
        # Comprueba el estado cuando NO hay token de GitHub en sesión

        # 1) Ejecutar la petición sin token en sesión
        resp = test_client.get("/github/status")
        # 2) Verificar código de estado
        assert resp.status_code == 200
        # 3) Verificar payload de respuesta
        assert resp.get_json()["connected"] is False

    def test_github_status_with_token(self, test_client):
        # Comprueba el estado cuando SÍ hay token de GitHub en sesión

        # 1) Inyectar token de GitHub en la sesión del cliente
        with test_client.session_transaction() as sess:
            sess["github_token"] = "abc"
        # 2) Realizar la petición de estado
        resp = test_client.get("/github/status")
        # 3) Verificar resultado esperado
        assert resp.status_code == 200
        assert resp.get_json()["connected"] is True

    def test_github_login_missing_env_returns_500(self, test_client):
        # Si faltan variables de entorno de OAuth, el login devuelve 500

        # 1) Vaciar variables de entorno relevantes para OAuth
        with patch.dict(os.environ, {}, clear=True):
            # 2) Ejecutar la ruta de login
            resp = test_client.get("/github/login")
        # 3) Validar error esperado
        assert resp.status_code == 500
        assert "GitHub OAuth not configured" in resp.get_data(as_text=True)

    def test_github_login_returns_redirect_html_and_sets_state(self, test_client):
        # Renderiza HTML con la URL de autorización y setea state/next en sesión

        # 1) Simular entorno con credenciales de OAuth
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "client123", "GITHUB_CLIENT_SECRET": "secret123"}, clear=True):
            # 2) Lanzar la petición incluyendo el parámetro next
            resp = test_client.get("/github/login?next=/after_oauth")
        # 3) Comprobar que la respuesta es correcta y contiene la URL de authorize
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "https://github.com/login/oauth/authorize?" in html
        assert "client_id=client123" in html
        # 4) Verificar que state y next se hayan almacenado en sesión
        with test_client.session_transaction() as sess:
            assert "github_oauth_state" in sess
            assert sess.get("github_oauth_next") == "/after_oauth"

    def test_github_callback_invalid_state(self, test_client):
        # El callback falla si el parámetro state no coincide con el almacenado

        # 1) Configurar entorno de OAuth
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "client123", "GITHUB_CLIENT_SECRET": "secret123"}, clear=True):
            # 2) Guardar state esperado en sesión
            with test_client.session_transaction() as sess:
                sess["github_oauth_state"] = "expected"
            # 3) Simular callback con state erróneo
            resp = test_client.get("/github/callback?code=CODE&state=wrong")
        # 4) Verificar respuesta de error
        assert resp.status_code == 400
        assert "Invalid OAuth state" in resp.get_data(as_text=True)

    def test_github_callback_success_sets_token_and_redirects(self, test_client):
        # Callback exitoso: intercambia code por token, guarda token y redirige

        # 1) Simular variables de entorno para OAuth
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "client123", "GITHUB_CLIENT_SECRET": "secret123"}, clear=True):
            # 2) Preparar sesión con state esperado y URL de retorno
            with test_client.session_transaction() as sess:
                sess["github_oauth_state"] = "abc"
                sess["github_oauth_next"] = "/post_login"

            # 3) Mockear el intercambio de code a token en GitHub
            class DummyResp:
                def __init__(self):
                    self._json = {"access_token": "tok-xyz"}

                def raise_for_status(self):
                    return None

                def json(self):
                    return self._json

            with patch("requests.post", return_value=DummyResp()):
                # 4) Realizar la llamada al callback con state correcto
                resp = test_client.get("/github/callback?code=CODE&state=abc")
        # 5) Verificar redirección y token en sesión
        assert resp.status_code == 302
        assert resp.headers.get("Location", "").endswith("/post_login")
        with test_client.session_transaction() as sess:
            assert sess.get("github_token") == "tok-xyz"
            assert "github_oauth_state" not in sess
            # github_oauth_next se hace pop en el callback

    def test_github_callback_error_payload_returns_400(self, test_client):
        # Callback con error: no hay access_token en la respuesta

        # 1) Simular entorno de OAuth y state válido
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "client123", "GITHUB_CLIENT_SECRET": "secret123"}, clear=True):
            with test_client.session_transaction() as sess:
                sess["github_oauth_state"] = "abc"

            # 2) Preparar DummyResp que no contiene access_token
            class DummyResp:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"error": "bad"}

            # 3) Mockear la llamada a GitHub devolviendo error
            with patch("requests.post", return_value=DummyResp()):
                # 4) Ejecutar callback y validar respuesta 400
                resp = test_client.get("/github/callback?code=CODE&state=abc")
        assert resp.status_code == 400
        assert "GitHub OAuth error" in resp.get_data(as_text=True)
