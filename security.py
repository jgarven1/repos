"""
Security utilities for Plaud Transcripts
-----------------------------------------
- All sensitive files stored in ~/Library/Application Support/Plaud/
  with owner-only (600/700) permissions
- Session files encrypted with Fernet; key stored in macOS Keychain
- Touch ID / device-password authentication via LocalAuthentication
- Automatic migration of old plain-text session files
"""

import json
import os
import pathlib
import threading

APP_SUPPORT = pathlib.Path.home() / "Library" / "Application Support" / "Plaud"

_KEYCHAIN_SERVICE = "com.plaud.transcripts"
_KEYCHAIN_USER    = "session_encryption_key"


# ---------------------------------------------------------------------------
# Directory + path helpers
# ---------------------------------------------------------------------------

def ensure_dirs():
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    os.chmod(APP_SUPPORT, 0o700)


def session_path(account="default"):
    ensure_dirs()
    if account == "default":
        return APP_SUPPORT / ".plaud_session.json"
    return APP_SUPPORT / f".plaud_session_{account}.json"


def transcripts_path(account="default"):
    if account == "default":
        return APP_SUPPORT / "transcripts"
    return APP_SUPPORT / f"transcripts_{account}"


def exported_log_path(account="default"):
    return transcripts_path(account) / ".exported"


def get_accounts():
    ensure_dirs()
    accounts = []
    if (APP_SUPPORT / ".plaud_session.json").exists():
        accounts.append("default")
    for f in sorted(APP_SUPPORT.glob(".plaud_session_*.json")):
        accounts.append(f.stem[len(".plaud_session_"):])
    return accounts


def set_secure_permissions(path):
    """Restrict a file to owner read/write only (chmod 600)."""
    os.chmod(path, 0o600)


# ---------------------------------------------------------------------------
# Keychain + Fernet encryption
# ---------------------------------------------------------------------------

def _get_or_create_key():
    """Retrieve encryption key from Keychain; generate and store if absent."""
    import keyring
    from cryptography.fernet import Fernet

    key = keyring.get_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USER)
    if not key:
        key = Fernet.generate_key().decode()
        keyring.set_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USER, key)
    return key.encode()


def encrypt_session(data_dict, path):
    """Encrypt a session dict and write it to path with secure permissions."""
    from cryptography.fernet import Fernet
    token = Fernet(_get_or_create_key()).encrypt(json.dumps(data_dict).encode())
    path = pathlib.Path(path)
    path.write_bytes(token)
    set_secure_permissions(path)


def decrypt_session(path):
    """
    Decrypt and return a session dict.
    Also handles legacy plain-text JSON — re-saves it encrypted automatically.
    """
    from cryptography.fernet import Fernet, InvalidToken
    path = pathlib.Path(path)
    raw = path.read_bytes()

    try:
        return json.loads(Fernet(_get_or_create_key()).decrypt(raw).decode())
    except (InvalidToken, Exception):
        # Try treating it as plain JSON (old format) and upgrade it
        try:
            data = json.loads(raw.decode())
            encrypt_session(data, path)   # re-save encrypted
            return data
        except Exception:
            raise ValueError(f"Cannot read session file: {path}")


# ---------------------------------------------------------------------------
# Touch ID / device-password authentication
# ---------------------------------------------------------------------------

def authenticate(reason="Open Plaud Transcripts"):
    """
    Prompt for Touch ID or the device login password via macOS
    LocalAuthentication.  Returns (success: bool, error: str | None).

    LAPolicyDeviceOwnerAuthentication tries Touch ID first and
    automatically falls back to the macOS password prompt, so a
    separate password dialog is not needed.
    """
    try:
        import LocalAuthentication   # pyobjc-framework-LocalAuthentication
    except ImportError:
        return False, "pyobjc-framework-LocalAuthentication is not installed"

    ctx = LocalAuthentication.LAContext.alloc().init()
    can_auth, err = ctx.canEvaluatePolicy_error_(
        LocalAuthentication.LAPolicyDeviceOwnerAuthentication, None
    )
    if not can_auth:
        return False, str(err) if err else "Authentication not available on this device"

    done   = threading.Event()
    result = [False, None]

    def reply(success, error):
        result[0] = bool(success)
        result[1] = str(error) if error else None
        done.set()

    ctx.evaluatePolicy_localizedReason_reply_(
        LocalAuthentication.LAPolicyDeviceOwnerAuthentication,
        reason,
        reply,
    )
    done.wait(timeout=60)
    return result[0], result[1]


# ---------------------------------------------------------------------------
# Migration — move old plain-text sessions to Application Support
# ---------------------------------------------------------------------------

def migrate_old_files(old_dir):
    """
    Find any .plaud_session*.json files in old_dir, encrypt them, move
    them to Application Support, and remove the originals.
    Returns a list of migrated filenames.
    """
    old_dir  = pathlib.Path(old_dir)
    migrated = []
    ensure_dirs()

    for old_file in sorted(old_dir.glob(".plaud_session*.json")):
        new_path = APP_SUPPORT / old_file.name
        if new_path.exists():
            continue
        try:
            data = json.loads(old_file.read_text())
            encrypt_session(data, new_path)
            old_file.unlink()
            migrated.append(old_file.name)
        except Exception:
            pass

    return migrated
