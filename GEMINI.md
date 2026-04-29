# formhandler — Middleware Reference

FastAPI middleware for searching, mapping, and exporting verified intake data.

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
- **Mocking:** Always test exports against `mock_ls_api.py` before targeting real endpoints.
- **Search:** Supports case-insensitive name matching and exact A# matching.
