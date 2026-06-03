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
    """Wrap HTML in the JSON string format expected by extract_mentions."""
    return json.dumps({"description_html": html})


class TestExtractMentions:

    def test_returns_both_uuids_from_two_mention_tags(self):
        """PU-20: extract_mentions retorna los UUIDs de los dos mention-components presentes."""
        html = (
            f'<p>Hola '
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f' y '
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_JAIRO}"></mention-component>'
            f'</p>'
        )
        result = extract_mentions(build_payload(html))

        assert isinstance(result, list)
        assert UUID_RAFA in result
        assert UUID_JAIRO in result
        assert len(result) == 2

    def test_ignores_tags_without_user_mention_entity(self):
        """Solo extrae tags con entity_name=user_mention, ignora otros."""
        html = (
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f'<mention-component entity_name="issue_mention" entity_identifier="other-uuid"></mention-component>'
        )
        result = extract_mentions(build_payload(html))

        assert result == [UUID_RAFA]

    def test_deduplicates_repeated_uuid(self):
        """Si el mismo UUID aparece dos veces, se retorna una sola vez."""
        html = (
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
            f'<mention-component entity_name="user_mention" entity_identifier="{UUID_RAFA}"></mention-component>'
        )
        result = extract_mentions(build_payload(html))

        assert result == [UUID_RAFA]

    def test_returns_empty_list_when_no_mentions(self):
        """Sin mention-components retorna lista vacía."""
        html = "<p>Sin menciones aqui.</p>"
        result = extract_mentions(build_payload(html))

        assert result == []

    def test_returns_empty_list_on_invalid_input(self):
        """Input inválido (no JSON) retorna lista vacía sin lanzar excepción."""
        result = extract_mentions("esto no es json")

        assert result == []
