# bridge — Reference

FastAPI bridge for mapping and exporting verified intake data.

## 🚨 Critical Constraints
- **Data Integrity:** Use Pydantic models in `models.py` for all data transformations.
- **Decoupling:** Never hard-code field names in `main.py`; always use `mapping_logic.py`.
- **Destinations:** Toggle visibility and active status in `config.json`.

## 🛠 Project Conventions
- **Centralized Translation:** The bridge consumes the entire `reviewed_data` JSON block from the forms app (sent as the `data` field in `IntakeRecord`). Field names match the legacy `IntakeForm` schema (`full_legal_name`, `date_of_birth`, `phone_primary`, etc.).
- **Action-Based Routing:** The `/export` endpoint uses an `action` field (`add_note`, `print`, `csv`) to route data to a destination.
- **UUID Normalization:** LegalServer exports return `legalserver_uuid` (the `matter_uuid` from the Search Matters response). Any other destination that returns `legalserver_id` has it normalized to `legalserver_uuid` as well.
- **Export Strategy:** Adding a new destination requires:
  1. Adding helper functions or a mapping entry in `mapping_logic.py`.
  2. Adding a config entry in `config.json`.
  3. Implementing the export function in `main.py` and mapping it to an `action` in `trigger_export`.

## 🚀 LegalServer Flow (two-step)
The `add_note` action performs two sequential calls to the LegalServer API:

1. **Search Matters** — `GET /api/v2/matters?first=...&last=...&date_of_birth=...&results=full`
   - Extracts search params via `get_ls_search_params()` in `mapping_logic.py`.
   - Validates: exactly 1 result, `authorized_records == total_records`, disposition is Open/Pending/Incomplete Intake.
   - Extracts `matter_uuid` from `data[0]`.

2. **Create Note** — `POST /api/v2/notes`
   - Builds HTML note body via `build_ls_note_body()` in `mapping_logic.py`.
   - Sends `module=matter`, `module_id=<matter_uuid>`, `is_html=true`.
   - Returns `matter_uuid` + `note_uuid` to the forms app.

**Config keys for LegalServer** (`config.json`):
- `base_url` — e.g. `https://your-site.legalserver.org` (use `http://localhost:8081` for mock)
- `api_token` — Bearer token for the LegalServer API user

**Required LegalServer permissions:** `API Matter: Search`, `API Get/Search Matter Full Results`, `API Create Note`.

## 🧪 Mocking
Run `mock_ls_api.py` on port 8081 to test locally:
- `GET /api/v2/matters` — returns one fake open matter matching the search params
- `POST /api/v2/notes` — returns a fake note with `note_uuid`

Set `base_url` to `http://localhost:8081` in `config.json` to route against the mock.

## 📋 Incoming Data Shape
Fields are keyed by intake form field names. Key fields used by the bridge:

| Field | Type | Used for |
|---|---|---|
| `full_legal_name` | string or `PersonName` dict | LS search (first/last) + note |
| `date_of_birth` | `{raw_string, structured_date}` | LS search + note |
| `phone_primary` | string | note, CSV |
| `a_number` | string | note |
| `personal_history` | string | note body |
| `fear_factors` | string | note body |
| `hearings` | list of `{hearing_date, location, hearing_type, outcome_notes}` | note body (HTML table) |
| `interview_date` | `{raw_string, structured_date}` | note subject + Markdown/CSV |

`SmartDate` fields (`date_of_birth`, `interview_date`, `entry_date`, `hearing_date`) are dicts with `raw_string` and `structured_date`. The helpers `_fmt_smart_date()` and `_fmt_address()` in `mapping_logic.py` flatten them for output.

## ✅ Validation
All incoming requests must conform to `IntakeRecord` in `models.py`:
- `action`: string — `add_note`, `print`, `csv`, or `all`
- `data`: dict — the full `reviewed_data` block from the forms app
- `id`: optional int
