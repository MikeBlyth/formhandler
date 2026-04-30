# bridge — Reference

FastAPI bridge for mapping and exporting verified intake data.

## 🚨 Critical Constraints
- **Data Integrity:** Use Pydantic models in `models.py` for all data transformations.
- **Decoupling:** Never hard-code field names in `main.py`; always use `mapping_logic.py`.
- **Destinations:** Toggle visibility and active status in `config.json`.

## 🛠 Project Conventions
- **Centralized Translation:** The bridge consumes the entire JSON data block from the forms app. Mapping logic in `mapping_logic.py` transforms this full data set for each destination.
- **Action-Based Routing:** The `/export` endpoint uses an `action` field (`add_note`, `print`, `csv`) to route data.
- **UUID Normalization:** All exports normalize the LegalServer ID to `legalserver_uuid` if the destination is LegalServer or if explicitly returned by the downstream system.
- **Export Strategy:** Adding a new destination requires:
  1. Adding a mapping entry in `mapping_logic.py`.
  2. Adding a config entry in `config.json`.
  3. Implementing the export function in `main.py` and mapping it to an `action` in `trigger_export`.

## 🚀 Workflow
- **Mocking:** Always test exports against `mock_ls_api.py`. Ensure the `endpoint` in `config.json` matches the port where the mock API is running (default 8081).
- **Validation:** All incoming data must conform to the `IntakeRecord` schema in `models.py`.
