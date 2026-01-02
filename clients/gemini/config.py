from pathlib import Path
import os
import sys

# ✅ Gemini API configuration
MODEL_NAME = "gemini-2.5-pro"
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# repo root inferred from this file location (clients/gemini/config.py -> repo/)
BASE_DIR = Path(__file__).resolve().parents[2]

PROMPT_FILE = BASE_DIR / "prompts" / "Breast_Nstage.txt"
INPUT_FILE  = BASE_DIR / "data_example" / "Breast_Pathology_Test.xlsx"

FIELDS = ["Nstage", "reason"]
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
