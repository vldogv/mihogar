from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


class TokenData:
    def __init__(self, payload: dict):
        self.owner_id: Optional[str] = payload.get("owner_id")
        self.usuario_id: Optional[str] = payload.get("usuario_id")
        self.casa_id: Optional[str] = payload.get("casa_id")
        self.rol: str = payload.get("rol", "usuario")
        self.email: Optional[str] = payload.get("email")

    @property
    def is_owner(self) -> bool:
        return self.owner_id is not None and self.casa_id is None

    @property
    def is_admin(self) -> bool:
        return self.rol == "administrador"

    @property
    def effective_user_id(self) -> str:
        return self.usuario_id or self.owner_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> TokenData:
    payload = decode_token(credentials.credentials)
    return TokenData(payload)


async def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.rol not in ("administrador", "owner", "propietario"):
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return current_user


async def require_admin_or_encargado(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    if current_user.rol not in ("administrador", "encargado", "owner", "propietario"):
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador o encargado")
    return current_user
