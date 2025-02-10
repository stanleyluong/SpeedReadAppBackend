import os
import sys

import pdfminer.high_level
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import html

# 📌 Extract text from PDF
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfminer."""
    try:
        text = pdfminer.high_level.extract_text(pdf_path)
        print(f"Extracted PDF preview: {text[:100]}")  # Debugging: Show first 100 chars
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

# 📌 Extract text from EPUB (removes ALL HTML)
def extract_text_from_epub(epub_bytes):
    """Extracts pure text from an EPUB, ensuring ALL HTML is stripped."""
    temp_filename = "temp.epub"
    print("📚 [DEBUG] Running extract_text_from_epub", file=sys.stderr, flush=True)  # Ensure print appears immediately
    try:
        # Save EPUB bytes to a temporary file
        with open(temp_filename, "wb") as f:
            f.write(epub_bytes)

        book = epub.read_epub(temp_filename)
        text_content = []

        for item in book.items:
            if isinstance(item, epub.EpubHtml):
                raw_html = item.get_body_content().decode("utf-8", errors="ignore")  # Decode bytes to text
                soup = BeautifulSoup(raw_html, "html.parser")

                # Completely remove ALL HTML tags
                for tag in soup.find_all(True):
                    tag.unwrap()  # Removes tags but keeps text content

                # Convert HTML entities (e.g., &nbsp; -> space, &amp; -> &)
                clean_text = html.unescape(soup.get_text(separator=" ", strip=True))

                # Extra cleaning: remove multiple spaces, weird symbols, and blank lines
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Normalize spaces
                clean_text = re.sub(r'[\r\n]+', '\n', clean_text)  # Normalize line breaks
                clean_text = re.sub(r'[^ -~]', '', clean_text)  # Remove non-printable characters

                if clean_text:  # Only add non-empty sections
                    text_content.append(clean_text)

        extracted_text = "\n\n".join(text_content)  # Join all sections with spacing

        # 🔹 Debugging: Print first 100 characters to verify
        print(f"Extracted EPUB preview: {extracted_text[:100]}")

    except Exception as e:
        print(f"Error extracting EPUB text: {e}")
        return None  # Return None if extraction fails

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)  # Cleanup temp file

    return extracted_text if extracted_text else "No readable text found."