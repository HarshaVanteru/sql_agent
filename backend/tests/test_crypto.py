"""Credential encryption.

Connected-database passwords are reversibly encrypted rather than hashed: the
agent has to present the real password to the target server. The point is that
a dump of Redis does not hand over every system a visitor has connected.
"""
import pytest
from cryptography.fernet import Fernet

from app.core.crypto import decrypt, encrypt


def test_round_trip():
    assert decrypt(encrypt("hunter2")) == "hunter2"


@pytest.mark.parametrize(
    "secret",
    ["", "p@ssw0rd!", "unicode-πásswörd", "x" * 4096, "with\nnewlines\tand\ttabs"],
)
def test_round_trip_survives_awkward_passwords(secret: str):
    assert decrypt(encrypt(secret)) == secret


def test_ciphertext_does_not_contain_the_plaintext():
    """The whole point: a Redis dump must not be a password list."""
    assert "hunter2" not in encrypt("hunter2")


def test_the_same_password_encrypts_differently_each_time():
    """Fernet includes a random IV, so equal passwords are not equal ciphertexts."""
    assert encrypt("hunter2") != encrypt("hunter2")


def test_a_credential_from_another_key_is_refused():
    """Rotating CREDENTIALS_KEY makes stored connections unreadable, not silently wrong."""
    foreign = Fernet(Fernet.generate_key()).encrypt(b"hunter2").decode()

    with pytest.raises(ValueError):
        decrypt(foreign)


def test_corrupt_ciphertext_is_refused():
    with pytest.raises(ValueError):
        decrypt("not-a-fernet-token")
