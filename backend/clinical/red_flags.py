"""Red flag detection rules - rule-based engine for emergency identification.

These rules are evaluated against structured patient data after every answer.
They do NOT rely on LLM inference for safety-critical detection.
"""

RED_FLAG_RULES = [
    {
        "id": "CARDIAC_EMERGENCY",
        "title": "Potential Cardiac Emergency Indicators",
        "severity": "HIGH",
        "description": "Potential priority symptoms detected: chest pain with high severity and associated breathlessness/sweating. A qualified healthcare professional should assess the patient immediately.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "chest_pain"},
            {"field": "severity", "operator": "gte", "value": 8},
            {"field": "breathlessness", "operator": "in", "values": ["Yes", "yes"]},
        ],
        "logic": "all",  # all conditions must be true
    },
    {
        "id": "CARDIAC_RADIATION",
        "title": "Chest Pain with Radiation",
        "severity": "HIGH",
        "description": "Chest pain radiating to arm, jaw, or neck detected. This pattern requires urgent medical evaluation.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "chest_pain"},
            {"field": "radiation", "operator": "contains_any", "values": ["arm", "jaw", "neck", "left"]},
            {"field": "sweating", "operator": "in", "values": ["Yes", "yes"]},
        ],
        "logic": "all",
    },
    {
        "id": "SEVERE_BREATHLESSNESS",
        "title": "Severe Breathing Difficulty",
        "severity": "HIGH",
        "description": "Severe breathing difficulty at rest detected. Immediate medical attention may be required.",
        "conditions": [
            {"field": "breathlessness", "operator": "in", "values": ["At rest", "Yes"]},
            {"field": "severity", "operator": "gte", "value": 7},
        ],
        "logic": "all",
    },
    {
        "id": "HEMOPTYSIS",
        "title": "Blood in Cough (Hemoptysis)",
        "severity": "HIGH",
        "description": "Patient reports coughing up blood. This requires urgent medical evaluation.",
        "conditions": [
            {"field": "hemoptysis", "operator": "in", "values": ["Yes", "yes"]},
        ],
        "logic": "all",
    },
    {
        "id": "MENINGITIS_SIGNS",
        "title": "Potential Meningitis Indicators",
        "severity": "HIGH",
        "description": "Headache with neck stiffness and fever detected. These symptoms may indicate meningitis and require urgent evaluation.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "headache"},
            {"field": "neck_stiffness", "operator": "in", "values": ["Yes", "yes"]},
            {"field": "fever", "operator": "in", "values": ["Yes", "yes"]},
        ],
        "logic": "all",
    },
    {
        "id": "STROKE_SIGNS",
        "title": "Potential Neurological Emergency",
        "severity": "HIGH",
        "description": "Sudden headache with weakness or speech difficulty detected. These may indicate a neurological emergency.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "headache"},
            {"field": "weakness", "operator": "in", "values": ["Yes", "yes"]},
            {"field": "severity", "operator": "gte", "value": 8},
        ],
        "logic": "all",
    },
    {
        "id": "SEVERE_ABDOMINAL",
        "title": "Severe Abdominal Pain",
        "severity": "HIGH",
        "description": "Severe abdominal pain with vomiting detected. This may indicate a surgical emergency.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "abdominal_pain"},
            {"field": "severity", "operator": "gte", "value": 8},
            {"field": "nausea_vomiting", "operator": "in", "values": ["Yes - Vomiting", "Vomiting"]},
        ],
        "logic": "all",
    },
    {
        "id": "GI_BLEEDING",
        "title": "Gastrointestinal Bleeding",
        "severity": "HIGH",
        "description": "Blood in stool reported. This requires urgent medical evaluation.",
        "conditions": [
            {"field": "bowel_changes", "operator": "in", "values": ["Blood in stool"]},
        ],
        "logic": "all",
    },
    {
        "id": "HIGH_FEVER",
        "title": "Very High Fever",
        "severity": "MEDIUM",
        "description": "Very high fever reported. Close monitoring and prompt medical evaluation recommended.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "fever"},
            {"field": "temperature", "operator": "contains_any", "values": ["104", "105", "106", "40", "41"]},
        ],
        "logic": "all",
    },
    {
        "id": "FEVER_WITH_RASH",
        "title": "Fever with Rash",
        "severity": "MEDIUM",
        "description": "Fever with skin rash detected. This combination may indicate dengue, measles, or other conditions requiring evaluation.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "fever"},
            {"field": "rash", "operator": "in", "values": ["Yes", "yes"]},
            {"field": "body_pain", "operator": "in", "values": ["Yes - Body pain", "Yes - Joint pain", "Yes - Both"]},
        ],
        "logic": "all",
    },
    {
        "id": "TB_SUSPICION",
        "title": "Possible Tuberculosis Indicators",
        "severity": "MEDIUM",
        "description": "Combination of chronic cough, weight loss, and night sweats detected. TB evaluation may be warranted.",
        "conditions": [
            {"field": "pathway", "operator": "eq", "value": "cough_breathing"},
            {"field": "weight_loss", "operator": "in", "values": ["Yes", "yes"]},
            {"field": "night_sweats", "operator": "in", "values": ["Yes", "yes"]},
        ],
        "logic": "all",
    },
    {
        "id": "BLOOD_SPUTUM",
        "title": "Blood-tinged Sputum",
        "severity": "MEDIUM",
        "description": "Blood-tinged sputum reported. Medical evaluation for underlying cause is recommended.",
        "conditions": [
            {"field": "cough_type", "operator": "in", "values": ["With phlegm - Blood-tinged"]},
        ],
        "logic": "all",
    },
]


def evaluate_condition(condition: dict, data: dict) -> bool:
    """Evaluate a single condition against the structured data."""
    field = condition["field"]
    value = data.get(field)

    if value is None:
        return False

    operator = condition["operator"]

    if operator == "eq":
        return str(value).lower() == str(condition["value"]).lower()
    elif operator == "in":
        return str(value) in condition["values"]
    elif operator == "gte":
        try:
            return float(value) >= float(condition["value"])
        except (ValueError, TypeError):
            return False
    elif operator == "lte":
        try:
            return float(value) <= float(condition["value"])
        except (ValueError, TypeError):
            return False
    elif operator == "contains_any":
        str_val = str(value).lower()
        return any(v.lower() in str_val for v in condition["values"])
    elif operator == "not_empty":
        return bool(value)

    return False


def evaluate_red_flags(structured_data: dict, pathway: str) -> list:
    """Evaluate all red flag rules against the patient's structured data.

    Returns a list of triggered red flag alerts.
    """
    data_with_pathway = {**structured_data, "pathway": pathway}
    triggered = []

    for rule in RED_FLAG_RULES:
        conditions = rule["conditions"]
        logic = rule.get("logic", "all")

        if logic == "all":
            if all(evaluate_condition(c, data_with_pathway) for c in conditions):
                triggered.append({
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "description": rule["description"],
                })
        elif logic == "any":
            if any(evaluate_condition(c, data_with_pathway) for c in conditions):
                triggered.append({
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "description": rule["description"],
                })

    return triggered
