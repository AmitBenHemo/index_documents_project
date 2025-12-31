# index_documents.py

import os
import re
from pathlib import Path
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from docx import Document
import PyPDF2


class DocumentIndexer:
    def __init__(self, db_url=None, api_key=None):
        """
        אתחול מחלקת אינדקסר
        db_url: מחרוזת חיבור ל-PostgreSQL
        api_key: מפתח API ל-Gemini
        """
        load_dotenv()
        self.db_url = db_url or os.getenv("POSTGRES_URL")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.db_url or not self.api_key:
            raise ValueError("Missing POSTGRES_URL or GEMINI_API_KEY")

    # -----------------------------
    # קריאת קבצים
    # -----------------------------
    def read_file(self, file_path):
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self._read_pdf(file_path)
        elif ext == ".docx":
            return self._read_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _read_docx(self, file_path):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip() != ""])

    def _read_pdf(self, file_path):
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()

    # -----------------------------
    # חלוקת טקסט (Chunking)
    # -----------------------------
    def chunk_text(self, text, strategy="paragraph", chunk_size=500, overlap=50):
        """
        strategy: "fixed", "sentence", "paragraph"
        """
        if strategy == "fixed":
            return self._chunk_fixed(text, chunk_size, overlap)
        elif strategy == "sentence":
            return self._chunk_sentence(text)
        elif strategy == "paragraph":
            return self._chunk_paragraph(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def _chunk_fixed(self, text, chunk_size=500, overlap=50):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def _chunk_sentence(self, text):
        sentences = re.split(r'(?<=[.!?]) +', text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_paragraph(self, text):
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    # -----------------------------
    # יצירת Embeddings
    # -----------------------------
    def create_embedding(self, text):
        url = "https://api.generativeai.googleapis.com/v1beta2/models/textembedding-gecko-001:embedText"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"input": text}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    # -----------------------------
    # שמירה ב-PostgreSQL
    # -----------------------------

    def save_chunks_to_db(self, chunks, filename, strategy):
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        # יצירת טבלה אם לא קיימת
        create_table_query = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            chunk_text TEXT,
            embedding FLOAT8[],
            filename TEXT,
            strategy_split TEXT,
            created_at TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        now = datetime.now()
        values = [(chunk, self.create_embedding(chunk), filename, strategy, now) for chunk in chunks]

        insert_query = """
        INSERT INTO document_chunks (chunk_text, embedding, filename, strategy_split, created_at)
        VALUES %s
        """
        execute_values(cursor, insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()


    # -----------------------------
    # פונקציה ראשית לאינדוקס מסמך
    # -----------------------------
    def index_document(self, file_path, strategy="paragraph"):
        text = self.read_file(file_path)
        chunks = self.chunk_text(text, strategy=strategy)
        self.save_chunks_to_db(chunks, Path(file_path).name, strategy)
        print(f"Document '{file_path}' indexed successfully with {len(chunks)} chunks.")


# -----------------------------
# דוגמת שימוש
# -----------------------------
if __name__ == "__main__":
    indexer = DocumentIndexer()
    indexer.index_document("sample_files/example1.docx", strategy="paragraph")
