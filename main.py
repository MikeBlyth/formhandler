import json
import csv
import os
import httpx
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from models import IntakeRecord, SearchResult
from mapping_logic import transform_data

app = FastAPI(title="Legal Intake Middleware")

# Mock Database: Verified Intake Records
MOCK_DB = [
    {
        "id": 1,
        "full_name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1985-05-12",
        "a_number": "123456789",
        "intake_date": "2024-03-01",
        "phone_number": "555-0101",
        "case_summary": "Client seeking asylum due to political persecution."
    },
    {
        "id": 2,
        "full_name": "Jane Smith",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1992-11-23",
        "a_number": "987654321",
        "intake_date": "2024-03-05",
        "phone_number": "555-0202",
        "case_summary": "Family-based petition for spouse."
    },
    {
        "id": 3,
        "full_name": "Mario Rossi",
        "first_name": "Mario",
        "last_name": "Rossi",
        "date_of_birth": "1978-08-30",
        "a_number": "112233445",
        "intake_date": "2024-03-10",
        "phone_number": "555-0303",
        "case_summary": "Employment visa renewal."
    },
    {
        "id": 4,
        "full_name": "Ibrahim Diallo",
        "first_name": "Ibrahim",
        "last_name": "Diallo",
        "date_of_birth": "1995-02-14",
        "a_number": "998877665",
        "intake_date": "2024-04-20",
        "phone_number": "555-0404",
        "case_summary": "Seeking asylum and work authorization."
    }
]

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

# --- Export Engine Functions ---

async def export_to_legalserver(data: dict, config: dict):
    transformed = transform_data(data, "LegalServer", config["fields"])
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                config["endpoint"],
                json=transformed,
                headers={"Authorization": "Bearer mock-token-123"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"LegalServer Export Failed: {e}")
            raise

def export_to_markdown(data: dict, config: dict):
    transformed = transform_data(data, "Markdown_Report", config["fields"])
    filename = f"exports/report_{data['id']}.md"
    os.makedirs("exports", exist_ok=True)
    with open(filename, "w") as f:
        f.write(f"# Case Summary: {transformed.get('Name', 'Unknown')}\n\n")
        for key, value in transformed.items():
            f.write(f"**{key}**: {value}  \n")
    return {"status": "success", "file": filename}

def export_to_csv(data: dict, config: dict):
    transformed = transform_data(data, "CSV_Export", config["fields"])
    filename = "master_intake.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=transformed.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(transformed)
    return {"status": "success", "file": filename}

# --- API Endpoints ---

@app.get("/search", response_model=List[SearchResult])
async def search_records(name: Optional[str] = None, a_number: Optional[str] = None):
    results = []
    for rec in MOCK_DB:
        if a_number and a_number == rec["a_number"]:
            results.append(rec)
        elif name and name.lower() in rec["full_name"].lower():
            results.append(rec)
    
    if not results and not name and not a_number:
        return [SearchResult(**rec) for rec in MOCK_DB]
        
    return [SearchResult(**rec) for rec in results]

@app.post("/export/{record_id}/{destination}")
async def trigger_export(record_id: int, destination: str):
    config = load_config()
    record = next((rec for rec in MOCK_DB if rec["id"] == record_id), None)
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if destination == "all":
        results = {}
        for dest, dest_config in config["destinations"].items():
            if dest_config["active"]:
                results[dest] = await run_single_export(record, dest, dest_config)
        return results
    
    dest_config = config["destinations"].get(destination)
    if not dest_config or not dest_config["active"]:
        raise HTTPException(status_code=400, detail="Invalid or inactive destination")
    
    return await run_single_export(record, destination, dest_config)

async def run_single_export(record, destination, config):
    if destination == "LegalServer":
        return await export_to_legalserver(record, config)
    elif destination == "Markdown_Report":
        return export_to_markdown(record, config)
    elif destination == "CSV_Export":
        return export_to_csv(record, config)
    else:
        raise HTTPException(status_code=400, detail="Export logic not implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
