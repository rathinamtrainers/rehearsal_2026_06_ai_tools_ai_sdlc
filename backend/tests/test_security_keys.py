"""RS256 key-resolution branches in app/security.py.

The default suite runs on HS256 (shared secret). These tests flip the algorithm
to RS256 and assert the private/public key files are read — and that a missing
path is a hard configuration error. _signing_key/_verify_key are lru_cached, so
each test clears the cache before and the fixture clears it after to avoid
leaking RS256 state into the HS256 tests.
"""
from __future__ import annotations

import pytest

from app import security
from app.config import settings


@pytest.fixture(autouse=True)
def _clear_key_cache():
    security._signing_key.cache_clear()
    security._verify_key.cache_clear()
    yield
    security._signing_key.cache_clear()
    security._verify_key.cache_clear()


def test_signing_key_rs256_requires_private_path(monkeypatch):
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_private_key_path", None)
    with pytest.raises(RuntimeError, match="JWT_PRIVATE_KEY_PATH"):
        security._signing_key()


def test_signing_key_rs256_reads_private_file(monkeypatch, tmp_path):
    key_file = tmp_path / "private.pem"
    key_file.write_text("PRIVATE-KEY-CONTENTS")
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_private_key_path", str(key_file))
    assert security._signing_key() == "PRIVATE-KEY-CONTENTS"


def test_verify_key_rs256_requires_public_path(monkeypatch):
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_public_key_path", None)
    with pytest.raises(RuntimeError, match="JWT_PUBLIC_KEY_PATH"):
        security._verify_key()


def test_verify_key_rs256_reads_public_file(monkeypatch, tmp_path):
    key_file = tmp_path / "public.pem"
    key_file.write_text("PUBLIC-KEY-CONTENTS")
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_public_key_path", str(key_file))
    assert security._verify_key() == "PUBLIC-KEY-CONTENTS"
