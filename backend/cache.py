import sqlite3
import hashlib
import os

DB_PATH = "cache.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def is_url_processed(url: str) -> bool:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM processed_urls WHERE url_hash = ?", (url_hash,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def mark_url_processed(url: str, title: str, subcategory: str, poster_path: str = None):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO processed_urls (url_hash, title, subcategory, poster_path) VALUES (?, ?, ?, ?)",
              (url_hash, title, subcategory, poster_path))
    conn.commit()
    conn.close()

def get_image_cache_path(cache_key: str) -> str:
    os.makedirs("image_cache", exist_ok=True)
    return f"image_cache/{cache_key}.png"

def is_image_cached(cache_key: str) -> bool:
    path = get_image_cache_path(cache_key)
    return os.path.exists(path)

def save_image_cache(cache_key: str, image_data: bytes):
    path = get_image_cache_path(cache_key)
    with open(path, "wb") as f:
        f.write(image_data)
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO image_cache (cache_key, image_path) VALUES (?, ?)", (cache_key, path))
    conn.commit()
    conn.close()