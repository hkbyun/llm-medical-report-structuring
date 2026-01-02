import json
from openai import OpenAI

from config import MODEL_NAME, OPENAI_API_KEY, FIELDS

# Configure the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def load_prompt(file_path):
    """Load the prompt template from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
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


def _fill_placeholders(template: str, mapping: dict) -> str:
    """Replace only the specified tokens (leave JSON braces { } intact)."""
    out = str(template)
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def generate_prompt(template: str, results: str) -> str:
    """Generate a prompt for the model using the given input text."""
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
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": wrapped},
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Return a non-JSON explicit error string; the caller can treat it as invalid.
        return f"[ERROR] {type(e).__name__}: {e}"


def correct_json_response(response):
    """Attempt to fix a malformed JSON response while preserving the original information."""
    correction_prompt = f"""
Your previous response did not strictly match the required JSON format.
Your task is to correct the format and return a valid JSON object.

DO NOT change any of the information from your previous response.
DO NOT provide explanations or additional text.
Do NOT modify JSON key names. Use the exact key names.

Simply return a properly formatted JSON with the following structure:

Required JSON format:
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
        correction = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": correction_prompt}
            ],
            temperature=0,
        )
        return correction.choices[0].message.content.strip()
    except Exception as e:
        return json.dumps({field: f"Correction Error: {str(e)}" if field == "Reason" else "Correction Failed" for field in FIELDS})