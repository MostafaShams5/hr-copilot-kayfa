import os
import hmac
import hashlib
import time
import secrets
from typing import Tuple, Optional

# Secret key with enterprise environment fallback
SECRET_KEY = os.getenv("INTERVIEW_SECURITY_SALT", "KAYFA_ENTERPRISE_HMAC_SALT_KEY_991823A")
TOKEN_EXPIRY_SECONDS = 72 * 3600  # 72 hours window


def generate_assessment_tokens(candidate_id: str, assessment_id: str) -> Tuple[str, str]:
    """
    Generates two cryptographically signed tokens for Technical and HR tracks.
    Format: <track>_<candidateId>_<assessmentId>_<expiryTimestamp>_<entropy>_<hmacSignature>
    """
    entropy_tech = secrets.token_hex(8)
    entropy_hr = secrets.token_hex(8)
    exp = int(time.time()) + TOKEN_EXPIRY_SECONDS

    raw_tech = f"tech_{candidate_id}_{assessment_id}_{exp}_{entropy_tech}"
    raw_hr = f"hr_{candidate_id}_{assessment_id}_{exp}_{entropy_hr}"

    sig_tech = hmac.new(SECRET_KEY.encode("utf-8"), raw_tech.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    sig_hr = hmac.new(SECRET_KEY.encode("utf-8"), raw_hr.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    return f"{raw_tech}_{sig_tech}", f"{raw_hr}_{sig_hr}"


def verify_assessment_token(token: str) -> bool:
    """
    Validates token integrity, HMAC signature, and timestamp validity.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not token or not isinstance(token, str):
        return False

    parts = token.strip().split("_")
    if len(parts) < 6:
        return False

    sig = parts[-1]
    raw = "_".join(parts[:-1])
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    # Constant-time signature comparison
    if not hmac.compare_digest(sig, expected_sig):
        return False

    # Check expiration
    try:
        exp_timestamp = int(parts[3])
        if time.time() > exp_timestamp:
            return False
    except (ValueError, IndexError):
        return False

    return True


def extract_token_metadata(token: str) -> Optional[dict]:
    """Extracts claims from a valid token."""
    if not verify_assessment_token(token):
        return None
    parts = token.strip().split("_")
    return {
        "track": parts[0].upper(),
        "candidate_id": parts[1],
        "assessment_id": parts[2],
        "expires_at": int(parts[3])
    }