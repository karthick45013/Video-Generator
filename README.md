# Wan2.1 Text-to-Video Generator 🎬

A fully **local**, unlimited text-to-video generator powered by [Wan-AI/Wan2.1-T2V-1.3B-Diffusers](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B-Diffusers) from Hugging Face.

- ✅ No token limits, no time limits
- ✅ Runs 100% on your machine
- ✅ GPU (CUDA) or CPU supported
- ✅ Live progress bar during generation
- ✅ Download generated videos as MP4

---

## Requirements

- Python 3.10+
- CUDA GPU with ≥ 8 GB VRAM *(strongly recommended; CPU works but is very slow)*
- ~10 GB free disk space (model weights + outputs)

---

## Installation

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. (GPU only) Install PyTorch with CUDA — if not already installed
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

## Running

```bash
python run.py
```

The server starts at **http://127.0.0.1:8000** and your browser opens automatically.

> ⚠️ **First launch** will download ~5 GB of model weights from Hugging Face. Subsequent launches use the local cache.

---

## Usage

1. Enter a descriptive **prompt** (e.g., *"A drone shot of a dense jungle waterfall at sunrise"*)
2. Optionally add a **negative prompt** and tweak settings (frames, resolution, steps, FPS)
3. Click **Generate Video** — a live progress bar shows each diffusion step
4. Once done, a video player appears — watch in-browser or download the `.mp4`

### ⌨️ Shortcut
Press **Ctrl + Enter** anywhere on the page to start generation.

---

## Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Frames | 81 | Total frames — 81 ≈ 5 s at 16 fps |
| Width × Height | 848 × 480 | Output resolution |
| Steps | 50 | Diffusion steps (more = higher quality) |
| CFG Scale | 7.5 | How closely to follow the prompt |
| FPS | 16 | Playback speed |
| Seed | Random | Set for reproducible results |

---

## Project Structure

```
├── backend/
│   ├── main.py          # FastAPI app + Wan2.1 model
│   └── requirements.txt
├── frontend/
│   ├── index.html       # UI
│   ├── style.css        # Dark glassmorphism design
│   └── app.js           # Fetch / SSE / video display
├── outputs/             # Generated MP4 files (auto-created)
├── run.py               # Launcher
└── README.md
```

---

## License

Model weights: [Apache 2.0](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B-Diffusers) · Application code: MIT
