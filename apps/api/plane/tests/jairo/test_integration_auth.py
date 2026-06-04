import json
import os
import uuid

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from plane.db.models import User
from plane.license.models.instance import Instance
from plane.tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_instance():
    if not Instance.objects.exists():
        Instance.objects.create(
            id=uuid.uuid4(),
            instance_name="Test Instance",
            instance_id=str(uuid.uuid4()),
            current_version="1.0.0",
            domain="http://localhost:8000",
            last_checked_at=timezone.now(),
            is_setup_done=True,
        )


def _make_client():
    return Client(HTTP_USER_AGENT="Mozilla/5.0")


# ---------------------------------------------------------------------------
# PI-01: POST /auth/sign-up/ con datos validos retorna redirect 302 con sesion
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI01SignUpValid:
    def setup_method(self):
        _setup_instance()
        self.client = _make_client()
        self.response = self.client.post(
            reverse("sign-up"),
            data={
                "email": "nuevo@itcr.ac.cr",
                "password": "P4ssw0rd!Segura",
                "first_name": "QA",
                "last_name": "Tester",
            },
            follow=False,
        )

    def test_returns_302(self):
        assert self.response.status_code == 302

    def test_establishes_session(self):
        assert "_auth_user_id" in self.client.session

    def test_no_error_code_in_url(self):
        assert "error_code" not in self.response.url


# ---------------------------------------------------------------------------
# PI-02: POST /auth/sign-up/ con email duplicado → USER_ALREADY_EXIST
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI02SignUpDuplicateEmail:
    def setup_method(self):
        _setup_instance()
        self.client = _make_client()
        UserFactory(email="duplicado@itcr.ac.cr")
        self.response = self.client.post(
            reverse("sign-up"),
            data={
                "email": "duplicado@itcr.ac.cr",
                "password": "P4ssw0rd!Segura",
            },
            follow=False,
        )

    def test_returns_302(self):
        assert self.response.status_code == 302

    def test_contains_error_code(self):
        assert "USER_ALREADY_EXIST" in self.response.url


# ---------------------------------------------------------------------------
# PI-03: POST /auth/sign-in/ con credenciales validas establece sesion (302)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI03SignInValid:
    def setup_method(self):
        _setup_instance()
        self.client = _make_client()
        user = UserFactory(email="login@itcr.ac.cr")
        user.set_password("PassValida1!")
        user.save()
        self.response = self.client.post(
            reverse("sign-in"),
            data={"email": "login@itcr.ac.cr", "password": "PassValida1!"},
            follow=False,
        )

    def test_returns_302(self):
        assert self.response.status_code == 302

    def test_establishes_session(self):
        assert "_auth_user_id" in self.client.session

    def test_no_error_code_in_url(self):
        assert "error_code" not in self.response.url


# ---------------------------------------------------------------------------
# PI-04: POST /auth/sign-in/ con contrasena incorrecta → AUTHENTICATION_FAILED
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI04SignInWrongPassword:
    def setup_method(self):
        _setup_instance()
        self.client = _make_client()
        user = UserFactory(email="wrongpass@itcr.ac.cr")
        user.set_password("RealPass1!")
        user.save()
        self.response = self.client.post(
            reverse("sign-in"),
            data={"email": "wrongpass@itcr.ac.cr", "password": "WrongPass1!"},
            follow=False,
        )

    def test_returns_302(self):
        assert self.response.status_code == 302

    def test_contains_error_code(self):
        assert "AUTHENTICATION_FAILED_SIGN_IN" in self.response.url

    def test_does_not_establish_session(self):
        assert "_auth_user_id" not in self.client.session


# ---------------------------------------------------------------------------
# PI-05: Throttle bloquea tras 30 requests/minuto (429)
# HALLAZGO: este test FALLA porque SignInAuthEndpoint es una
#       django.views.View y NO aplica AuthenticationThrottle (DRF).
#       Esto expone una brecha de seguridad en el repositorio.
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI05AuthenticationThrottle:
    def setup_method(self):
        _setup_instance()
        self.client = _make_client()
        self.url = reverse("sign-in")
        for _ in range(30):
            self.client.post(
                self.url,
                data={"email": "cualquiera@test.com", "password": "nop"},
            )

    def test_throttle_blocks_after_30_requests(self):
        response = self.client.post(
            self.url,
            data={"email": "cualquiera@test.com", "password": "nop"},
        )
        assert response.status_code == 429


# ---------------------------------------------------------------------------
# PI-06: POST /auth/forgot-password/ invoca tarea asincrona y retorna 200
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.jairo
class TestPI06ForgotPassword:
    def setup_method(self):
        _setup_instance()
        os.environ.setdefault("EMAIL_HOST", "test-smtp.invalid")
        self.client = _make_client()
        UserFactory(email="usuario@itcr.ac.cr")
        self.patcher = patch(
            "plane.authentication.views.app.password_management.forgot_password.delay"
        )
        self.mock_delay = self.patcher.start()
        self.response = self.client.post(
            "/auth/forgot-password/",
            data=json.dumps({"email": "usuario@itcr.ac.cr"}),
            content_type="application/json",
        )

    def teardown_method(self):
        self.patcher.stop()

    def test_returns_200(self):
        assert self.response.status_code == 200

    def test_calls_forgot_password_delay(self):
        self.mock_delay.assert_called_once()
