"""Environment loading.

Settings live in backend/.env, but the app is started from the repo root, so a
bare load_dotenv() searches the wrong directory. Modules that read settings at
import time should import this first.
"""
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"

load_dotenv(ENV_PATH)
