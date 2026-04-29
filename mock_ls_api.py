from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uuid
import time
import random

app = FastAPI(title="Mock LegalServer API v2")

class LegalServerMatter(BaseModel):
    first_name: str
    last_name: str
    case_summary_custom_99: str
    date_of_birth: str
    a_number_internal: str

@app.post("/api/v2/matters")
async def create_matter(matter: LegalServerMatter, authorization: str = Header(None)):
    # Simulating Latency
    time.sleep(1)
    
    # Mocking OAuth 2.1 check
    if not authorization or "Bearer" not in authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Error Injection (5% chance)
    if random.random() < 0.05:
        raise HTTPException(status_code=500, detail="Random simulated internal server error.")

    # Return a mock UUID
    return {
        "id": str(uuid.uuid4()),
        "status": "created",
        "message": "Matter successfully simulated."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
