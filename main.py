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

async def export_to_legalserver(payload: dict, config: dict):
    transformed = transform_data(payload, "LegalServer", config["fields"])
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

def export_to_markdown(payload: dict, config: dict):
    transformed = transform_data(payload, "Markdown_Report", config["fields"])
    record_id = payload.get("id") or "unknown"
    filename = f"exports/report_{record_id}.md"
    os.makedirs("exports", exist_ok=True)
    with open(filename, "w") as f:
        f.write(f"# Case Summary: {transformed.get('Name', 'Unknown')}\n\n")
        for key, value in transformed.items():
            f.write(f"**{key}**: {value}  \n")
    return {
        "status": "success", 
        "message": "printed", 
        "file": filename, 
        "action": "markdown"
    }

def export_to_csv(payload: dict, config: dict):
    transformed = transform_data(payload, "CSV_Export", config["fields"])
    filename = "master_intake.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=transformed.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(transformed)
    return {
        "status": "success", 
        "message": f"saved to {filename} (stubbed)", 
        "file": filename, 
        "action": "csv"
    }

# --- API Endpoints ---

@app.post("/export")
async def trigger_export(record: IntakeRecord):
    config = load_config()
    payload = record.model_dump()
    action = payload.get("action")
    
    if action == "all":
        results = {}
        for dest, dest_config in config["destinations"].items():
            if dest_config["active"]:
                results[dest] = await run_single_export(payload, dest, dest_config)
        return results
    
    # Map friendly actions to destination names
    action_map = {
        "add_note": "LegalServer",
        "LegalServer": "LegalServer",
        "print": "Markdown_Report",
        "csv": "CSV_Export"
    }
    
    destination = action_map.get(action, action)
    dest_config = config["destinations"].get(destination)
    
    if not dest_config or not dest_config["active"]:
        raise HTTPException(status_code=400, detail=f"Invalid or inactive action/destination: {action}")
    
    return await run_single_export(payload, destination, dest_config)

async def run_single_export(payload, destination, config):
    if destination == "LegalServer":
        res = await export_to_legalserver(payload, config)
    elif destination == "Markdown_Report":
        res = export_to_markdown(payload, config)
    elif destination == "CSV_Export":
        res = export_to_csv(payload, config)
    else:
        raise HTTPException(status_code=400, detail="Export logic not implemented")

    # UUID Normalization Logic:
    # 1. If destination is LegalServer, we map its ID to legalserver_uuid.
    if destination == "LegalServer":
        ls_id = res.get("legalserver_id") or res.get("id")
        if ls_id:
            res["legalserver_uuid"] = ls_id
    # 2. Or, if ANY downstream returns legalserver_id explicitly, we honor it.
    elif isinstance(res, dict) and "legalserver_id" in res:
        res["legalserver_uuid"] = res["legalserver_id"]
        
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
