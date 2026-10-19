# Doc Chatbot (RAG)

Chatbot tanya jawab dokumen PDF berbasis RAG (Retrieval-Augmented Generation). User mengunggah PDF ke sebuah sesi, lalu bertanya. Jawaban dibuat LLM hanya dari isi dokumen, lengkap dengan nomor halaman sumber.

## Fitur

- Sesi terisolasi dengan ID acak (UUIDv4)
- Upload PDF dengan validasi ukuran
- Ekstraksi teks per halaman
- Chunking per kalimat dengan overlap, membawa metadata halaman
- Embedding lokal multilingual (data tidak dikirim ke pihak luar)
- Penyimpanan dan pencarian vector dengan PostgreSQL + pgvector
- Jawaban LLM (Gemini) dengan citation `(hlm. N)` dan penolakan jika jawaban tidak ada di dokumen

## Arsitektur

```
Upload PDF
  → validasi (ukuran)
  → simpan sementara di storage/sessions/{session_id}/
  → ekstrak teks per halaman
  → chunking (per kalimat, overlap)
  → embedding (multilingual-e5-small, 384 dimensi)
  → simpan chunk + vector di PostgreSQL (pgvector)
  → hapus file PDF asli

Tanya
  → embed pertanyaan
  → similarity search (cosine, filter session_id) → top-k chunk
  → buang chunk di bawah MIN_SCORE
  → susun context + pertanyaan → LLM
  → jawaban + sumber halaman
```

## Stack

| Komponen | Teknologi |
|---|---|
| API | FastAPI |
| Parsing PDF | PyMuPDF |
| Embedding | sentence-transformers, `intfloat/multilingual-e5-small` |
| Database | PostgreSQL 16 + pgvector |
| LLM | Google Gemini (`google-genai`) |
| Infrastruktur dev | Docker Compose (database) |

## Struktur Project

```
doc-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py          # endpoint API
│   ├── db.py            # koneksi dan skema database
│   ├── pdf_parser.py    # ekstraksi teks per halaman
│   ├── chunkers.py      # chunking per kalimat
│   └── embedder.py      # embedding passage dan query
├── storage/sessions/    # file sementara (di-gitignore)
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

## Menjalankan

### Prasyarat

- Python 3.12
- Docker dan Docker Compose
- API key Gemini

### 1. Install dependensi

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt`:

```
fastapi
uvicorn[standard]
python-multipart
pymupdf
sentence-transformers
psycopg[binary]
pgvector
python-dotenv
numpy
pydantic
google-genai
```

### 2. Konfigurasi environment

Buat `.env` di root project:

```
DB_PASSWORD=ganti_dengan_password_alfanumerik
DATABASE_URL=postgresql://app:ganti_dengan_password_alfanumerik@localhost:5432/docchat
GEMINI_API_KEY=isi_api_key
```

`DB_PASSWORD` dan password di dalam `DATABASE_URL` harus sama. Gunakan password alfanumerik agar tidak perlu URL-encode.
```

### 3. Jalankan database

```bash
docker compose up -d
```

`docker-compose.yml`:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: docchat
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
volumes:
  pgdata:
```

### 4. Jalankan API

```bash
uvicorn app.main:app --reload --reload-dir app
```

Pada startup pertama, tabel dibuat otomatis dan model embedding diunduh. Dokumentasi interaktif tersedia di `http://localhost:8000/docs`.

## API

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/sessions` | Membuat sesi baru, mengembalikan `session_id` |
| POST | `/sessions/{session_id}/upload` | Upload PDF (multipart, field `file`) |
| POST | `/sessions/{session_id}/search` | Pencarian chunk relevan (tanpa LLM) |
| POST | `/sessions/{session_id}/ask` | Tanya jawab dengan LLM dan citation |

### Contoh

```bash
# 1. Buat sesi
curl -X POST http://localhost:8000/sessions
# {"session_id": "..."}

# 2. Upload PDF
curl -X POST http://localhost:8000/sessions/<session_id>/upload \
  -F "file=@dokumen.pdf"
# {"document_id": 1, "page_with_text": 38, "total_chunks": 55}

# 3. Cari chunk relevan
curl -X POST http://localhost:8000/sessions/<session_id>/search \
  -H "Content-Type: application/json" \
  -d '{"query": "apa fungsi perintah SELECT?", "k": 5}'

# 4. Tanya
curl -X POST http://localhost:8000/sessions/<session_id>/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "apa fungsi perintah SELECT?", "k": 5}'
# {"answer": "... (hlm. 12)", "sources": [{"page": 12, "score": 0.83}]}
```

Body `search` dan `ask`:

| Field | Tipe | Aturan |
|---|---|---|
| `query` | string | 1-500 karakter |
| `k` | integer | jumlah chunk teratas, 1-20, default 5 |

### Kode status

| Kode | Arti |
|---|---|
| 400 | Bukan PDF, atau PDF tidak bisa dibaca / melebihi batas halaman |
| 404 | Sesi tidak ditemukan atau sudah kedaluwarsa |
| 413 | File lebih dari 20 MB |
| 422 | Input tidak valid, atau PDF tanpa teks (hasil scan) |

## Konfigurasi di Kode

| Parameter | Lokasi | Keterangan |
|---|---|---|
| `MAX_SIZE` | `main.py` | Batas ukuran upload (20 MB) |
| `MAX_PAGES` | `pdf_parser.py` | Batas halaman per PDF (200) |
| `size`, `overlap` | `chunkers.py` | Panjang chunk dan overlap, dalam karakter |
| `MIN_SCORE` | `main.py` | Ambang skor minimum chunk. Cosine similarity maksimal 1, jadi nilainya harus antara 0 dan 1. Tentukan dari skor nyata di `/search` (pertanyaan relevan vs tidak relevan) |
| `LLM_MODEL` | `main.py` | Nama model Gemini. Sesuaikan dengan daftar model terbaru |
| `MODEL_NAME` | `embedder.py` | Model embedding |

## Next To-do

- **Penghapusan data belum otomatis.** `expires_at` sudah memblokir akses ke sesi setelah 24 jam, tetapi baris database, vector, dan folder sesi belum dihapus secara fisik. Penghapusan manual lewat SQL:
  ```sql
  DELETE FROM sessions WHERE id = '<session_id>';
  ```
  Lalu hapus folder `storage/sessions/<session_id>`. Endpoint hapus sesi dan job cleanup TTL belum dibuat.
- Belum ada autentikasi. Siapa pun yang memegang `session_id` bisa mengakses sesinya.
- Belum ada rate limit.
- PDF hasil scan (tanpa teks) ditolak, belum ada OCR.
- Parsing PDF dan embedding bersifat blocking di dalam endpoint `async`, sehingga memblokir request lain selama proses berjalan.
- Chunking memakai karakter, bukan token, dan menggabungkan baris sehingga format blok kode atau tabel bisa rusak.
- Chunk tidak melewati batas halaman.
- Potongan dokumen dikirim ke API Gemini. Untuk dokumen sensitif, gunakan tier berbayar atau model lokal.
- Belum ada pencarian hybrid, reranking, streaming jawaban, maupun evaluasi kualitas retrieval.