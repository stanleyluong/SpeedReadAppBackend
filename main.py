from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from extract import extract_text_from_pdf, extract_text_from_epub
import models
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Correct usage of CORSMiddleware
# Correct usage of CORSMiddleware
origins = [
    "http://localhost:8081",  # Allow requests from your frontend
    "https://speedreadappbackend.onrender.com"
    # Add other origins as needed, e.g., "https://yourdomain.com"
]
# origins=["*"]
app.add_middleware(
    CORSMiddleware,  # Just CORSMiddleware, not Middleware(...)
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],  # Adjust for production!
    allow_headers=["*"],  # Adjust for production!
)
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
    print('in upload book')

    # Log the received file details
    print(f"Received file: {file.filename}")
    print(f"File type: {file.content_type}")
    print(f"File size: {file.spool_max_size if hasattr(file, 'spool_max_size') else 'Unknown'}")

    # Check file type
    if file.filename.endswith(".pdf"):
        print('Processing PDF file...')
        text = extract_text_from_pdf(await file.read())
    elif file.filename.endswith(".epub"):
        print('Processing EPUB file...')
        text = extract_text_from_epub(await file.read())
    else:
        print('Invalid file type detected.')
        raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported")

    print(f"Text extracted from {file.filename}, length of text: {len(text)} characters")

    # Store in database
    try:
        new_book = models.Book(title=file.filename, text=text)
        print(f"Adding book: {new_book.title} to the database")
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        print(f"Book {new_book.title} added with ID: {new_book.id}")
    except Exception as e:
        print(f"Error while saving to database: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save book in database")

    return JSONResponse(content={"message": "Book uploaded successfully!", "title": new_book.title, "id": new_book.id})
# @app.post("/upload/")
# async def upload_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
#     print('in upload book')
#     # Check file type
#     if file.filename.endswith(".pdf"):
#         text = extract_text_from_pdf(await file.read())
#     elif file.filename.endswith(".epub"):
#         text = extract_text_from_epub(await file.read())
#     else:
#         raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported")
#
#     # Store in database
#     new_book = models.Book(title=file.filename, text=text)
#     db.add(new_book)
#     db.commit()
#     db.refresh(new_book)
#
#     return JSONResponse(content={"message": "Book uploaded successfully!", "title": new_book.title, "id": new_book.id})


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

@app.get("/test")
async def test_endpoint():
    return {"message": "Hello from FastAPI!"}