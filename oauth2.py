from fastapi import Depends, status, HTTPException
from routers import token as token_module
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
import database, models
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_moderator(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = token_module.verify_token(token, credentials_exception)

    moderator = db.query(models.Moderator).filter(
        models.Moderator.email == token_data.email
    ).first()
    if moderator is None:
        raise credentials_exception

    return moderator