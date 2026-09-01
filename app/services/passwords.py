"""Password hashing via stdlib scrypt — no extra dependency needed for a
small app already keeping its dependency list to fastapi/sqlmodel/psycopg."""

import hashlib
import hmac
import os

_N = 2**14
_R = 8
_P = 1
_SALT_LEN = 16


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_LEN)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, n, r, p, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    derived = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p))
    return hmac.compare_digest(derived, expected)


# A hash of a password nobody will ever type, used to make failed logins for
# a nonexistent user (or one with no password set) take the same time as a
# wrong-password attempt against a real account — without this, the extra
# scrypt call only happening for real accounts would leak which emails/
# handles are registered via a timing side-channel.
DUMMY_HASH = hash_password(os.urandom(32).hex())
