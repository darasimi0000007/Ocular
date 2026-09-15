from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional
import schemas
from config import settings



SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30




def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        org_id = payload.get("org_id")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, organization_id = org_id)
        return token_data
    
    except JWTError:
        raise credentials_exception