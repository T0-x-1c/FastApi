from sqlalchemy.orm import Session
from . import models, schemas

def get_all_book(db: Session):
    books = db.query(models.Book).all()
    return books
