from sqlalchemy.orm import Session
import models

def create_book(db: Session, title: str, text: str):
    book = models.Book(title=title, text=text)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def get_books(db: Session):
    return db.query(models.Book).all()

def get_book_text(db: Session, book_id: int):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    return book.text if book else None

def save_progress(db: Session, book_id: int, position: int):
    progress = db.query(models.ReadingProgress).filter(models.ReadingProgress.book_id == book_id).first()
    if progress:
        progress.position = position
    else:
        progress = models.ReadingProgress(book_id=book_id, position=position)
        db.add(progress)
    db.commit()
    return progress

def get_progress(db: Session, book_id: int):
    progress = db.query(models.ReadingProgress).filter(models.ReadingProgress.book_id == book_id).first()
    return progress.position if progress else 0