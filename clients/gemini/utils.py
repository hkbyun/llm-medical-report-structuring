import json
import google.generativeai as genai
from config import MODEL_NAME, GEMINI_API_KEY, FIELDS

# Configure the Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def is_valid_json(response):
    """Validate whether the response is a well-formed JSON object (+ fail if values are all 'Invalid')."""
    if not response or not isinstance(response, str):
        return False
    try:
        parsed = json.loads(response)
        if not isinstance(parsed, dict):
            return False
        # Are all required keys present?
        if not all(field in parsed for field in FIELDS):
            return False
        # If all values are placeholders like 'Invalid', treat as not valid
        placeholder_values = {"invalid", "Invalid", "INVALID"}
        if all(isinstance(parsed[k], str) and parsed[k].strip() in placeholder_values for k in FIELDS):
            return False
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def extract_json_from_cell(cell_value):
    if isinstance(cell_value, str):
        cell_value = cell_value.replace("\n", "").strip()
        start_index, end_index = cell_value.find("{"), cell_value.rfind("}")
        if start_index != -1 and end_index != -1:
            return cell_value[start_index:end_index + 1]
    return None

def _fill_placeholders(template: str, mapping: dict) -> str:
    out = str(template)
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", str(v))
    return out

def generate_prompt(template: str, results: str) -> str:
    return _fill_placeholders(template, {"Results": results})

def _force_json_wrapper(user_prompt: str) -> str:
    """Wrap the prompt to force the model to output JSON only."""
    fields_spec = ", ".join([f'"{f}": "<string>"' for f in FIELDS])
    return f"""
You must respond with **only** a single JSON object and nothing else (no prose).
JSON schema:
{{
  {fields_spec}
}}

User content:
{user_prompt}
"""

def get_gpt_response(prompt):
    try:
        wrapped = _force_json_wrapper(prompt)
        resp = model.generate_content(wrapped)
        # Depending on the SDK/version, text may appear in resp.text or in candidates[0].content.parts
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            # fallback
            parts = getattr(resp.candidates[0].content, "parts", [])
            text = "".join(getattr(p, "text", "") for p in parts)
        if not text:
            raise RuntimeError("Empty response text from Gemini.")
        return text.strip()
    except Exception as e:
        # On error, return an explicit non-JSON string -> will be marked invalid by is_valid_json()
        return f"[ERROR] {type(e).__name__}: {e}"

def correct_json_response(response):
    """Fix malformed JSON responses (Gemini-based correction)."""
    fields_spec = ", ".join([f'"{f}": "<string>"' for f in FIELDS])
    correction_prompt = f"""
        Your previous response did not strictly match the required JSON format. 
    Your task is to correct the format and return a valid JSON format. 

    DO NOT change any of the information from your previous response. 
    DO NOT provide explanations or additional text.
    Do NOT modify JSON key names. Use the exact key names.

    Simply return a properly formatted JSON with the following structure:

    **Required JSON format:** 
    ```json
    {{
        {", ".join([f'"{field}": "<string>"' for field in FIELDS])}
    }}
    ```

    ----
    Here is your previous response: 
    {response}
    ----   
    """
    try:
        resp = model.generate_content(correction_prompt)
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            parts = getattr(resp.candidates[0].content, "parts", [])
            text = "".join(getattr(p, "text", "") for p in parts)
        if not text:
            raise RuntimeError("Empty correction response from Gemini.")
        return text.strip()
    except Exception as e:
        # If correction fails, return a non-JSON string -> can be retried or post-processed later
        return f"[CORRECTION_ERROR] {type(e).__name__}: {e}"
