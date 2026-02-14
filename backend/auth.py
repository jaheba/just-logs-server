import secrets
import os
import sys
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# JWT Secret Key - MUST be set via environment variable
SECRET_KEY = os.getenv("JLO_SECRET_KEY")

if not SECRET_KEY:
    # Check for legacy .secret_key file for backward compatibility
    SECRET_KEY_FILE = Path(__file__).parent / ".secret_key"
    if SECRET_KEY_FILE.exists():
        with open(SECRET_KEY_FILE, "r") as f:
            SECRET_KEY = f.read().strip()
        print("=" * 70)
        print("⚠️  WARNING: Using legacy .secret_key file")
        print("⚠️  Please migrate to environment variable for security:")
        print(f"⚠️  export JLO_SECRET_KEY={SECRET_KEY}")
        print("⚠️  Then delete the .secret_key file")
        print("=" * 70)
    else:
        # No secret key found - fail fast
        print("=" * 70)
        print("❌ CRITICAL: JLO_SECRET_KEY environment variable not set!")
        print("")
        print("Generate a secure secret key with:")
        print("  openssl rand -hex 32")
        print("")
        print("Then set it as an environment variable:")
        print("  export JLO_SECRET_KEY=your_generated_key_here")
        print("")
        print("For Docker deployments, add to docker-compose.yml:")
        print("  environment:")
        print("    - JLO_SECRET_KEY=${JLO_SECRET_KEY}")
        print("=" * 70)
        sys.exit(1)

# Use argon2 instead of bcrypt for Python 3.14 compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"], deprecated="auto", argon2__rounds=2
)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate a random API key"""
    return f"jlo_{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
