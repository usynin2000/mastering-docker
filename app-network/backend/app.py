from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host="database",  # Имя контейнера!
            database="appdb",
            user="postgres",
            password="dbpass"
        )
        conn.close()
        return {"status": "DB connected"}
    except Exception as e:
        return {"status": "DB error", "error": str(e)}