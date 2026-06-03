import pytest
from django.core.exceptions import ValidationError
from plane.app.serializers.workspace import WorkSpaceSerializer


class TestPU05ValidSlug:
    """PU-05: Aceptar slug alfanumerico-guion en validate_slug"""

    @pytest.mark.django_db(databases=["default"])
    def test_valid_slug_passes_validation(self):
        serializer = WorkSpaceSerializer(data={"name": "Test", "slug": "plane-tec-2026"})
        assert serializer.is_valid() is True


class TestPU06InvalidSlug:
    """PU-06: Rechazar slug con caracteres especiales en validate_slug"""

    @pytest.mark.django_db(databases=["default"])
    def test_invalid_slug_fails_validation(self):
        serializer = WorkSpaceSerializer(data={"name": "Test", "slug": "plane@tec/2026"})
        assert serializer.is_valid() is False
        assert "slug" in serializer.errors
