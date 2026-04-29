# Legal Intake Middleware

This middleware acts as a "Universal Translator" between verified intake data and various legal destinations (LegalServer, Markdown, CSV).

## Architecture
- **Clean Pipeline:** Consumes verified JSON, handles logic/mapping/search.
- **Strategy Pattern:** Export destinations are decoupled; adding new ones doesn't break existing code.
- **Extensible Mapping:** `config.json` and `mapping_logic.py` handle field renaming without touching core logic.

## Project Structure
- `main.py`: Core FastAPI application and Export Engine.
- `models.py`: Pydantic data models for validation.
- `mapping_logic.py`: Field mapping and transformation logic.
- `config.json`: Control panel for active fields and destinations.
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
4. **Interactive Docs:** [http://localhost:8001/docs](http://localhost:8001/docs)
