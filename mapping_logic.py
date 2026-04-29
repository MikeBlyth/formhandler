import json
import os

MAPPING_CONFIG = {
    "LegalServer": {
        "first_name": "first_name",
        "last_name": "last_name",
        "date_of_birth": "date_of_birth",
        "case_summary": "case_summary_custom_99",
        "a_number": "a_number_internal"
    },
    "Markdown_Report": {
        "full_name": "Name",
        "date_of_birth": "DOB",
        "a_number": "A#",
        "case_summary": "Summary",
        "intake_date": "Date"
    },
    "CSV_Export": {
        "full_name": "Name",
        "date_of_birth": "DOB",
        "a_number": "A#",
        "intake_date": "IntakeDate",
        "phone_number": "Phone"
    }
}

def transform_data(data: dict, destination: str, active_fields: list):
    """
    Universal Translator: Maps internal field names to destination-specific keys
    based on the mapping config and active fields toggle.
    """
    mapping = MAPPING_CONFIG.get(destination, {})
    transformed = {}
    
    for internal_key, value in data.items():
        if internal_key in active_fields:
            dest_key = mapping.get(internal_key, internal_key)
            transformed[dest_key] = value
            
    return transformed
