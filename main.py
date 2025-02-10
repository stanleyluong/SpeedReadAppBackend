from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
import pdfminer.high_level
from ebooklib import epub
import sqlite3
import os
from extract import extract_text_from_pdf, extract_text_from_epub

app = FastAPI()

# Database setup
DB_FILE = "books.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            last_read_position INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable fetching results as dictionaries
    return conn


# 📌 Upload file endpoint (PDF/EPUB)
@app.post("/upload/")
async def upload_book(file: UploadFile = File(...)):
    # Check file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(await file.read())
    elif file.filename.endswith(".epub"):
        text = extract_text_from_epub(await file.read())
    else:
        raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported")

    # Store in database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO books (title, content) VALUES (?, ?)", (file.filename, text))
    conn.commit()
    conn.close()

    return JSONResponse(content={"message": "Book uploaded successfully!", "title": file.filename})



# 📌 Fetch all books
@app.get("/books/")
def get_all_books():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, last_read_position FROM books")
    books = c.fetchall()
    conn.close()

    return [{"id": book["id"], "title": book["title"], "last_read_position": book["last_read_position"]} for book in books]


# 📌 Fetch a single book by ID
@app.get("/books/{book_id}")
def get_book(book_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = c.fetchone()
    conn.close()

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return {
        "id": book["id"],
        "title": book["title"],
        "content": book["content"],
        "last_read_position": book["last_read_position"]
    }


# 📌 Save last read position
@app.patch("/books/{book_id}/resume")
def update_last_read_position(book_id: int, last_position: int = Query(..., description="Last position read")):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE books SET last_read_position = ? WHERE id = ?", (last_position, book_id))
    conn.commit()
    conn.close()

    return {"message": "Last read position updated", "book_id": book_id, "last_read_position": last_position}