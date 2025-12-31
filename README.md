# Index Documents Project

## תיאור
מודול Python ליצירת Embeddings ממסמכי PDF ו-DOCX ושמירתם במסד PostgreSQL.

### יכולות:
- חילוץ טקסט נקי מ-PDF ו-DOCX
- חלוקת הטקסט למקטעים (Chunks) בשלוש אסטרטגיות:
  - fixed → גודל קבוע עם חפיפה
  - sentence → חלוקה לפי משפטים
  - paragraph → חלוקה לפי פסקאות
- יצירת Embeddings לכל מקטע באמצעות Google Gemini
- שמירה למסד PostgreSQL

---

## התקנה

1. הורד את הפרויקט או שכפל מ-GitHub
2. התקן את התלויות
3. צור קובץ .env עם משתני הסביבה
```bash
git clone https://github.com/username/index_documents_project.git
cd index_documents_project

pip install -r requirements.txt

GEMINI_API_KEY=your_google_gemini_api_key_here
POSTGRES_URL=postgresql://username:password@host:port/dbname
