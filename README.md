# Legal Intake Middleware (Handler)

A stateless middleware designed to receive JSON intake data and route it to various destinations (LegalServer, CSV, Markdown, etc.). 

## Architecture
- **Stateless Bridge:** Acts as a "push" model receiver. It does not store or search for data.
- **Webhook Style:** Receives data via POST and forwards it after applying mapping logic.
- **Strategy Pattern:** Export destinations are decoupled; adding new ones doesn't break existing code.
- **Extensible Mapping:** `config.json` and `mapping_logic.py` handle field renaming and data transformation.

## Project Structure
- `main.py`: Core FastAPI application that handles incoming data and routes it.
- `models.py`: Pydantic data models for validation.
- `mapping_logic.py`: Field mapping and transformation logic.
- `config.json`: Configuration for active destinations and field requirements.
- `mock_ls_api.py`: Mock LegalServer v2 API for testing.

## Getting Started
1. **Activate Virtual Environment:**
   ```bash
   source .venv/bin/activate
   ```
2. **Start Mock API:**
   ```bash
   python mock_ls_api.py
   ```
3. **Start Middleware:**
   ```bash
   python main.py
   ```

## Usage
Send a POST request to `/export/{destination}` with the intake record JSON in the body.
- `destination`: `LegalServer`, `CSV_Export`, `Markdown_Report`, or `all`.

Example:
```bash
curl -X POST "http://localhost:8001/export/LegalServer" \
-H "Content-Type: application/json" \
-d '{"full_name": "John Doe", ...}'
```
