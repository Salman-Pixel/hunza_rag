from dotenv import load_dotenv
from pathlib import Path
import os
import pathlib
import re


# always load .env at repo root
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)


def env_str(name, default=None):
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"missing env var {name}")
    return v
# ... keep the rest of utils as is


def env_str(name, default=None):
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"missing env var {name}")
    return v


def env_int(name, default=None):
    v = os.getenv(name)
    return int(v) if v is not None else int(default)


def env_float(name, default=None):
    v = os.getenv(name)
    return float(v) if v is not None else float(default)


def env_bool(name, default=False):
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "y"}


def ensure_dir(p: str):
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)


def clean_text(t: str) -> str:
    t = t.replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
