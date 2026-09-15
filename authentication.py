from fastapi import APIRouter, Depends, status, HTTPException
import schemas, database, models, hashing
from database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from routers import token
from fastapi.security import OAuth2PasswordRequestForm

router =APIRouter(
    prefix = "/auth",
    tags=["Authentication"]
)


@router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):


    #iltering out the user based on the email he put in as the username
    user_name_checking = db.query(models.Moderator).filter(models.Moderator.email == request.username).first()

    #checking if the user exists in the models.Modderator databsase table
    if not user_name_checking:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Invalid credentials")
    



    #cross-checking password the user put in with the hashed password stored in the database
    password_checking = hashing.Hash().verify(request.password, user_name_checking.password)

    #checking to see if the password of the user is correct by comparing password with saved hashed password in the database
    if not password_checking:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Invalid credentials")
    




    #generate jwt token and return it to the user if the credentials are correct. This is for authentication and authorization
    access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token.create_access_token( data={"sub":user_name_checking.email, "org_id": str(user_name_checking.organization_id)} )
    


    return schemas.Token(access_token=access_token, token_type="bearer")