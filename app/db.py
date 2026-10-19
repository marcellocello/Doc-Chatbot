import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;;

CREATE TABLE IF NOT EXISTS sessions(
    id          TEXT PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS documents(
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks(
    id          SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page        INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunk_session_idx ON chunks(session_id);
"""

def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(SCHEMA)

def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn