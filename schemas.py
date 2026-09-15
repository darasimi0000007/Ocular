from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid
import regex as re


class TaskAccepted(BaseModel):
    task_id: str
    status: str = "queued"


class TaskResult(BaseModel):
    task_id: str
    status: str  # PENDING | STARTED | SUCCESS | FAILURE
    result: dict | None = None



class PersonCreate(BaseModel):
    external_id: str = Field(min_length = 1, max_length = 64)
    first_name: str = Field(min_length = 1, max_length = 100)
    last_name: str = Field(min_length = 1, max_length = 100)

    @field_validator("external_id", "first_name", "last_name")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty or whitespace")
        return v


class PersonCreated(PersonCreate):
    person_id: uuid.UUID

    class Config():
        from_attributes = True










#pydantic schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    organization_id: uuid.UUID | None = None
    scopes: list[str] = []







class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 1)






# #schema for data validation for users
# class ModeratorCreate(BaseModel):
#     firstname: str
#     lastname: str
#     email: str
#     role: str
#     password: str




#first moderator signup schema for authentication
class ModeratorSignup(BaseModel):
    first_name: str = Field(min_length = 1, max_length = 50)
    last_name: str = Field(min_length = 1, max_length = 50)
    organization_name: str = Field(min_length = 1, max_length = 100)
    organization_slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("organization_slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", v):
            raise ValueError(
                "slug must be lowercase alphanumeric with single hyphens, e.g. 'riverside-academy'"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("password must contain at least one letter and one digit")
        return v



#response mode for moderator signup
class ModeratorCreated(BaseModel):
    moderator_id: uuid.UUID
    organization_id: uuid.UUID