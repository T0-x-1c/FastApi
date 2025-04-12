from sqlalchemy.orm import Session
from . import models, schemas
from .models import Book, Author

def get_all_book(db: Session):
    books = db.query(Book).all()
    return books

def create_book(book: schemas.BookCreate, db: Session):
    author = db.query(Author).filter(Author.name == book.author_name).first()
    if not author:
        author = Author(name=book.author_name)
        db.add(author)
        db.commit()
        db.refresh(author)

    db_book = Book(title=book.title, pages=book.pages, author_id = author.id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    return db_book

def get_book_by_author(author_name: str, db: Session):
    author = db.query(Author).filter(Author.name == author_name).first()
    if author:
        return author.books
    return None

def delete_book(author_name:str, book_title:str ,db: Session):
    book = db.query(Book).join(Author).filter(Author.name == author_name, Book.title == book_title).first()
    if book:
        db.delete(book)
        db.commit()
        return True
    return False

def update_book_pages(author_name:str, book_title:str, new_count_pages:int, db: Session):
    book = db.query(Book).filter(Book.title == book_title).first()
    if book:
        book.pages = new_count_pages
        db.commit()
        return True
    return False