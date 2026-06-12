import pytest
from unittest.mock import patch, MagicMock
from core.config import get_settings
from core.firebase import verify_firebase_token
from core.security import encrypt_token, decrypt_token


def test_firebase_config_path():
    """Verify FIREBASE_CREDENTIALS_PATH is present in settings."""
    settings = get_settings()
    assert hasattr(settings, "FIREBASE_CREDENTIALS_PATH")
    assert settings.FIREBASE_CREDENTIALS_PATH == "socialpx-admin.json"


@patch("core.firebase.auth.verify_id_token")
def test_verify_firebase_token_success(mock_verify_id_token):
    """Happy path: valid token returns decoded claims."""
    mock_decoded = {"uid": "test_firebase_uid", "email": "test@example.com"}
    mock_verify_id_token.return_value = mock_decoded

    result = verify_firebase_token("mock_token_123")

    mock_verify_id_token.assert_called_once_with("mock_token_123")
    assert result == mock_decoded


@patch("core.firebase.auth.verify_id_token")
def test_verify_firebase_token_invalid(mock_verify_id_token):
    """Error path: expired or malformed token raises an exception."""
    mock_verify_id_token.side_effect = ValueError("Token expired")

    with pytest.raises(ValueError, match="Token expired"):
        verify_firebase_token("expired_token")


def test_encrypt_decrypt_roundtrip():
    """Fernet encryption round-trips correctly."""
    original = "sensitive_data_12345"
    encrypted = encrypt_token(original)
    assert encrypted != original
    assert decrypt_token(encrypted) == original
