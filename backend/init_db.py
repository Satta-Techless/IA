import sqlite3
import os

DB_PATH = "cache.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS processed_urls
             (url_hash TEXT PRIMARY KEY,
              title TEXT,
              subcategory TEXT,
              poster_path TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS image_cache
             (cache_key TEXT PRIMARY KEY,
              image_path TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
conn.close()
print("✅ Cache database initialized.")