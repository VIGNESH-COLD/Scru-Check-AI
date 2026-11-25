"""Entrypoint for Hugging Face Spaces (runs FastAPI backend on port 7860)."""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
