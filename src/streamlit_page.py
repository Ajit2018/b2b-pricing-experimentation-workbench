"""Compatibility entry point for the Streamlit workbench.

The deployed and authoritative application lives in repository-root ``app.py``.
This wrapper prevents the historical ``src/streamlit_page.py`` copy from
silently drifting away from the deployed implementation.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import main  # noqa: E402


if __name__ == "__main__":
    main()
