from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from extract import extract_text_from_pdf, extract_text_from_epub
import models

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency: Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 📌 Upload file endpoint (PDF/EPUB)
@app.post("/upload/")
async def upload_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(await file.read())
    elif file.filename.endswith(".epub"):
        text = extract_text_from_epub(await file.read())
    else:
        raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported")

    # Store in database
    new_book = models.Book(title=file.filename, text=text)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return JSONResponse(content={"message": "Book uploaded successfully!", "title": new_book.title, "id": new_book.id})


# 📌 Fetch all books
@app.get("/books/")
def get_all_books(db: Session = Depends(get_db)):
    books = db.query(models.Book).all()
    return [{"id": book.id, "title": book.title} for book in books]


# 📌 Fetch a single book by ID
@app.get("/books/{book_id}")
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return {"id": book.id, "title": book.title, "content": book.text}


# 📌 Save last read position
@app.patch("/books/{book_id}/resume")
def update_last_read_position(book_id: int, last_position: int = Query(..., description="Last position read"),
                              db: Session = Depends(get_db)):
    book_progress = db.query(models.ReadingProgress).filter(models.ReadingProgress.book_id == book_id).first()

    if book_progress:
        book_progress.position = last_position
    else:
        book_progress = models.ReadingProgress(book_id=book_id, position=last_position)
        db.add(book_progress)

    db.commit()
    return {"message": "Last read position updated", "book_id": book_id, "last_read_position": last_position}