"""
 * Author: Fabián Vargas
 * Test cases: PU-10
"""

import pytest

from plane.app.serializers import WorkSpaceSerializer

@pytest.mark.unit
@pytest.mark.django_db
@pytest.mark.qa
@pytest.mark.fabian
class TestWorkSpaceSerializer:
    """Test the WorkSpaceSerializer"""

    def test_validate_slug_rejects_disallowed_characters(self):
        """PU-10: reject custom URL with disallowed characters"""
        serializer = WorkSpaceSerializer(data={"name": "Plane TEC", "slug": "plane@tec/2026"})

        assert not serializer.is_valid()
        assert serializer.errors == {
            "slug": ["Slug can only contain letters, numbers, hyphens (-), and underscores (_)"]
        }