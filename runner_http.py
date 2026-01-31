import os
import asyncio
from fastapi import FastAPI, Header, HTTPException

from etl.etl_runner import run_etl

app = FastAPI()

EXPECTED_TOKEN = os.environ.get("INTERNAL_TOKEN")
WORKER_ID = os.environ.get("WORKER_ID", "forensic-runner")


def _auth(x_internal_token: str | None):
    if not EXPECTED_TOKEN:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if x_internal_token != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/healthz")
def healthz():
    return {"ok": True, "worker": WORKER_ID}


@app.post("/internal/run-once")
async def run_once(x_internal_token: str | None = Header(default=None)):
    _auth(x_internal_token)

    # Run one full ETL/queue pass. This should:
    # - claim forensic_jobs
    # - process one or more jobs
    # - write results back
    await run_etl()

    return {"status": "done", "worker": WORKER_ID}
