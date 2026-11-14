from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from app.config import get_settings
from app.errors import ApiError

password_hasher = PasswordHasher()
ACCESS_SECONDS = 15 * 60
REFRESH_SECONDS = 7 * 24 * 60 * 60


def verify_password(encoded: str, password: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def utcnow():
    return datetime.now(timezone.utc)


def encode_token(user_id: uuid.UUID, kind: str):
    now = utcnow()
    expires = now + timedelta(seconds=ACCESS_SECONDS if kind == 'access' else REFRESH_SECONDS)
    token = jwt.encode({'sub': str(user_id), 'type': kind, 'jti': str(uuid.uuid4()), 'iat': now, 'exp': expires},
                       get_settings().jwt_secret.get_secret_value(), algorithm='HS256')
    return token, expires


def decode_token(token: str, kind: str):
    try:
        claims = jwt.decode(token, get_settings().jwt_secret.get_secret_value(), algorithms=['HS256'],
                            options={'require': ['sub', 'exp', 'iat', 'jti', 'type']})
        if claims['type'] != kind:
            raise ValueError('Sai loại token')
        return uuid.UUID(claims['sub'])
    except (jwt.PyJWTError, ValueError, TypeError):
        raise ApiError(401, 'UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.') from None


def token_hash(token: str):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
