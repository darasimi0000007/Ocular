from passlib.context import CryptContext
import hashlib


pwd_cxt = CryptContext(schemes = ["argon2"], deprecated = "auto")   
"""argon2 is more secure than bcrypt so it is adopted for future projects"""


class Hash():
    def bcrypt(self, password: str):
        # Hash with SHA256 first to handle long passwords
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return pwd_cxt.hash(password_hash)
    




    
    def verify(self, plain_password, hashed_password):
        # hash the plain password with SHA256 before verifying
        plain_password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        #compare user input password with the hashed password in the database
        return pwd_cxt.verify(plain_password_hash, hashed_password)