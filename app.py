"""
Crowdlike Option B: Keep the existing React UI, run it inside Streamlit (iframe),
and optionally provide a Python backend (FastAPI) for data/services.

Goals
- Maximum UI fidelity (React stays intact)
- Minimal setup friction: `streamlit run app.py` from repo root
  - If `./dist` is missing, the wrapper will attempt to build it automatically.

Runtime
- Streamlit: http://127.0.0.1:8501
- React (served from dist): http://127.0.0.1:<frontend_port>
- Backend (FastAPI): http://127.0.0.1:<backend_port> (optional)
"""

from __future__ import annotations

import atexit
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"  # Vite build output (npm run build)
DIST_INDEX = DIST_DIR / "index.html"

# Optional: point Streamlit to a remotely hosted frontend (no local dist required).
# Useful for Streamlit Community Cloud and other environments without Node/npm.
#
# Set either:
# - Environment variable: CROWDLIKE_REMOTE_FRONTEND_URL
# - Streamlit secrets:     CROWDLIKE_REMOTE_FRONTEND_URL
#
# Example (Streamlit secrets):
#   CROWDLIKE_REMOTE_FRONTEND_URL = "https://your-frontend-host.example"


def _get_secret(key: str) -> Optional[str]:
    """Safely read Streamlit secrets without requiring them to be configured."""
    try:
        val = st.secrets.get(key)  # type: ignore[attr-defined]
        return str(val) if val else None
    except Exception:
        return None


def _remote_frontend_url() -> Optional[str]:
    return os.environ.get("CROWDLIKE_REMOTE_FRONTEND_URL") or _get_secret("CROWDLIKE_REMOTE_FRONTEND_URL")

DEFAULT_BACKEND_PORT = int(os.environ.get("CROWDLIKE_BACKEND_PORT", "8001"))
DEFAULT_FRONTEND_PORT = int(os.environ.get("CROWDLIKE_FRONTEND_PORT", "8502"))
START_BACKEND = os.environ.get("CROWDLIKE_START_BACKEND", "true").lower() in ("1", "true", "yes")


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) != 0


def _pick_port(preferred: int) -> int:
    if _port_is_free(preferred):
        return preferred
    # pick a random free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    """Run a command and return (return_code, combined_output)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env={**os.environ},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return int(p.returncode), p.stdout or ""
    except Exception as e:
        return 1, f"Failed to run {cmd!r}: {e}"


def _ensure_react_build() -> Tuple[bool, str]:
    """
    Ensure ./dist exists. If missing, try to build it automatically.
    Returns (ok, log_output).
    """
    if DIST_INDEX.exists():
        return True, ""

    # Avoid repeated attempts on Streamlit reruns unless the user explicitly retries.
    if st.session_state.get("_crowdlike_build_attempted"):
        return False, st.session_state.get("_crowdlike_build_log", "")

    st.session_state["_crowdlike_build_attempted"] = True

    # Preconditions
    if not (ROOT / "package.json").exists():
        log = "package.json not found in repo root; cannot build React app."
        st.session_state["_crowdlike_build_log"] = log
        return False, log

    npm = shutil.which("npm")
    if not npm:
        log = (
            "npm was not found on PATH, so this environment cannot build the React frontend.\n\n"
            "To run this on Streamlit Community Cloud (or any server without Node), do ONE of the following:\n"
            "  1) Build the frontend locally (npm install && npm run build) and commit ./dist to the repo; OR\n"
            "  2) Host the frontend elsewhere and set CROWDLIKE_REMOTE_FRONTEND_URL (env var or Streamlit secrets)."
        )
        st.session_state["_crowdlike_build_log"] = log
        return False, log

    logs = []

    # Install deps if node_modules is missing
    if not (ROOT / "node_modules").exists():
        install_cmd = ["npm", "ci"] if (ROOT / "package-lock.json").exists() else ["npm", "install"]
        rc, out = _run(install_cmd, cwd=ROOT)
        logs.append(f"$ {' '.join(install_cmd)}\n{out}")
        if rc != 0:
            log = "\n\n".join(logs)
            st.session_state["_crowdlike_build_log"] = log
            return False, log

    # Build
    build_cmd = ["npm", "run", "build"]
    rc, out = _run(build_cmd, cwd=ROOT)
    logs.append(f"$ {' '.join(build_cmd)}\n{out}")

    log = "\n\n".join(logs)
    st.session_state["_crowdlike_build_log"] = log

    return DIST_INDEX.exists(), log


def _start_process(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _ensure_started():
    """Start backend + frontend servers once per Streamlit session."""
    if "crowdlike_started" in st.session_state:
        return

    remote_ui = _remote_frontend_url()

    # If a remote UI is configured, we don't need a local build/server.
    # Otherwise, ensure dist exists (auto-build if possible).
    build_ok, build_log = (True, "") if remote_ui else _ensure_react_build()

    # Backend (FastAPI via uvicorn)
    backend_port = _pick_port(DEFAULT_BACKEND_PORT)
    backend_url = f"http://127.0.0.1:{backend_port}"

    backend_proc = None
    if START_BACKEND:
        backend_proc = _start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(backend_port),
                "--log-level",
                "warning",
            ],
            cwd=ROOT,
        )

    # Frontend (static dist server)
    frontend_proc = None
    frontend_url = remote_ui

    if not remote_ui:
        frontend_port = _pick_port(DEFAULT_FRONTEND_PORT)
        if build_ok and DIST_DIR.exists():
            frontend_url = f"http://127.0.0.1:{frontend_port}"
            frontend_proc = _start_process(
                [sys.executable, "-m", "http.server", str(frontend_port), "--bind", "127.0.0.1"],
                cwd=DIST_DIR,
            )

    st.session_state["crowdlike_started"] = True
    st.session_state["backend_url"] = backend_url
    st.session_state["frontend_url"] = frontend_url
    st.session_state["backend_proc"] = backend_proc
    st.session_state["frontend_proc"] = frontend_proc
    st.session_state["build_ok"] = build_ok
    st.session_state["build_log"] = build_log

    def _cleanup():
        for key in ("frontend_proc", "backend_proc"):
            p = st.session_state.get(key)
            try:
                if p and p.poll() is None:
                    p.terminate()
            except Exception:
                pass

    atexit.register(_cleanup)


def main():
    st.set_page_config(page_title="Crowdlike (Option B)", layout="wide")
    st.title("Crowdlike — Streamlit Wrapper (Option B)")
    st.caption("React UI preserved; Streamlit is the shell/orchestrator.")

    _ensure_started()

    backend_url = st.session_state.get("backend_url")
    frontend_url = st.session_state.get("frontend_url")
    build_ok = st.session_state.get("build_ok", False)
    build_log = st.session_state.get("build_log", "")

    with st.sidebar:
        st.header("Runtime")
        st.write("Backend (FastAPI):", backend_url if START_BACKEND else "disabled")
        st.write("Frontend (React):", frontend_url or "not available")
        st.divider()

        st.subheader("Run from repo root")
        st.code(
            "\n".join(
                [
                    "pip install -r requirements.txt",
                    "streamlit run app.py",
                ]
            ),
            language="bash",
        )

        st.caption(
            "If `./dist` is missing and npm is available, this wrapper will try to run `npm install` + `npm run build`."
        )

        st.subheader("Deploy to Streamlit")
        st.markdown(
            """
For Streamlit Community Cloud (public access):
- **Best**: build locally and commit `./dist` (so the server doesn't need Node/npm)
- **Alternative**: host the frontend elsewhere and set `CROWDLIKE_REMOTE_FRONTEND_URL`
"""
        )

        if not build_ok:
            if st.button("Retry React build"):
                st.session_state.pop("_crowdlike_build_attempted", None)
                st.session_state.pop("_crowdlike_build_log", None)
                st.rerun()

    if not frontend_url:
        st.error("React UI is not available yet (dist build missing or build failed).")

        st.markdown(
            """
**What you can do**
- If you're running locally: install **Node.js + npm**, then rerun `streamlit run app.py`.
- If you're deploying on Streamlit: build locally and commit `./dist`, **or** set `CROWDLIKE_REMOTE_FRONTEND_URL`.
- You can also click **Retry React build** in the sidebar.
"""
        )
        if build_log:
            with st.expander("Build log"):
                st.code(build_log)
        return

    # Embed the React app
    st.components.v1.iframe(frontend_url, height=900, scrolling=True)

    if START_BACKEND:
        st.markdown(f"Backend health: `{backend_url}/health`")


if __name__ == "__main__":
    main()
