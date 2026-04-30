import json
import csv
import os
import secrets
import httpx
from typing import Annotated, List, Optional
from fastapi import Depends, FastAPI, Header, HTTPException, status, BackgroundTasks
from models import IntakeRecord
from mapping_logic import (
    transform_data,
    get_ls_search_params,
    build_ls_note_subject,
    build_ls_note_body,
)

app = FastAPI(title="Legal Intake Bridge")

_BRIDGE_API_KEY = os.environ.get("BRIDGE_API_KEY", "")


def _verify_api_key(authorization: Annotated[str | None, Header()] = None) -> None:
    if not _BRIDGE_API_KEY:
        return  # No key configured — open (dev mode)
    expected = f"Bearer {_BRIDGE_API_KEY}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized.",
        )


def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Environment overrides for production/demo use
    ls_config = config["destinations"].get("LegalServer", {})
    if os.environ.get("LS_BASE_URL"):
        ls_config["base_url"] = os.environ.get("LS_BASE_URL")
    if os.environ.get("LS_API_TOKEN"):
        ls_config["api_token"] = os.environ.get("LS_API_TOKEN")
    
    return config

# --- Export Engine Functions ---

async def export_to_legalserver(payload: dict, config: dict):
    data = payload.get("data", payload)
    base_url = config["base_url"].rstrip("/")
    token = config["api_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    search_params = get_ls_search_params(data)
    if not search_params.get("first") and not search_params.get("last"):
        raise HTTPException(
            status_code=422,
            detail="Insufficient data to search LegalServer: need at least a client name"
        )
    search_params["results"] = "full"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for the matter
        search_resp = await client.get(
            f"{base_url}/api/v2/matters",
            params=search_params,
            headers=headers,
        )
        search_resp.raise_for_status()
        search_result = search_resp.json()

        total = search_result.get("total_records", 0)
        authorized = search_result.get("authorized_records", total)

        if total == 0:
            raise HTTPException(status_code=404, detail="No matching matter found in LegalServer")
        if authorized < total:
            raise HTTPException(
                status_code=403,
                detail=f"LegalServer found {total} match(es) but API user can only see {authorized} — check permissions"
            )
        if total > 1:
            raise HTTPException(
                status_code=409,
                detail=f"Ambiguous: {total} matters match the search criteria — narrow the query"
            )

        matter = search_result["data"][0]
        disposition = (matter.get("case_disposition") or {}).get("lookup_value", "")
        if disposition and disposition not in ("Open", "Pending", "Incomplete Intake"):
            raise HTTPException(
                status_code=422,
                detail=f"Matter disposition is '{disposition}' — will not write to a non-open case"
            )

        matter_uuid = matter["matter_uuid"]

        # Step 2: Create the note
        note_payload = {
            "module": "matter",
            "module_id": matter_uuid,
            "subject": build_ls_note_subject(data),
            "body": build_ls_note_body(data),
            "is_html": True,
        }
        note_resp = await client.post(
            f"{base_url}/api/v2/notes",
            json=note_payload,
            headers=headers,
        )
        note_resp.raise_for_status()
        note_result = note_resp.json()

        return {
            "matter_uuid": matter_uuid,
            "note_uuid": note_result.get("note_uuid"),
            "legalserver_uuid": matter_uuid,
        }


def export_to_markdown(payload: dict, config: dict):
    transformed = transform_data(payload, "Markdown_Report", config.get("fields", []))
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
    transformed = transform_data(payload, "CSV_Export", config.get("fields", []))
    filename = "master_intake.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=transformed.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(transformed)
    return {
        "status": "success",
        "message": f"saved to {filename}",
        "file": filename,
        "action": "csv"
    }


# --- API Endpoints ---

@app.post("/export")
async def trigger_export(
    record: IntakeRecord,
    _: Annotated[None, Depends(_verify_api_key)] = None,
):
    config = load_config()
    payload = record.model_dump()
    action = payload.get("action")

    if action == "all":
        results = {}
        for dest, dest_config in config["destinations"].items():
            if dest_config["active"]:
                results[dest] = await run_single_export(payload, dest, dest_config)
        return results

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

    # If any destination explicitly returns legalserver_id, normalize it
    if isinstance(res, dict) and "legalserver_id" in res and "legalserver_uuid" not in res:
        res["legalserver_uuid"] = res["legalserver_id"]

    return res


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
