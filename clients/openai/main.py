import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import PROMPT_FILE, INPUT_FILE, OUTPUT_FILE, INPUT_COLUMN
from utils import (
    load_prompt,
    generate_prompt,
    get_gpt_response,
    correct_json_response,
    extract_json_from_cell,
    is_valid_json,
)

# Load the prompt template
prompt_template = load_prompt(PROMPT_FILE)

# Resume from an existing output file if it exists; otherwise start from the input file
if OUTPUT_FILE.exists():
    print(f"Found existing output file. Loading from {OUTPUT_FILE}")
    data = pd.read_excel(OUTPUT_FILE, sheet_name=0)
else:
    print(f"No previous output found. Starting fresh from {INPUT_FILE}")
    data = pd.read_excel(INPUT_FILE, sheet_name=0)

# Verify that the input column exists
if INPUT_COLUMN not in data.columns:
    raise ValueError(f"The input file must contain a '{INPUT_COLUMN}' column.")

# Create response/time columns if they do not exist
for col in ["Response", "Response2", "Time"]:
    if col not in data.columns:
        data[col] = None

# Pre-scan rows that have already been processed
skipped_indices = [
    idx for idx, row in data.iterrows()
    if pd.notnull(row["Response"]) and str(row["Response"]).strip() != ""
]

if skipped_indices:
    print(f"Skipping {len(skipped_indices)} already-processed rows...")

# Process each row
for idx, row in tqdm(data.iterrows(), total=data.shape[0], desc="Processing Rows"):
    if idx in skipped_indices:
        continue

    input_text = row[INPUT_COLUMN]
    prompt = generate_prompt(prompt_template, input_text)

    start_time = time.perf_counter()

    response = get_gpt_response(prompt)
    data.at[idx, "Response"] = response

    extracted_json = extract_json_from_cell(response)
    if not is_valid_json(extracted_json):
        corrected_response = correct_json_response(response)
        data.at[idx, "Response2"] = corrected_response
    else:
        data.at[idx, "Response2"] = ""

    end_time = time.perf_counter()
    data.at[idx, "Time"] = round(end_time - start_time, 4)

    # Periodic checkpoint saving
    if (idx + 1) % 10 == 0:
        # Ensure the parent directory exists (safe if OUTPUT_FILE is under outputs/)
        Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
        data.to_excel(OUTPUT_FILE, index=False)
        print(f"Checkpoint: {idx + 1} rows saved to {OUTPUT_FILE}")

# Final save
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
data.to_excel(OUTPUT_FILE, index=False)
print(f"Final result saved to {OUTPUT_FILE}")
