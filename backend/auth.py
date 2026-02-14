import secrets
import os
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuration
# Generate or load a persistent secret key
SECRET_KEY_FILE = Path(__file__).parent / ".secret_key"


def get_or_create_secret_key() -> str:
    """Get existing secret key or create a new one"""
    if SECRET_KEY_FILE.exists():
        with open(SECRET_KEY_FILE, "r") as f:
            return f.read().strip()
    else:
        # Generate new secret key
        new_key = secrets.token_urlsafe(32)
        with open(SECRET_KEY_FILE, "w") as f:
            f.write(new_key)
        print(f"Generated new secret key at {SECRET_KEY_FILE}")
        return new_key


SECRET_KEY = get_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

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
