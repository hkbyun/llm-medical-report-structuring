[Figure1.tif](https://github.com/user-attachments/files/24823864/Figure1.tif)

# LLM Extraction Pipelines (OpenAI / Gemini / Local)

Minimal scripts to run **LLM extraction → (optional) JSON correction → Excel output**.

## Folder structure
- `openai/` : OpenAI pipeline (`config.py`, `utils.py`, `main.py`)
- `gemini/` : Gemini pipeline (`config.py`, `utils.py`, `main.py`)
- `local/`  : Local (Ollama) pipeline (`config.py`, `utils.py`, `main.py`)
- `prompts/` : prompt templates (`.txt`)
- `data_example/` : example input Excel files (`.xlsx`)
- `outputs/` : output Excel files (auto-created)

## Install
Common:
```bash
pip install pandas tqdm openpyxl
```
OpenAI:
```bash
pip install openai
```
Gemini:
```bash
pip install google-generativeai
```
Local (Ollama):
```bash
pip install langchain-ollama
```

## API keys
OpenAI:
- Windows (PowerShell): `setx OPENAI_API_KEY "YOUR_KEY"`
- macOS/Linux: `export OPENAI_API_KEY="YOUR_KEY"`

Gemini:
- Windows (PowerShell): `setx GOOGLE_API_KEY "YOUR_KEY"`
- macOS/Linux: `export GOOGLE_API_KEY="YOUR_KEY"`

## Configure
Edit each pipeline’s `config.py`:
- `MODEL_NAME`, `FIELDS`, `PROMPT_FILE`, `INPUT_FILE`, `INPUT_COLUMN`

## Run
From the repo root:
```bash
python openai/main.py
python gemini/main.py
python local/main.py
```
Outputs are written to `outputs/`.

## Input format
Your input Excel must include the column name set by `INPUT_COLUMN` (default: `Results`).

