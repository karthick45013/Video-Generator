# Wan2.1 Text-to-Video Generator

A local text-to-video app powered by [Wan-AI/Wan2.1-T2V-1.3B-Diffusers](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B-Diffusers).

## What it does

- Turns a text prompt into a short video
- Runs locally on your machine
- Shows live generation progress
- Lets you download the result as an MP4

## Requirements

- Python 3.10 or newer
- A CUDA GPU with at least 8 GB VRAM is strongly recommended
- About 10 GB of free disk space for model files and outputs

## Install

```bash
pip install -r backend/requirements.txt
```

If you need CUDA-enabled PyTorch, install it separately:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Run the app

```bash
python run.py
```

The server runs at:

```text
http://127.0.0.1:8000
```

The browser should open automatically.

## First run

The first launch downloads the model files from Hugging Face. That can take a while.

## How to use it

1. Enter a prompt.
2. Optionally adjust the negative prompt and generation settings.
3. Click **Generate Video**.
4. Wait for the progress bar to finish.
5. Watch the video in the browser or download it as MP4.

## Shortcuts

- Press `Ctrl + Enter` to start generation.

## Default settings

| Setting | Default | Notes |
| --- | --- | --- |
| Frames | 33 | Safer default for local generation |
| Width | 480 | Output width |
| Height | 272 | Output height |
| Steps | 20 | Fewer steps is faster |
| CFG Scale | 7.5 | Prompt strength |
| FPS | 16 | Playback speed |
| Seed | Random | Use a number for repeatable results |

## Project layout

```text
backend/
  main.py
  requirements.txt
frontend/
  app.js
  index.html
  style.css
outputs/
run.py
README.md
```

## Notes

- CPU-only generation may be slow or unstable on some machines.
- For best results, use a CUDA GPU.

## License

- Model weights: Apache 2.0
- Application code: MIT
