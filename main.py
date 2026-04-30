import json
import csv
import os
import httpx
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from models import IntakeRecord
from mapping_logic import transform_data

app = FastAPI(title="Legal Intake Bridge")

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

@app.post("/export/{destination}")
async def trigger_export(destination: str, record: IntakeRecord):
    config = load_config()
    # Convert Pydantic model to dictionary for the mapping logic
    record_dict = record.model_dump()
    
    if destination == "all":
        results = {}
        for dest, dest_config in config["destinations"].items():
            if dest_config["active"]:
                results[dest] = await run_single_export(record_dict, dest, dest_config)
        return results
    
    dest_config = config["destinations"].get(destination)
    if not dest_config or not dest_config["active"]:
        raise HTTPException(status_code=400, detail="Invalid or inactive destination")
    
    return await run_single_export(record_dict, destination, dest_config)

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
