"""Entrypoint for Hugging Face Spaces (runs FastAPI + ZeroGPU Gradio mount on port 7860)."""

import os

try:
    import spaces  # Must be imported before torch / sentence_transformers on ZeroGPU
except ImportError:

    class _SpacesFallback:
        @staticmethod
        def GPU(fn=None, **_kwargs):
            return fn if callable(fn) else (lambda f: f)

    spaces = _SpacesFallback()  # type: ignore[assignment]

import gradio as gr
import uvicorn

from app.main import app as fastapi_app


@spaces.GPU
def verify_engine(ping: str = "ScruCheckAI") -> str:
    """Top-level ZeroGPU function required by Hugging Face ZeroGPU startup."""
    return f"ScruCheckAI Scrutiny Engine Online ({ping})"


with gr.Blocks(title="ScruCheckAI Backend API") as demo:
    gr.Markdown(
        "# ScruCheckAI Scrutiny Backend\nAPI endpoints are active at `/api/v1` and `/healthz`."
    )
    ping_in = gr.Textbox(label="Ping", value="ScruCheckAI")
    ping_out = gr.Textbox(label="Status")
    ping_btn = gr.Button("Check Engine")
    ping_btn.click(fn=verify_engine, inputs=ping_in, outputs=ping_out)


app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
