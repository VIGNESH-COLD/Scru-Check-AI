"""Entrypoint for Hugging Face Spaces (runs Gradio ZeroGPU lifecycle + FastAPI backend on port 7860)."""
# ruff: noqa: I001

import os
import threading

import spaces  # noqa: I001 - Must be imported before gradio / torch on ZeroGPU
import gradio as gr
from starlette.routing import BaseRoute, Match
from starlette.types import Receive, Scope, Send

from app.main import app as fastapi_app


@spaces.GPU
def verify_engine(ping: str = "ScruCheckAI") -> str:
    """Top-level ZeroGPU function registered with Gradio for Hugging Face ZeroGPU startup."""
    return f"ScruCheckAI Scrutiny Engine Online ({ping})"


class PrefixPassthroughRoute(BaseRoute):
    """Route /healthz and /api/* directly to the FastAPI app without stripping path prefixes."""

    def __init__(self, prefixes: list[str], target_app) -> None:
        self.prefixes = tuple(prefixes)
        self.app = target_app

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            for prefix in self.prefixes:
                if path == prefix or path.startswith(prefix + "/"):
                    return Match.FULL, {"endpoint": self.app}
        return Match.NONE, {}

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.app(scope, receive, send)


with gr.Blocks(title="ScruCheckAI Backend API") as demo:
    gr.Markdown(
        "# ScruCheckAI Scrutiny Backend\n"
        "API endpoints are active at `/api/v1` and `/healthz`."
    )
    ping_in = gr.Textbox(label="Ping", value="ScruCheckAI")
    ping_out = gr.Textbox(label="Status")
    ping_btn = gr.Button("Check Engine")
    ping_btn.click(fn=verify_engine, inputs=ping_in, outputs=ping_out)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue()
    gradio_app, _, _ = demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        ssr_mode=False,
        prevent_thread_lock=True,
    )
    gradio_app.router.routes.insert(
        0, PrefixPassthroughRoute(["/healthz", "/api"], fastapi_app)
    )
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        demo.close()
