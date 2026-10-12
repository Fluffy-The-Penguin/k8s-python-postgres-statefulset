import os
import psycopg2
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-svc"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "secret123"),
        dbname=os.getenv("POSTGRES_DB", "postgres")
    )
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY);")
    cur.execute("INSERT INTO visits DEFAULT VALUES;")
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return f"Python + PostgreSQL Live! Total DB Rows: {count}\n"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
