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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def setup_instance(db):
    instance_id = uuid.uuid4() if not Instance.objects.exists() else Instance.objects.first().id
    Instance.objects.update_or_create(
        id=instance_id,
        defaults={
            "instance_name": "Test Instance",
            "instance_id": str(uuid.uuid4()),
            "current_version": "1.0.0",
            "domain": "http://localhost:8000",
            "last_checked_at": timezone.now(),
            "is_setup_done": True,
        },
    )
    return Instance.objects.first()


@pytest.fixture
def django_client():
    return Client(HTTP_USER_AGENT="Mozilla/5.0")


# ---------------------------------------------------------------------------
# PI-01: POST /auth/sign-up/ con datos validos retorna redirect 302 con sesion
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI01SignUpValid:
    def test_sign_up_valid_redirects_with_session(self, django_client, setup_instance):
        response = django_client.post(
            reverse("sign-up"),
            data={
                "email": "nuevo@itcr.ac.cr",
                "password": "P4ssw0rd!Segura",
                "first_name": "QA",
                "last_name": "Tester",
            },
            follow=False,
        )
        assert response.status_code == 302
        assert "_auth_user_id" in django_client.session
        assert "error_code" not in response.url


# ---------------------------------------------------------------------------
# PI-02: POST /auth/sign-up/ con email duplicado → USER_ALREADY_EXIST
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI02SignUpDuplicateEmail:
    def test_sign_up_duplicate_email_returns_user_already_exist(self, django_client, setup_instance):
        UserFactory(email="duplicado@itcr.ac.cr")
        response = django_client.post(
            reverse("sign-up"),
            data={
                "email": "duplicado@itcr.ac.cr",
                "password": "P4ssw0rd!Segura",
            },
            follow=False,
        )
        assert response.status_code == 302
        assert "USER_ALREADY_EXIST" in response.url


# ---------------------------------------------------------------------------
# PI-03: POST /auth/sign-in/ con credenciales validas establece sesion (302)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI03SignInValid:
    def test_sign_in_valid_redirects_with_session(self, django_client, setup_instance):
        user = UserFactory(email="login@itcr.ac.cr")
        user.set_password("PassValida1!")
        user.save()
        response = django_client.post(
            reverse("sign-in"),
            data={"email": "login@itcr.ac.cr", "password": "PassValida1!"},
            follow=False,
        )
        assert response.status_code == 302
        assert "_auth_user_id" in django_client.session
        assert "error_code" not in response.url


# ---------------------------------------------------------------------------
# PI-04: POST /auth/sign-in/ con contrasena incorrecta → AUTHENTICATION_FAILED
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI04SignInWrongPassword:
    def test_sign_in_wrong_password_returns_error(self, django_client, setup_instance):
        user = UserFactory(email="wrongpass@itcr.ac.cr")
        user.set_password("RealPass1!")
        user.save()
        response = django_client.post(
            reverse("sign-in"),
            data={"email": "wrongpass@itcr.ac.cr", "password": "WrongPass1!"},
            follow=False,
        )
        assert response.status_code == 302
        assert "AUTHENTICATION_FAILED_SIGN_IN" in response.url
        assert "_auth_user_id" not in django_client.session


# ---------------------------------------------------------------------------
# PI-05: Throttle bloquea tras 30 requests/minuto (429)
# NOTA: Se espera que este test FALLE porque SignInAuthEndpoint es una
#       django.views.View y NO aplica AuthenticationThrottle (DRF).
#       Esto expone una brecha de seguridad en el repositorio.
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI05AuthenticationThrottle:
    def test_throttle_blocks_after_30_requests(self, django_client, setup_instance):
        for _ in range(30):
            django_client.post(
                reverse("sign-in"),
                data={"email": "cualquiera@test.com", "password": "nop"},
            )
        response = django_client.post(
            reverse("sign-in"),
            data={"email": "cualquiera@test.com", "password": "nop"},
        )
        assert response.status_code == 429


# ---------------------------------------------------------------------------
# PI-06: POST /auth/forgot-password/ invoca tarea asincrona y retorna 200
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPI06ForgotPassword:
    @patch("plane.authentication.views.app.password_management.forgot_password.delay")
    def test_forgot_password_invokes_async_task(self, mock_delay, django_client, setup_instance):
        os.environ.setdefault("EMAIL_HOST", "test-smtp.invalid")
        user = UserFactory(email="usuario@itcr.ac.cr")
        response = django_client.post(
            "/auth/forgot-password/",
            data={"email": "usuario@itcr.ac.cr"},
            content_type="application/json",
        )
        assert response.status_code == 200
        mock_delay.assert_called_once()
