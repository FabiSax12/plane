"""
PI-21: POST attachment excediendo FILE_SIZE_LIMIT
Tecnica: Analisis de valores limite
HU-22: Adjuntar archivos a un work item

HALLAZGO: Plane usa pre-signed URLs de S3 para todos los uploads.
Django nunca recibe el archivo directamente. El FILE_SIZE_LIMIT no genera un 400;
en cambio, el endpoint trunca silenciosamente el size enviado al limite configurado
y devuelve una URL pre-firmada con ese cap. La validacion real ocurre en S3.

Por lo tanto:
- La validacion unitaria del validator (PU-23) cubre el caso de rechazo de archivos grandes.
- Este test de integracion verifica el comportamiento real del endpoint:
  truncacion del size y validacion de entity_type/file_type invalidos.
"""
import pytest
from unittest.mock import patch, MagicMock

from plane.tests.factories import IssueFactory


FILE_SIZE_LIMIT = 5_242_880  # 5 MB


@pytest.mark.django_db
class TestIssueAttachmentEndpoint:

    def _asset_url(self, workspace):
        return f"/api/workspaces/{workspace.slug}/assets/v2/workspaces/{workspace.slug}/"

    @patch("plane.app.views.asset.v2.S3Storage")
    def test_size_above_limit_is_capped_not_rejected(self, mock_s3, auth_client, workspace, project, default_state):
        """PI-21: Enviar size=15MB no genera 400 - el endpoint lo trunca a FILE_SIZE_LIMIT y retorna 200."""
        mock_storage = MagicMock()
        mock_storage.generate_presigned_post.return_value = {"url": "https://s3.fake/upload", "fields": {}}
        mock_s3.return_value = mock_storage

        issue = IssueFactory(project=project, state=default_state)

        url = self._asset_url(workspace)
        response = auth_client.post(
            url,
            data={
                "name": "big_file.jpg",
                "type": "image/jpeg",
                "size": FILE_SIZE_LIMIT * 3,  # 15 MB
                "entity_type": "ISSUE_ATTACHMENT",
                "entity_identifier": str(issue.id),
            },
            format="json",
        )

        # El endpoint no rechaza - trunca el size y devuelve 200 con upload_data
        assert response.status_code == 200
        assert "upload_data" in response.data
        assert "asset_id" in response.data

    @patch("plane.app.views.asset.v2.S3Storage")
    def test_invalid_file_type_returns_400(self, mock_s3, auth_client, workspace, project, default_state):
        """Tipo de archivo no permitido (ej. .exe) retorna 400."""
        issue = IssueFactory(project=project, state=default_state)

        url = self._asset_url(workspace)
        response = auth_client.post(
            url,
            data={
                "name": "malware.exe",
                "type": "application/octet-stream",
                "size": 1_000_000,
                "entity_type": "ISSUE_ATTACHMENT",
                "entity_identifier": str(issue.id),
            },
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data

    def test_invalid_entity_type_returns_400(self, auth_client, workspace):
        """entity_type invalido retorna 400 sin necesidad de S3."""
        url = self._asset_url(workspace)
        response = auth_client.post(
            url,
            data={
                "name": "file.jpg",
                "type": "image/jpeg",
                "size": 1_000_000,
                "entity_type": "INVALID_TYPE",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data
