from fastapi import APIRouter,Depends, HTTPException,Path
from pydantic import BaseModel,Field
from starlette import status
from typing import Annotated
from sqlalchemy.orm import Session
from models import Todos, Users
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


@router.get("/",status_code=status.HTTP_200_OK)
async def get_user(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication failed")
    return db.query(Users).filter(Users.id==user.get("id")).first()

@router.put("/password",status_code=status.HTTP_204_NO_CONTENT)
async def update_password(user_verfication:UserVerification,user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication failed")
    
    user_model = db.query(Users).filter(Users.id==user.get("id")).first()

    if not bcrypt_context.verify(user_verfication.password,user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Incorrect password")
    
    user_model.hashed_password = bcrypt_context.hash(user_verfication.new_password)

    db.add(user_model)
    db.commit()