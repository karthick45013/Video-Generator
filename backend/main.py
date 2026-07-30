import asyncio
import os
import uuid
import json
import threading
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# ── lazy model import so the server starts fast ──────────────────────────────
pipeline = None
device = None
pipeline_lock = threading.Lock()
progress_store: dict[str, dict] = {}  # job_id -> {"step": int, "total": int, "status": str}

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
FRONTEND_DIR = BASE_DIR / "frontend"

# ─── Startup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="Wan2.1 Text-to-Video Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated videos directory
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Serve frontend
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def load_model(cpu_safe_mode: bool = False):
    """Load Wan2.1-T2V-1.3B pipeline once."""
    global pipeline, device
    if pipeline is not None:
        return

    with pipeline_lock:
        if pipeline is not None:
            return

        print("⏳  Loading Wan2.1-T2V-1.3B model … (first run downloads ~5 GB)")
        from diffusers import AutoencoderKLWan, WanPipeline

        MODEL_ID = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # CPU inference on Windows is much more stable in float32.
        # bfloat16 is not consistently supported by all CPU backends here.
        dtype = torch.float16 if device == "cuda" else torch.float32

        print(f"🖥  Using device: {device.upper()}  |  dtype: {dtype}")

        load_kwargs = {
            "torch_dtype": dtype,
            "low_cpu_mem_usage": True,
        }

        # CPU-safe mode avoids the extra standalone VAE load, which is the
        # most likely place for Windows to run out of memory and crash.
        if cpu_safe_mode and device == "cpu":
            pipeline = WanPipeline.from_pretrained(MODEL_ID, **load_kwargs)
        else:
            vae = AutoencoderKLWan.from_pretrained(
                MODEL_ID,
                subfolder="vae",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
            pipeline = WanPipeline.from_pretrained(
                MODEL_ID,
                vae=vae,
                **load_kwargs,
            )

        # Memory optimisations
        if device == "cuda":
            pipeline.enable_model_cpu_offload()
        else:
            # Move to CPU explicitly (sequential offload not helpful for pure-CPU inference)
            pipeline = pipeline.to("cpu")

        print("✅  Model loaded.")


# ─── Request / Response models ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    job_id: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = "low quality, blurry, distorted, watermark"
    cpu_safe_mode: bool = True
    # CPU-safe defaults: 33 frames (~2 s at 16 fps) at 480x272 takes ~8-12 GB RAM.
    # Users with a CUDA GPU can safely increase these.
    num_frames: int = 33
    width: int = 480
    height: int = 272
    num_inference_steps: int = 20
    guidance_scale: float = 5.0
    fps: int = 16
    seed: Optional[int] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Redirect to the frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "device": device or "not loaded yet"}


@app.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    """Server-Sent Events stream for generation progress."""

    async def event_generator():
        while True:
            info = progress_store.get(job_id)
            if info is None:
                yield {"data": json.dumps({"status": "not_found"})}
                break
            yield {"data": json.dumps(info)}
            if info.get("status") in ("done", "error"):
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Queue a video generation job and return a job id immediately."""

    job_id = req.job_id or str(uuid.uuid4())
    out_path = OUTPUTS_DIR / f"{job_id}.mp4"
    progress_store[job_id] = {
        "step": 0,
        "total": req.num_inference_steps,
        "status": "queued",
        "job_id": job_id,
    }

    def run_generation():
        try:
            load_model(cpu_safe_mode=req.cpu_safe_mode)
            progress_store[job_id]["status"] = "generating"

            generator = None
            if req.seed is not None:
                generator = torch.Generator(device=device).manual_seed(req.seed)

            def step_callback(pipeline_self, i, t, callback_kwargs):
                progress_store[job_id]["step"] = i + 1
                progress_store[job_id]["status"] = "generating"
                return callback_kwargs

            output = pipeline(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                num_frames=req.num_frames,
                width=req.width,
                height=req.height,
                num_inference_steps=req.num_inference_steps,
                guidance_scale=req.guidance_scale,
                generator=generator,
                callback_on_step_end=step_callback,
                callback_on_step_end_tensor_inputs=["latents"],
            )

            frames = output.frames[0]

            import imageio
            import numpy as np

            writer = imageio.get_writer(str(out_path), fps=req.fps, codec="libx264", quality=8)
            for frame in frames:
                writer.append_data(np.array(frame))
            writer.close()

            progress_store[job_id]["status"] = "done"
            progress_store[job_id]["video_url"] = f"/outputs/{job_id}.mp4"
        except Exception as exc:
            progress_store[job_id]["status"] = "error"
            progress_store[job_id]["error"] = str(exc)

    threading.Thread(target=run_generation, daemon=True).start()

    return JSONResponse({
        "job_id": job_id,
        "status": "queued",
        "progress_url": f"/progress/{job_id}",
        "video_url": f"/outputs/{job_id}.mp4",
    })
