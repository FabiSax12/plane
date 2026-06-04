import pytest
from plane.app.serializers.workspace import WorkSpaceSerializer


class TestPU05ValidSlug:
    """PU-05: Aceptar slug alfanumerico-guion en validate_slug"""

    @pytest.mark.django_db(databases=["default"])
    def test_valid_slug_passes_validation(self):
        serializer = WorkSpaceSerializer(data={"name": "Test", "slug": "plane-tec-2026"})
        assert serializer.is_valid() is True


class TestPU06InvalidSlug:
    """PU-06: Rechazar slug con caracteres especiales en validate_slug"""

    def setup_method(self):
        self.serializer = WorkSpaceSerializer(
            data={"name": "Test", "slug": "plane@tec/2026"}
        )

    @pytest.mark.django_db(databases=["default"])
    def test_rejects_invalid_slug(self):
        assert self.serializer.is_valid() is False

    @pytest.mark.django_db(databases=["default"])
    def test_reports_slug_error_field(self):
        self.serializer.is_valid()
        assert "slug" in self.serializer.errors
