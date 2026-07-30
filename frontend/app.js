const API_BASE = "http://127.0.0.1:8000";

let currentJobId = null;
let sseSource = null;

// ── Generate ──────────────────────────────────────────────────────────────────
async function generateVideo() {
  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) { showError("Please enter a prompt."); return; }

  clearError();
  hideResult();
  showProgress("Sending request to the model…", 0);
  setGenerating(true);

  const payload = {
    prompt,
    negative_prompt: document.getElementById("negative-prompt").value || "low quality, blurry, distorted, watermark",
    cpu_safe_mode: true,
    num_frames: parseInt(document.getElementById("num-frames").value, 10),
    width: parseInt(document.getElementById("width").value, 10),
    height: parseInt(document.getElementById("height").value, 10),
    num_inference_steps: parseInt(document.getElementById("steps").value, 10),
    guidance_scale: parseFloat(document.getElementById("guidance").value),
    fps: parseInt(document.getElementById("fps").value, 10),
    seed: document.getElementById("seed").value
      ? parseInt(document.getElementById("seed").value, 10)
      : null,
  };

  try {
    const resp = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || "Server error");
    }

    const data = await resp.json();
    currentJobId = data.job_id;
    startSSE(data.job_id);

    // Keep the progress panel visible while the job runs.
    updateProgress("Queued…", 0);

  } catch (e) {
    stopSSE();
    setGenerating(false);
    hideProgress();
    showError(`Generation failed: ${e.message}`);
  }
}

// ── SSE progress ──────────────────────────────────────────────────────────────
function startSSE(jobId) {
  stopSSE();
  sseSource = new EventSource(`${API_BASE}/progress/${jobId}`);
  sseSource.onmessage = (e) => {
    const info = JSON.parse(e.data);
    const total = info.total || 1;
    const step  = info.step  || 0;
    const pct   = Math.min(Math.round((step / total) * 100), 100);

    let label = "Generating…";
    if (info.status === "starting")    label = "Initialising model…";
    if (info.status === "generating")  label = `Diffusing step ${step} / ${total}`;
    if (info.status === "done")        label = "✅ Done!";
    if (info.status === "error")       label = "❌ Error";

    updateProgress(label, pct);
    if (info.status === "done") {
      stopSSE();
      hideProgress();
      currentJobId = null;
      showVideo(`${API_BASE}${info.video_url}`);
      setGenerating(false);
    }
    if (info.status === "error") {
      stopSSE();
      hideProgress();
      currentJobId = null;
      showError(info.error ? `Generation failed: ${info.error}` : "Generation failed.");
      setGenerating(false);
    }
  };
}

function stopSSE() {
  if (sseSource) { sseSource.close(); sseSource = null; }
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function setGenerating(on) {
  const btn = document.getElementById("generate-btn");
  const txt = document.getElementById("btn-text");
  const spinner = document.getElementById("btn-spinner");
  btn.disabled = on;
  txt.textContent = on ? "Generating…" : "Generate Video";
  spinner.classList.toggle("hidden", !on);
}

function showProgress(label, pct) {
  document.getElementById("progress-section").classList.remove("hidden");
  updateProgress(label, pct);
}

function updateProgress(label, pct) {
  document.getElementById("progress-label").textContent = label;
  document.getElementById("progress-pct").textContent = `${pct}%`;
  document.getElementById("progress-bar").style.width = `${pct}%`;
}

function hideProgress() {
  document.getElementById("progress-section").classList.add("hidden");
}

function showVideo(url) {
  const section = document.getElementById("result-section");
  const player  = document.getElementById("video-player");
  const dlLink  = document.getElementById("download-link");
  player.src = url;
  dlLink.href = url;
  dlLink.setAttribute("download", "wan2_video.mp4");
  section.classList.remove("hidden");
  section.scrollIntoView({ behavior: "smooth" });
}

function hideResult() {
  document.getElementById("result-section").classList.add("hidden");
}

function showError(msg) {
  const box = document.getElementById("error-box");
  document.getElementById("error-msg").textContent = msg;
  box.classList.remove("hidden");
}

function clearError() {
  document.getElementById("error-box").classList.add("hidden");
}

function resetForm() {
  hideResult();
  hideProgress();
  clearError();
  document.getElementById("prompt").value = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Keyboard shortcut: Ctrl+Enter to generate ─────────────────────────────────
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") generateVideo();
});
