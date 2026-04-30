import os
import html

# --- Markdown / CSV field mappings ---

MAPPING_CONFIG = {
    "Markdown_Report": {
        "full_legal_name": "Name",
        "date_of_birth": "DOB",
        "a_number": "A#",
        "personal_history": "Summary",
        "interview_date": "Date"
    },
    "CSV_Export": {
        "full_legal_name": "Name",
        "date_of_birth": "DOB",
        "a_number": "A#",
        "interview_date": "IntakeDate",
        "phone_primary": "Phone"
    }
}

def transform_data(data: dict, destination: str, active_fields: list):
    """Maps internal field names to destination-specific keys for Markdown/CSV exports."""
    mapping = MAPPING_CONFIG.get(destination, {})
    transformed = {}
    source_data = data.get("data", data)
    for internal_key, value in source_data.items():
        if not active_fields or internal_key in active_fields:
            dest_key = mapping.get(internal_key, internal_key)
            # Flatten SmartDate / Address / PersonName to a string for flat exports
            if isinstance(value, dict):
                value = _fmt_person_name(value) or _fmt_smart_date(value) or _fmt_address(value) or str(value)
            elif isinstance(value, list):
                value = _fmt_list(value)
            transformed[dest_key] = value
    return transformed


# --- LegalServer helpers ---

def get_ls_search_params(data: dict) -> dict:
    """Build query params for GET /api/v2/matters from intake data."""
    params = {}

    name = data.get("full_legal_name")
    if isinstance(name, dict):
        params["first"] = name.get("first_name") or ""
        params["last"] = name.get("last_name") or ""
    elif isinstance(name, str) and name:
        parts = name.strip().split()
        params["first"] = parts[0]
        params["last"] = parts[-1] if len(parts) > 1 else parts[0]

    dob = data.get("date_of_birth")
    if isinstance(dob, dict):
        structured = dob.get("structured_date")
        if structured:
            params["date_of_birth"] = structured
    elif isinstance(dob, str) and dob:
        params["date_of_birth"] = dob

    return params


def build_ls_note_subject(data: dict) -> str:
    name_val = data.get("full_legal_name")
    name = _fmt_person_name(name_val) if name_val else "Unknown Client"
    interview_date = data.get("interview_date")
    date_str = _fmt_smart_date(interview_date) if interview_date else ""
    if date_str:
        return f"Intake Record: {name} ({date_str})"
    return f"Intake Record: {name}"


def build_ls_note_body(data: dict) -> str:
    parts = []

    parts.append("<h3>Client Information</h3>\n")
    parts.append(_row("Full Legal Name", _fmt_person_name(data.get("full_legal_name"))))
    parts.append(_row("Preferred Name", data.get("preferred_name")))
    parts.append(_row("Date of Birth", _fmt_smart_date(data.get("date_of_birth"))))
    parts.append(_row("Sex / Gender", data.get("sex_gender")))
    parts.append(_row("Marital Status", data.get("marital_status")))
    parts.append(_row("Languages Spoken", _fmt_list(data.get("languages_spoken"))))
    parts.append(_row("A-Number", data.get("a_number")))
    parts.append(_row("File #", data.get("file_num")))
    parts.append(_row("Phone (Primary)", data.get("phone_primary")))
    parts.append(_row("Phone (Alternate)", data.get("phone_alternate")))
    parts.append(_row("Email", data.get("email")))

    parts.append("<br>\n<h3>Location &amp; Immigration</h3>\n")
    parts.append(_row("Current Address", _fmt_address(data.get("current_home_address"))))
    parts.append(_row("Client Location", data.get("client_location")))
    parts.append(_row("Country of Birth", data.get("country_of_birth")))
    parts.append(_row("Nationality", data.get("nationality")))
    parts.append(_row("City of Origin", data.get("city_of_origin")))
    parts.append(_row("Ethnic Group", data.get("ethnic_group")))
    parts.append(_row("Port of Entry", data.get("port_of_entry")))
    parts.append(_row("Entry Date", _fmt_smart_date(data.get("entry_date"))))
    parts.append(_row("Manner of Entry", data.get("manner_of_entry")))
    parts.append(_row("Immigration Status", data.get("current_immigration_status")))

    parts.append("<br>\n<h3>Interview Details</h3>\n")
    parts.append(_row("Interview Date", _fmt_smart_date(data.get("interview_date"))))
    parts.append(_row("Interviewer", data.get("interviewer")))

    personal_history = data.get("personal_history")
    fear_factors = data.get("fear_factors")
    if personal_history or fear_factors:
        parts.append("<br>\n<h3>Case Narrative</h3>\n")
        if personal_history:
            parts.append(f"<b>Personal History:</b><br>\n<p>{html.escape(str(personal_history))}</p>\n")
        if fear_factors:
            parts.append(f"<b>Fear Factors:</b><br>\n<p>{html.escape(str(fear_factors))}</p>\n")

    hearings = data.get("hearings")
    if isinstance(hearings, list) and hearings:
        parts.append("<br>\n<h3>Court Hearings</h3>\n")
        parts.append("<table border='1' cellpadding='4' style='border-collapse:collapse'>\n")
        parts.append("<tr><th>Date</th><th>Location</th><th>Type</th><th>Outcome Notes</th></tr>\n")
        for h in hearings:
            if isinstance(h, dict):
                date = html.escape(_fmt_smart_date(h.get("hearing_date")))
                location = html.escape(str(h.get("location") or ""))
                htype = html.escape(str(h.get("hearing_type") or ""))
                outcome = html.escape(str(h.get("outcome_notes") or ""))
                parts.append(f"<tr><td>{date}</td><td>{location}</td><td>{htype}</td><td>{outcome}</td></tr>\n")
        parts.append("</table>\n")

    health = data.get("health_conditions")
    medications = data.get("medications")
    allergies = data.get("allergies")
    if health or medications or allergies:
        parts.append("<br>\n<h3>Health</h3>\n")
        parts.append(_row("Health Conditions", health))
        parts.append(_row("Medications", medications))
        parts.append(_row("Allergies", allergies))

    emergency_contact = data.get("emergency_contact")
    relations = data.get("relations_in_us")
    if emergency_contact or relations:
        parts.append("<br>\n<h3>Contacts</h3>\n")
        parts.append(_row("Emergency Contact", emergency_contact))
        parts.append(_row("Emergency Relationship", data.get("emergency_relationship")))
        parts.append(_row("Emergency Phone", data.get("emergency_phone")))
        parts.append(_row("Relations in US", _fmt_list(relations)))

    docs = data.get("documents")
    if isinstance(docs, list) and docs:
        parts.append("<br>\n<h3>Documents</h3>\n<ul>\n")
        for doc in docs:
            if doc:
                parts.append(f"<li>{html.escape(str(doc))}</li>\n")
        parts.append("</ul>\n")

    other = data.get("other")
    if other:
        parts.append("<br>\n<h3>Other Notes</h3>\n")
        parts.append(f"<p>{html.escape(str(other))}</p>\n")

    return "".join(p for p in parts if p)


# --- Formatting helpers ---

def _fmt_smart_date(val) -> str:
    if isinstance(val, dict):
        # Ensure it's actually a SmartDate
        if "structured_date" not in val and "raw_string" not in val:
            return ""
        structured = val.get("structured_date")
        raw = val.get("raw_string")
        if structured and raw and structured != raw:
            return f"{raw} ({structured})"
        return structured or raw or ""
    return str(val) if val else ""


def _fmt_person_name(val) -> str:
    if isinstance(val, dict):
        # Ensure it's actually a PersonName
        if any(k in val for k in ["first_name", "last_name", "full_name_raw"]):
            parts = [val.get("first_name"), val.get("middle_name"), val.get("last_name")]
            name = " ".join(p for p in parts if p)
            suffix = val.get("suffix")
            if suffix:
                name = f"{name}, {suffix}"
            return name or val.get("full_name_raw") or ""
    return ""


def _fmt_address(val) -> str:
    if isinstance(val, dict):
        raw = val.get("raw_string")
        parts = [val.get("street"), val.get("city"), val.get("state"), val.get("zip_code"), val.get("country")]
        structured = ", ".join(p for p in parts if p)
        return structured or raw or ""
    return str(val) if val else ""


def _fmt_list(val) -> str:
    if isinstance(val, list):
        return "; ".join(str(v) for v in val if v)
    return str(val) if val else ""


def _row(label: str, val) -> str:
    if val is None or val == "" or val == [] or val == {}:
        return ""
    return f"<b>{label}:</b> {html.escape(str(val))}<br>\n"
