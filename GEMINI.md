# bridge — Reference

FastAPI bridge for mapping and exporting verified intake data.

## 🚨 Critical Constraints
- **Data Integrity:** Use Pydantic models in `models.py` for all data transformations.
- **Decoupling:** Never hard-code field names in `main.py`; always use `mapping_logic.py`.
- **Destinations:** Toggle visibility and active status in `config.json`.

## 🛠 Project Conventions
- **Export Strategy:** Adding a new destination requires:
  1. Adding a mapping entry in `mapping_logic.py`.
  2. Adding a config entry in `config.json`.
  3. Implementing the export function in `main.py`.

## 🚀 Workflow
- **Mocking:** Always test exports against `mock_ls_api.py`. Ensure the `endpoint` in `config.json` matches the port where the mock API is running (default 8081).
- **Validation:** All incoming data must conform to the `IntakeRecord` schema in `models.py`.
