from pathlib import Path
import sys

from langchain_ollama import OllamaLLM

# Model configuration
MODEL_NAME = "llama3.3"  # e.g., "llama3.3", "deepseek-r1:70b", "gemma3:27b", "llama4", "qwen3:32b"
MODEL = OllamaLLM(model=MODEL_NAME)

# Project root (repo root) inferred from this file location
# Example: repo/clients/local/config.py -> repo/
BASE_DIR = Path(__file__).resolve().parents[2]

# File path configuration (stored inside the repository)
PROMPT_FILE = BASE_DIR / "prompts" / "Breast_Tstage.txt"
INPUT_FILE = BASE_DIR / "data_example" / "Breast_Pathology_Test.xlsx"

# JSON field configuration
FIELDS = ["Tstage", "reason"]

# Input column name
INPUT_COLUMN = "Results"  # Column name containing the input text

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
