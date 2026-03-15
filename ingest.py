from fastapi import FastAPI, Request, Header, HTTPException
import sqlite3
import os
import uvicorn

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "sensors.db")
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize DB
con = sqlite3.connect(DB_PATH, check_same_thread=False)
con.execute(
    """
    CREATE TABLE IF NOT EXISTS readings (
        ts INTEGER,
        plant TEXT,
        temperature REAL,
        humidity REAL,
        light REAL,
        soil_moisture REAL,
        ph REAL
    )
    """
)

API_TOKEN = os.environ.get("INGEST_TOKEN", "changeme")

app = FastAPI()

@app.post("/ingest")
async def ingest(request: Request, authorization: str = Header(default="")):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")

    payload = await request.json()
    try:
        con.execute(
            "INSERT INTO readings VALUES (?,?,?,?,?,?,?)",
            (
                payload["ts"],
                payload["plant"],
                payload["temperature"],
                payload["humidity"],
                payload["light"],
                payload["soil_moisture"],
                payload["ph"],
            ),
        )
        con.commit()
        return {"ok": True}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

