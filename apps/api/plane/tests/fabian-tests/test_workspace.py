"""
 * Author: Fabián Vargas
 * Test cases: PU-10
"""

import pytest

from plane.app.serializers import WorkSpaceSerializer

EXPECTED_SLUG_ERROR = [
    'Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'
]


@pytest.mark.unit
@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.fabian
class TestWorkSpaceSerializer:
    """Test the WorkSpaceSerializer"""

    def _build_invalid_slug_serializer(self):
        return WorkSpaceSerializer(data={"name": "Plane TEC", "slug": "plane@tec/2026"})

    def test_validate_slug_rejects_disallowed_characters(self):
        """PU-10: reject custom URL with disallowed characters"""
        serializer = self._build_invalid_slug_serializer()

        assert not serializer.is_valid()

    def test_validate_slug_disallowed_characters_error_message(self):
        """PU-10: the rejection produces the documented error message for the slug field"""
        serializer = self._build_invalid_slug_serializer()
        serializer.is_valid()

        assert serializer.errors == {"slug": EXPECTED_SLUG_ERROR}
