"""End-to-end smoke test for the LoRiS Streamlit app.

The app reads several required environment variables (BACKEND_URL, PAGE_ICON, …)
with no defaults and, on a full run, calls a backend and loads remote QALD data.
We therefore exercise the built-in DRY_RUN path: it executes the whole startup
sequence (imports, config, favicon/Image loading, CSS, index.html handling) and
then stops the process before any backend/network work — so an import error or a
broken dependency upgrade fails here, without needing live services.
"""
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
APP = "loris--llm-based-explanations-for-sparql-queries.py"

pytestmark = pytest.mark.e2e


def _app_env():
    return {
        **os.environ,
        "DRY_RUN": "true",
        "BACKEND_URL": "http://localhost:9999",
        "PAGE_ICON": "images/loris-small.png",
        "PAGE_IMAGE": "images/loris.png",
        "GITHUB_REPO": "https://github.com/WSE-research/LoRiS-LLM-generated-Representations-of-SPARQL-queries",
        "DESCRIPTION": "Test description. Repo: %s — report bugs at %s or request features at %s.",
        "UPLOAD_DIRECTORY": tempfile.mkdtemp(prefix="loris-e2e-"),
    }


def test_app_imports_and_reaches_dry_run():
    proc = subprocess.run(
        [sys.executable, APP],
        cwd=REPO_ROOT,
        env=_app_env(),
        capture_output=True,
        text=True,
        timeout=180,
    )
    combined = proc.stdout + proc.stderr
    assert "Traceback (most recent call last)" not in combined, combined[-2000:]
    assert "ModuleNotFoundError" not in combined, combined[-2000:]
    assert "dry run enabled" in combined.lower() or proc.returncode in (0, -signal.SIGTERM, 143)
