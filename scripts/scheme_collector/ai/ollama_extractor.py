import subprocess
import os

OLLAMA_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")

PROMPT = """
Extract:
- Eligibility criteria
- Required documents
Return as bullet points.

TEXT:
"""

def extract_info(text):
    process = subprocess.Popen(
        [OLLAMA_PATH, "run", "tinyllama"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    stdout, _ = process.communicate(PROMPT + text[:4000], timeout=120)
    return stdout
