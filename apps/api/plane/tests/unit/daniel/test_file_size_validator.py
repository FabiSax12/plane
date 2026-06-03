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


class TestFileSizeValidator:

    def test_rejects_file_above_limit(self):
        """PU-23 (caso invalido): archivo de 15 MB lanza ValidationError."""
        large_file = SimpleUploadedFile("big.bin", b"\x00" * (FILE_SIZE_LIMIT + 1))

        with pytest.raises(ValidationError) as exc_info:
            file_size(large_file)

        assert "5 MB" in str(exc_info.value)

    def test_accepts_file_at_exact_limit(self):
        """Valor limite exacto (5 MB justo) no lanza excepcion."""
        exact_file = SimpleUploadedFile("exact.bin", b"\x00" * FILE_SIZE_LIMIT)

        try:
            file_size(exact_file)
        except ValidationError:
            pytest.fail("file_size lanzo ValidationError para un archivo exactamente en el limite")

    def test_accepts_file_below_limit(self):
        """Archivo por debajo del limite (1 MB) no lanza excepcion."""
        small_file = SimpleUploadedFile("small.bin", b"\x00" * 1_048_576)

        try:
            file_size(small_file)
        except ValidationError:
            pytest.fail("file_size lanzo ValidationError para un archivo de 1 MB")

    def test_rejects_file_well_above_limit(self):
        """Archivo de 15 MB (3x el limite) siempre lanza ValidationError."""
        huge_file = SimpleUploadedFile("huge.bin", b"\x00" * (FILE_SIZE_LIMIT * 3))

        with pytest.raises(ValidationError):
            file_size(huge_file)
