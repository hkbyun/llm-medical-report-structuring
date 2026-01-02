import json
from config import MODEL, FIELDS

### Verifier placeholder-replacement checks (non-crashing version)

def _fill_placeholders(template: str, mapping: dict) -> str:
    """Replace only the specified tokens to avoid brace-format collisions."""
    out = str(template)
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", str(v))
    return out

def _error_json(message: str) -> str:
    """Return a JSON string that fills all fields with the same error message."""
    return json.dumps({field: message for field in FIELDS})

def load_prompt(file_path):
    """Load a prompt template from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def is_valid_json(response):
    """Validate whether the response is a well-formed JSON object with all required keys."""
    if not response or not isinstance(response, str):
        return False
    try:
        parsed = json.loads(response)
        return isinstance(parsed, dict) and all(field in parsed for field in FIELDS)
    except (json.JSONDecodeError, TypeError):
        return False

def extract_json_from_cell(cell_value):
    """Extract a JSON substring from a model response."""
    if isinstance(cell_value, str):
        cell_value = cell_value.replace("\n", "").strip()
        start_index, end_index = cell_value.find("{"), cell_value.rfind("}")
        if start_index != -1 and end_index != -1:
            return cell_value[start_index:end_index + 1]
    return None

def generate_prompt(template, results):
    # ⚠️ Do NOT use format() → use safe replacement instead
    return _fill_placeholders(template, {"Results": results})

def get_llama_response(prompt):
    """Call the local LLM and return raw text. On error, return a JSON string filled with an error message."""
    try:
        return MODEL.invoke(prompt).strip()
    except Exception as e:
        msg = f"Error: {type(e).__name__}: {e}"
        return _error_json(msg)

def correct_json_response(response):
    """Fix malformed JSON responses while preserving the original content. Never raises; returns error JSON on failure."""
    correction_prompt = f"""
Your previous response did not strictly match the required JSON format.
Your task is to correct the format and return a valid JSON.

DO NOT change any information from your previous response.
DO NOT provide explanations or additional text.
Do NOT modify JSON key names. Use the exact key names.

Return JSON with exactly these keys:
{', '.join([f'"{f}"' for f in FIELDS])}

----
Here is your previous response:
{response}
----
"""
    try:
        return MODEL.invoke(correction_prompt).strip()
    except Exception as e:
        msg = f"Correction Error: {type(e).__name__}: {e}"
        return _error_json(msg)

def verify_llama_response(template: str, results_text: str, draft_json: str) -> str:
    """
    Verifier step that NEVER raises.
    - If placeholders are missing or replacement fails, returns an error JSON string (filled for all fields).
    - If the LLM call fails, returns an error JSON string (filled for all fields).
    """
    required_tokens = ["{Results}", "{draft_json}"]

    # 1) Check required placeholders exist in the template
    for token in required_tokens:
        if token not in template:
            return _error_json(f"Verification Template Error: missing placeholder {token}")

    # 2) Validate inputs
    if results_text is None or draft_json is None:
        return _error_json("Verification Input Error: results_text or draft_json is None")

    # 3) Perform replacement
    filled_prompt = _fill_placeholders(template, {
        "Results": results_text,
        "draft_json": draft_json,
    })

    # 4) Ensure placeholders are fully replaced
    for token in required_tokens:
        if token in filled_prompt:
            return _error_json(f"Verification Template Error: placeholder {token} was not filled correctly")

    # 5) Call the verifier LLM
    try:
        return MODEL.invoke(filled_prompt).strip()
    except Exception as e:
        msg = f"Verification Error: {type(e).__name__}: {e}"
        return _error_json(msg)
