from pathlib import Path
import os
import sys

# Prompt template contains only {Results}

# ✅ OpenAI GPT configuration
MODEL_NAME = "gpt-5.1"  # gpt-4.1, gpt-4.1-mini, gpt-5.1

# Prefer OPENAI_API_KEY, but keep GPT_API_KEY for backward compatibility
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GPT_API_KEY", "")

# Repo root inferred from this file location:
# e.g., repo/clients/openai/config.py -> repo/
BASE_DIR = Path(__file__).resolve().parents[2]

# Files inside the repository
PROMPT_FILE = BASE_DIR / "prompts" / "LiverMR.txt"
INPUT_FILE  = BASE_DIR / "data_example" / "LiverMR_Test.xlsx"

# JSON field configuration
FIELDS = ["decision", "evidence"]

# Input column name
INPUT_COLUMN = "Results"


############## Configuration ends here ##############

# Automatically set suffixes
prompt_filename = PROMPT_FILE.stem
model_suffix = "_" + MODEL_NAME.replace(":", "_")

input_name_lower = INPUT_FILE.name.lower()
OUTPUT_SUFFIX = (
    "_Develop" if "develop" in input_name_lower else
    "_Test" if "test" in input_name_lower else
    "_Temp" if "temp" in input_name_lower else
    ""
)

# Save outputs under outputs/ (recommended)
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / f"{prompt_filename}{model_suffix}{OUTPUT_SUFFIX}.xlsx"
