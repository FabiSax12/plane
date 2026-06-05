"""
PU-23: Rechazar archivo adjunto que excede FILE_SIZE_LIMIT (5 MB)
Tecnica: Analisis de valores limite
HU-22: Adjuntar archivos a un work item
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from plane.db.models.asset import file_size

FILE_SIZE_LIMIT = 5_242_880  # 5 MB en bytes


@pytest.mark.qa
@pytest.mark.daniel
class TestFileSizeValidatorRejectsLargeFile:
    """PU-23 caso invalido: archivo mayor al limite lanza ValidationError."""

    @pytest.fixture(autouse=True)
    def setup(self):
        large_file = SimpleUploadedFile("big.bin", b"\x00" * (FILE_SIZE_LIMIT + 1))
        try:
            file_size(large_file)
            self.raised = False
            self.exception = None
        except ValidationError as exc:
            self.raised = True
            self.exception = exc

    def test_raises_validation_error(self):
        assert self.raised is True

    def test_error_message_mentions_5mb(self):
        assert "5 MB" in str(self.exception)


@pytest.mark.qa
@pytest.mark.daniel
class TestFileSizeValidatorAcceptsValidFiles:
    """PU-23 casos validos: archivos en o por debajo del limite no lanzan excepcion."""

    def test_accepts_file_at_exact_limit(self):
        exact_file = SimpleUploadedFile("exact.bin", b"\x00" * FILE_SIZE_LIMIT)
        try:
            file_size(exact_file)
            raised = False
        except ValidationError:
            raised = True
        assert raised is False

    def test_accepts_file_below_limit(self):
        small_file = SimpleUploadedFile("small.bin", b"\x00" * 1_048_576)
        try:
            file_size(small_file)
            raised = False
        except ValidationError:
            raised = True
        assert raised is False

    def test_rejects_file_well_above_limit(self):
        huge_file = SimpleUploadedFile("huge.bin", b"\x00" * (FILE_SIZE_LIMIT * 3))
        with pytest.raises(ValidationError):
            file_size(huge_file)
