"""Password hashing via pwdlib (the maintained passlib successor).

Uses bcrypt with cost factor 12 (NFR-02). ``verify_password`` is also used with the
module-level ``DUMMY_HASH`` on the no-such-user login path so an unknown email costs
the same wall-clock time as a real bcrypt comparison — closing the account-enumeration
timing side channel (AC-AUTH-05 / EC-AUTH-LGN-05).
"""

from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

# bcrypt, cost 12. Structured as a tuple so additional/upgraded hashers can be added
# later (pwdlib verifies against any in the list, hashes with the first).
_password_hash = PasswordHash((BcryptHasher(rounds=12),))


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


# Precomputed once at import; compared against when no user row is found so the
# failed-login response time matches the real-user path.
DUMMY_HASH = hash_password("learnflow-timing-equalizer")


def verify_dummy() -> None:
    """Burn the same bcrypt time as a real verify, discarding the result."""
    verify_password("not-the-password", DUMMY_HASH)
