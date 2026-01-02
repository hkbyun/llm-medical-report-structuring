import time
import pandas as pd
from tqdm import tqdm
from pathlib import Path

from config import BASE_DIR, PROMPT_FILE, INPUT_FILE, OUTPUT_FILE, INPUT_COLUMN
from utils import (
    load_prompt, generate_prompt, get_llama_response,
    verify_llama_response, correct_json_response,
    extract_json_from_cell, is_valid_json,
)

# ──────────────────────────────────────────
# ① Load prompt templates
# ──────────────────────────────────────────
prompt_template = load_prompt(PROMPT_FILE)

# Load the verifier prompt file
VERIFY_PATH_CANDIDATES = [
    BASE_DIR / "prompts" / "Breast_Tstage_verifier.txt"
]

verify_prompt_template = None
for _p in VERIFY_PATH_CANDIDATES:
    if _p.exists():
        verify_prompt_template = load_prompt(_p)
        print(f"Loaded verify prompt: {_p}")
        break

if verify_prompt_template is None:
    raise FileNotFoundError(
        "Verify prompt file not found. Tried:\n" + "\n".join(str(p) for p in VERIFY_PATH_CANDIDATES)
    )

# ──────────────────────────────────────────
# ② Resume from an existing output file or start fresh
# ──────────────────────────────────────────
if OUTPUT_FILE.exists():
    print(f"Found existing output file. Loading from {OUTPUT_FILE}")
    data = pd.read_excel(OUTPUT_FILE, sheet_name=0)
else:
    print(f"No previous output found. Starting fresh from {INPUT_FILE}")
    data = pd.read_excel(INPUT_FILE, sheet_name=0)

# Validate that the input column exists
if INPUT_COLUMN not in data.columns:
    raise ValueError(f"The input file must contain a '{INPUT_COLUMN}' column.")

# Create response/time columns if they do not exist
for col in ["Response", "Response2", "Response3", "Time"]:
    if col not in data.columns:
        data[col] = None

# Skip rows that have already been processed
skipped = [
    i for i, r in data.iterrows()
    if pd.notnull(r["Response"]) and str(r["Response"]).strip() != ""
]
if skipped:
    print(f"Skipping {len(skipped)} already-processed rows…")

# ──────────────────────────────────────────
# ③ Row-wise processing loop
# ──────────────────────────────────────────
for idx, row in tqdm(data.iterrows(), total=data.shape[0], desc="Processing Rows"):
    if idx in skipped:
        continue

    t0 = time.perf_counter()
    report_text = row[INPUT_COLUMN]

    # 1) First-pass response
    raw_prompt = generate_prompt(prompt_template, report_text)
    resp1 = get_llama_response(raw_prompt)
    data.at[idx, "Response"] = resp1

    # 2) Content verification (verifier step)
    resp2 = verify_llama_response(verify_prompt_template, report_text, resp1)
    data.at[idx, "Response2"] = resp2

    # 3) Format check → correct if needed
    extracted = extract_json_from_cell(resp2)
    if not is_valid_json(extracted):
        resp3 = correct_json_response(resp2)
        data.at[idx, "Response3"] = resp3
    else:
        data.at[idx, "Response3"] = ""  # Format OK → leave empty

    data.at[idx, "Time"] = round(time.perf_counter() - t0, 4)

    # Checkpoint every 10 rows
    if (idx + 1) % 10 == 0:
        data.to_excel(OUTPUT_FILE, index=False)
        print(f"Checkpoint: {idx + 1} rows saved to {OUTPUT_FILE}")

# ──────────────────────────────────────────
# ④ Final save
# ──────────────────────────────────────────
data.to_excel(OUTPUT_FILE, index=False)
print(f"Final result saved to {OUTPUT_FILE}")
