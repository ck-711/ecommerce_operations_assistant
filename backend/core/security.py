from datetime import datetime, timedelta, timezone
import jwt
from backend.core.config import settings

def create_access_token(user_id: int, username: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({'sub': str(user_id), 'username': username, 'role': role, 'exp': exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
