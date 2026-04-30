"""
Mock LegalServer API v2 — simulates Search Matters + Create Note flow.

Endpoints:
  GET  /api/v2/matters          → returns one fake matter matching the search
  POST /api/v2/notes            → creates a fake note on a matter
"""
import uuid
import time
import random
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Mock LegalServer API v2")


def _check_auth(authorization: Optional[str]):
    if not authorization or "Bearer" not in authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")


# --- Search Matters ---

@app.get("/api/v2/matters")
async def search_matters(
    first: Optional[str] = Query(None),
    last: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    results: Optional[str] = Query("pro_bono"),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    time.sleep(0.5)

    if random.random() < 0.05:
        raise HTTPException(status_code=500, detail="Simulated internal server error")

    if not first and not last:
        return {"total_records": 0, "authorized_records": 0, "page_number": 1, "page_size": 20, "data": []}

    matter_uuid = str(uuid.uuid4())
    full_name = f"{first or ''} {last or ''}".strip()

    return {
        "page_number": 1,
        "page_size": 20,
        "total_number_of_pages": 1,
        "total_records": 1,
        "authorized_records": 1,
        "data": [
            {
                "matter_uuid": matter_uuid,
                "case_number": f"2024-PB-{random.randint(10000, 99999)}",
                "case_id": random.randint(10000, 99999),
                "client_full_name": full_name,
                "first": first or "",
                "last": last or "",
                "date_of_birth": date_of_birth or "",
                "case_disposition": {"lookup_value": "Open"},
                "intake_date": "2024-09-01",
                "case_profile_url": f"https://mock.legalserver.org/matter/profile/{matter_uuid}",
            }
        ]
    }


# --- Create Note ---

class NotePayload(BaseModel):
    module: str
    module_id: str
    subject: str
    body: str
    is_html: bool = False
    date_posted: Optional[str] = None
    created_by: Optional[str] = None


@app.post("/api/v2/notes", status_code=201)
async def create_note(
    note: NotePayload,
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    time.sleep(0.5)

    if random.random() < 0.05:
        raise HTTPException(status_code=500, detail="Simulated internal server error")

    note_uuid = str(uuid.uuid4())
    return {
        "id": random.randint(1000, 9999),
        "note_uuid": note_uuid,
        "module": note.module,
        "module_id": note.module_id,
        "subject": note.subject,
        "date_time_created": "2024-09-01T12:00:00Z",
        "note_type": {"lookup_value": "General"},
        "active": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
