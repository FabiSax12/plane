"""
PU-20: Extraer menciones de comentario HTML con extract_mentions
Tecnica: Cobertura de sentencias
HU-21: Añadir comentarios a un work item con menciones
"""
import json
import pytest

from plane.bgtasks.notification_task import extract_mentions


UUID_RAFA = "uuid-rafa-0000-0000-000000000001"
UUID_JAIRO = "uuid-jairo-000-0000-000000000002"


def build_payload(html: str) -> str:
    """Envuelve HTML en el JSON string que espera extract_mentions."""
    return json.dumps({"description_html": html})


@pytest.mark.qa
@pytest.mark.daniel
class TestExtractMentionsTwoTags:
    """PU-20: Caso base con dos mention-components distintos."""

    @pytest.fixture(autouse=True)
    def setup(self):
        html = (
            f'<p>'
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f' y '
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_JAIRO}"></mention-component>'
            f'</p>'
        )
        self.result = extract_mentions(build_payload(html))

    def test_result_is_a_list(self):
        assert isinstance(self.result, list)

    def test_result_contains_first_uuid(self):
        assert UUID_RAFA in self.result

    def test_result_contains_second_uuid(self):
        assert UUID_JAIRO in self.result

    def test_result_has_exactly_two_elements(self):
        assert len(self.result) == 2


@pytest.mark.qa
@pytest.mark.daniel
class TestExtractMentionsEdgeCases:
    """Casos borde: entidad incorrecta, duplicados, sin menciones, input invalido."""

    def test_ignores_non_user_mention_entity(self):
        html = (
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f'<mention-component entity_name="issue_mention" entity_identifier="other-uuid"></mention-component>'
        )
        result = extract_mentions(build_payload(html))
        assert result == [UUID_RAFA]

    def test_deduplicates_repeated_uuid(self):
        html = (
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
        )
        result = extract_mentions(build_payload(html))
        assert result == [UUID_RAFA]

    def test_returns_empty_list_when_no_mentions(self):
        html = "<p>Sin menciones aqui.</p>"
        result = extract_mentions(build_payload(html))
        assert result == []

    def test_returns_empty_list_on_invalid_json(self):
        result = extract_mentions("esto no es json")
        assert result == []
