from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Annotated, Union
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from db.database import SessionLocal, engine
from db import models, schemas, crud

SECRET_KEY = "19109197bd5e7c289b92b2b355083ea26c71dee2085ceccc19308a7291b2ea06"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Визначення аутентифікації через OAuth2BearerToken
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Залежність
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


all_books = {
    "Джордж Оруелл": [["1984", 328], ["Колгосп тварин", 112]],
    "Стівен Кінг": [["Воно", 1138], ["Сяйво", 447]],
    "Артур Конан Дойл": [["Пригоди Шерлока Холмса", 307], ["Собака Баскервілів", 256]],
    "Джоан Роулінг": [["Гаррі Поттер і філософський камінь", 223], ["Гаррі Поттер і таємна кімната", 251]],
    "Лев Толстой": [["Війна і мир", 1225], ["Анна Кареніна", 864]]
            }

def token_create(data: dict):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

@app.post("/token")
async def token_get(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = crud.check_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = token_create(data={"sub": user.login})
    return {"access_token": token, "token_type": "bearer"}

class Book(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=3, max_length=200)
    pages: int = Field(..., gt=10)

@app.get("/")
async def get_all_books(db: Session = Depends(get_db)):
    """
    Повертає список усіх книг бібліотеки
    """
    return crud.get_all_book(db)

@app.post("/add_book")
async def add_new_book(book:schemas.BookCreate,
                    token: Annotated[str, Depends(oauth2_scheme)],
                    db: Session = Depends(get_db)):
    """
    Додає нову книгу
    """
    new_book = crud.create_book(book, db)
    return {"message": "Книга успішно створена", "book": new_book}

@app.get("/author/{author}")
async def get_author_book(author:str, db: Session = Depends(get_db)):
    """
    Знаходить всі книги автора
    """
    books = crud.get_book_by_author(author, db)
    if books:
        return books
    else:
        return {"message": "Такого автора немає"}
    
@app.put("/{author}/{book_title}")
async def update_book_title(author: str, 
                            title: str, 
                            pages: int = Query(gt=10, title="Нова к-сть сторінок")):
    """
    Оновлює назву книги
    """
    if author in all_books:
        for book in all_books[author]:
            if book[0] == title:
                book[1] = pages
                return {"message":"к-сть сторінок оновлено"}
            
    return {"message":"Книги не знайденно"}
    
@app.delete('/{author}/{book_title}')
async def delete_book(author:str, book_title:str, db: Session = Depends(get_db)):
    """
    Видаляє книгу
    """
    if crud.delete_book(author, book_title, db):        
        return {"message":"Книга видалина"}
            
    return {"message":"Книги не знайденно"}


