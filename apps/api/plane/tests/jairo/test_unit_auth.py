import pytest
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from zxcvbn import zxcvbn


@pytest.mark.qa
@pytest.mark.jairo
class TestPU01ValidEmail:
    """PU-01: Aceptar correo valido con validate_email de Django"""

    def test_valid_email_does_not_raise(self):
        assert validate_email("usuario.prueba@itcr.ac.cr") is None


@pytest.mark.qa
@pytest.mark.jairo
class TestPU02InvalidEmail:
    """PU-02: Rechazar correo invalido con validate_email de Django"""

    def test_invalid_email_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_email("sin-arroba.com")


@pytest.mark.qa
@pytest.mark.jairo
class TestPU03StrongPassword:
    """PU-03: Aceptar contrasena fuerte (zxcvbn score >= 3)"""

    def test_strong_password_score(self):
        result = zxcvbn("P4ssw0rd!Segura")
        assert result["score"] >= 3


@pytest.mark.qa
@pytest.mark.jairo
class TestPU04WeakPassword:
    """PU-04: Rechazar contrasena debil (zxcvbn score < 3)"""

    def test_weak_password_score(self):
        result = zxcvbn("12345")
        assert result["score"] < 3
