"""Backward-compatible entrypoint.

Use:
  streamlit run app.py

This file simply forwards to app.py.
"""

from app import main

if __name__ == "__main__":
    main()
