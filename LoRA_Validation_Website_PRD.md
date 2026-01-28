# LoRA Validation Website — Product Requirements Document

## Overview

A web application for validating LoRA models across multiple image generation architectures (FLUX, Z-Image, Qwen, WAN). The tool runs standardized test prompts through each model, displays results in a grid comparison view, and exports validation reports as PDFs.

**Primary Use Case:** Internal tool for Trent Films to quickly validate trained LoRAs before deployment.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend (SvelteKit)                               │
│  - Hosted on Railway (or static)                    │
│  - LoRA selection dropdowns                         │
│  - Trigger word input                               │
│  - Generation status/progress                       │
│  - Grid display of results                          │
│  - PDF export (client-side, jsPDF)                  │
└─────────────────────────────────────────────────────┘
                         ↕ HTTP
┌─────────────────────────────────────────────────────┐
│  Backend (FastAPI on Railway)                       │
│  - /api/config — get current config                 │
│  - /api/loras — list available LoRAs                │
│  - /api/generate — submit workflow to ComfyUI       │
│  - /api/status/{id} — poll for completion           │
│  - /api/image/{filename} — proxy images             │
│  - config.py — portable model paths                 │
└─────────────────────────────────────────────────────┘
                         ↕ HTTP (localhost)
┌─────────────────────────────────────────────────────┐
│  ComfyUI (localhost:8188)                           │
│  - Runs headless                                    │
│  - Receives workflow JSON via REST API              │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | SvelteKit + Tailwind CSS |
| Backend | Python 3.11+ / FastAPI |
| PDF Export | jsPDF (client-side) |
| Generation | ComfyUI API |
| Deployment | Railway |

---

## File Structure

```
lora-validator/
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte          # Main UI
│   │   │   └── +layout.svelte        # App shell
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── LoraSelector.svelte
│   │   │   │   ├── GenerateButton.svelte
│   │   │   │   ├── StatusIndicator.svelte
│   │   │   │   ├── ResultGrid.svelte
│   │   │   │   └── PdfExport.svelte
│   │   │   ├── api.js                # Fetch wrappers
│   │   │   └── pdf.js                # jsPDF helper
│   │   └── app.css                   # Tailwind imports
│   ├── static/
│   ├── package.json
│   ├── svelte.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/
│   ├── app.py                        # FastAPI app
│   ├── comfy_client.py               # ComfyUI API wrapper
│   ├── workflow_loader.py            # Load + modify workflow JSON
│   ├── config.py                     # Model paths (editable)
│   ├── workflow_api.json             # Exported ComfyUI workflow
│   └── requirements.txt
│
├── README.md
└── .env.example
```

---

## Configuration System

### backend/config.py

```python
import os

CONFIG = {
    # ComfyUI connection
    "comfyui_url": os.getenv("COMFYUI_URL", "http://localhost:8188"),
    
    # Base paths (override for different servers)
    "paths": {
        "loras": os.getenv("LORA_PATH", "models/loras/"),
    },
    
    # Model files (override if locations differ)
    "models": {
        # FLUX
        "flux_unet": "FLUX1/flux1-dev.sft",
        "flux_vae": "ae.safetensors",
        "flux_clip_l": "clip_l.safetensors",
        "flux_t5": "t5xxl_fp16.safetensors",
        
        # WAN
        "wan_unet": "Wan2.1-T2V-14B/split_files/diffusion_models/",
        "wan_vae": "Wan2.1-T2V-14B/split_files/vae/",
        "wan_clip": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "wan_causvid_lora": "Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors",
        
        # QWEN
        "qwen_unet": "qwen_image_fp8_e4m3fn.safetensors",
        "qwen_clip": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
        "qwen_lightning_lora": "Qwen-Image-Lightning-8steps-V1.0.safetensors",
        
        # Z-Image
        "zimage_unet": "z_image_turbo_bf16.safetensors",
        "zimage_clip": "qwen_3_4b.safetensors",  # type: lumina2
    },
    
    # Workflow node IDs (from workflow_api.json)
    "nodes": {
        # LoRA inputs
        "flux_lora": "447",
        "zimage_lora": "480",
        "qwen_lora": "509",
        "wan_lora": "467",
        
        # Trigger word
        "trigger_word": "146",
        
        # Seeds (for reproducibility)
        "flux_seed": "445",
        "wan_seed": "472",
        "zimage_seed": "476",
        "qwen_seed": "488",
        
        # Batch size
        "batch_size": "544",
        
        # Output grids
        "output_combined_grid": "412",
        "output_flux_grid": "537",
        "output_wan_grid": "538",
        "output_zimage_grid": "539",
        "output_qwen_grid": "541",
    }
}
```

### Environment Variables (.env)

```bash
# .env.example
COMFYUI_URL=http://localhost:8188
LORA_PATH=models/loras/
```

---

## API Endpoints

### GET /api/loras

Returns available LoRA files grouped by architecture.

**Response:**
```json
{
  "flux": ["QueenCorgiFlux.safetensors", "OtherFlux.safetensors"],
  "zimage": ["QueenCorgiZImage.safetensors"],
  "qwen": ["QueenCorgiQwen.safetensors"],
  "wan": ["QueenCorgiWan.safetensors"]
}
```

**Implementation notes:**
- Scan the loras directory
- Group by naming convention OR subdirectories
- Consider convention: `{name}Flux.safetensors`, `{name}Qwen.safetensors`, etc.

---

### GET /api/config

Returns non-sensitive config for frontend (optional, for debugging).

**Response:**
```json
{
  "comfyui_url": "http://localhost:8188",
  "available_prompts": 9,
  "batch_size": 2
}
```

---

### POST /api/generate

Submits a validation job to ComfyUI.

**Request:**
```json
{
  "trigger_word": "Queen Corgi",
  "loras": {
    "flux": "QueenCorgiFlux.safetensors",
    "zimage": "QueenCorgiZImage.safetensors",
    "qwen": "QueenCorgiQwen.safetensors",
    "wan": "QueenCorgiWan.safetensors"
  },
  "seed": 12345,           // optional, random if omitted
  "batch_size": 2          // optional, default from config
}
```

**Response:**
```json
{
  "prompt_id": "abc123-def456",
  "status": "queued"
}
```

**Implementation:**
1. Load `workflow_api.json`
2. Inject trigger word into node `146`
3. Inject LoRA filenames into nodes `447`, `509`, etc.
4. Set seed (random or provided)
5. POST to `{comfyui_url}/prompt`
6. Return `prompt_id`

---

### GET /api/status/{prompt_id}

Polls ComfyUI for job status.

**Response (in progress):**
```json
{
  "done": false,
  "status": "running",
  "progress": null
}
```

**Response (complete):**
```json
{
  "done": true,
  "status": "complete",
  "outputs": {
    "combined_grid": "ComfyUI_00001_.png",
    "flux_grid": "ComfyUI_00002_.png",
    "wan_grid": "ComfyUI_00003_.png",
    "zimage_grid": "ComfyUI_00004_.png",
    "qwen_grid": "ComfyUI_00005_.png"
  }
}
```

**Implementation:**
1. GET `{comfyui_url}/history/{prompt_id}`
2. Parse outputs from configured node IDs
3. Return filenames or "not done"

---

### GET /api/image/{filename}

Proxies images from ComfyUI to frontend.

**Response:** Binary image data (PNG)

**Implementation:**
```python
@app.get("/api/image/{filename}")
def get_image(filename: str):
    r = requests.get(f"{CONFIG['comfyui_url']}/view?filename={filename}")
    return Response(content=r.content, media_type="image/png")
```

---

## Frontend Components

### 1. LoraSelector.svelte

```svelte
<script>
  export let label = "FLUX LoRA";
  export let options = [];
  export let value = "";
</script>

<div class="flex flex-col gap-1">
  <label class="text-sm font-medium text-gray-700">{label}</label>
  <select 
    bind:value
    class="border rounded-lg px-3 py-2 bg-white"
  >
    <option value="">Select a LoRA...</option>
    {#each options as lora}
      <option value={lora}>{lora}</option>
    {/each}
  </select>
</div>
```

---

### 2. Main Page (+page.svelte)

**State:**
```svelte
<script>
  import { onMount } from 'svelte';
  
  let triggerWord = "";
  let loras = { flux: "", zimage: "", qwen: "", wan: "" };
  let availableLoras = { flux: [], zimage: [], qwen: [], wan: [] };
  
  let loading = false;
  let promptId = null;
  let results = null;
  let error = null;
  
  onMount(async () => {
    const res = await fetch('/api/loras');
    availableLoras = await res.json();
  });
  
  async function generate() {
    loading = true;
    error = null;
    
    // Submit job
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_word: triggerWord, loras })
    });
    const data = await res.json();
    promptId = data.prompt_id;
    
    // Poll for completion
    while (true) {
      await new Promise(r => setTimeout(r, 2000));
      const status = await fetch(`/api/status/${promptId}`);
      const statusData = await status.json();
      
      if (statusData.done) {
        results = statusData.outputs;
        break;
      }
    }
    
    loading = false;
  }
</script>
```

**Layout:**
```svelte
<main class="max-w-6xl mx-auto p-8">
  <h1 class="text-3xl font-bold mb-8">LoRA Validation Tool</h1>
  
  <!-- Input Section -->
  <section class="bg-white rounded-xl shadow p-6 mb-8">
    <div class="grid grid-cols-2 gap-6">
      <!-- Trigger Word -->
      <div class="col-span-2">
        <label class="block text-sm font-medium mb-1">Trigger Word</label>
        <input 
          type="text" 
          bind:value={triggerWord}
          placeholder="e.g. Queen Corgi"
          class="w-full border rounded-lg px-4 py-2"
        />
      </div>
      
      <!-- LoRA Selectors -->
      <LoraSelector label="FLUX LoRA" options={availableLoras.flux} bind:value={loras.flux} />
      <LoraSelector label="Z-Image LoRA" options={availableLoras.zimage} bind:value={loras.zimage} />
      <LoraSelector label="Qwen LoRA" options={availableLoras.qwen} bind:value={loras.qwen} />
      <LoraSelector label="WAN LoRA" options={availableLoras.wan} bind:value={loras.wan} />
    </div>
    
    <button 
      on:click={generate}
      disabled={loading || !triggerWord}
      class="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-medium
             hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {loading ? 'Generating...' : 'Run Validation'}
    </button>
  </section>
  
  <!-- Loading State -->
  {#if loading}
    <section class="text-center py-12">
      <div class="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
      <p class="mt-4 text-gray-600">Running validation across 4 models...</p>
      <p class="text-sm text-gray-400">This may take a few minutes</p>
    </section>
  {/if}
  
  <!-- Results Section -->
  {#if results}
    <section class="bg-white rounded-xl shadow p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-semibold">Results: {triggerWord}</h2>
        <button 
          on:click={exportPDF}
          class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
        >
          Export to PDF
        </button>
      </div>
      
      <!-- Combined Grid -->
      <img 
        src="/api/image/{results.combined_grid}" 
        alt="Combined validation grid"
        class="w-full rounded-lg"
      />
      
      <!-- Or individual grids in a 2x2 layout -->
      <div class="grid grid-cols-2 gap-4 mt-6">
        <div>
          <h3 class="font-medium mb-2">FLUX</h3>
          <img src="/api/image/{results.flux_grid}" alt="FLUX results" class="rounded" />
        </div>
        <div>
          <h3 class="font-medium mb-2">Z-Image</h3>
          <img src="/api/image/{results.zimage_grid}" alt="Z-Image results" class="rounded" />
        </div>
        <div>
          <h3 class="font-medium mb-2">Qwen</h3>
          <img src="/api/image/{results.qwen_grid}" alt="Qwen results" class="rounded" />
        </div>
        <div>
          <h3 class="font-medium mb-2">WAN</h3>
          <img src="/api/image/{results.wan_grid}" alt="WAN results" class="rounded" />
        </div>
      </div>
    </section>
  {/if}
</main>
```

---

### 3. PDF Export (lib/pdf.js)

```javascript
import jsPDF from 'jspdf';

export async function exportValidationPDF(triggerWord, imageUrl) {
  const pdf = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: 'a4'
  });
  
  // Title
  pdf.setFontSize(24);
  pdf.text(`LoRA Validation Report`, 15, 20);
  
  // Metadata
  pdf.setFontSize(12);
  pdf.text(`Trigger Word: ${triggerWord}`, 15, 30);
  pdf.text(`Generated: ${new Date().toLocaleString()}`, 15, 37);
  
  // Fetch image as base64
  const response = await fetch(imageUrl);
  const blob = await response.blob();
  const base64 = await blobToBase64(blob);
  
  // Add image (fit to page width)
  pdf.addImage(base64, 'PNG', 15, 45, 267, 0); // auto-height
  
  // Save
  pdf.save(`${triggerWord.replace(/\s+/g, '_')}_validation.pdf`);
}

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(blob);
  });
}
```

---

## Backend Implementation

### backend/app.py

```python
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import os

from config import CONFIG
from workflow_loader import load_workflow, list_loras

app = FastAPI()

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    trigger_word: str
    loras: dict[str, str]
    seed: Optional[int] = None
    batch_size: Optional[int] = None


@app.get("/api/loras")
def get_loras():
    return list_loras(CONFIG["paths"]["loras"])


@app.post("/api/generate")
def generate(req: GenerateRequest):
    workflow = load_workflow(
        trigger_word=req.trigger_word,
        loras=req.loras,
        seed=req.seed,
        batch_size=req.batch_size
    )
    
    r = requests.post(
        f"{CONFIG['comfyui_url']}/prompt",
        json={"prompt": workflow}
    )
    
    return {"prompt_id": r.json()["prompt_id"], "status": "queued"}


@app.get("/api/status/{prompt_id}")
def get_status(prompt_id: str):
    r = requests.get(f"{CONFIG['comfyui_url']}/history/{prompt_id}")
    history = r.json()
    
    if prompt_id not in history:
        return {"done": False, "status": "running"}
    
    outputs = history[prompt_id].get("outputs", {})
    nodes = CONFIG["nodes"]
    
    result = {"done": True, "status": "complete", "outputs": {}}
    
    # Map node outputs to friendly names
    output_map = {
        nodes["output_combined_grid"]: "combined_grid",
        nodes["output_flux_grid"]: "flux_grid",
        nodes["output_wan_grid"]: "wan_grid",
        nodes["output_zimage_grid"]: "zimage_grid",
        nodes["output_qwen_grid"]: "qwen_grid",
    }
    
    for node_id, key in output_map.items():
        if node_id in outputs and "images" in outputs[node_id]:
            result["outputs"][key] = outputs[node_id]["images"][0]["filename"]
    
    return result


@app.get("/api/image/{filename}")
def get_image(filename: str):
    r = requests.get(f"{CONFIG['comfyui_url']}/view?filename={filename}")
    return Response(content=r.content, media_type="image/png")
```

---

### backend/workflow_loader.py

```python
import json
import random
import os
from pathlib import Path
from config import CONFIG

WORKFLOW_PATH = Path(__file__).parent / "workflow_api.json"

def load_workflow(trigger_word: str, loras: dict, seed: int = None, batch_size: int = None):
    with open(WORKFLOW_PATH) as f:
        workflow = json.load(f)
    
    nodes = CONFIG["nodes"]
    
    # Set trigger word
    workflow[nodes["trigger_word"]]["inputs"]["a"] = trigger_word
    
    # Set LoRAs
    if loras.get("flux"):
        workflow[nodes["flux_lora"]]["inputs"]["lora_name"] = loras["flux"]
    if loras.get("zimage"):
        workflow[nodes["zimage_lora"]]["inputs"]["lora_name"] = loras["zimage"]
    if loras.get("qwen"):
        workflow[nodes["qwen_lora"]]["inputs"]["lora_name"] = loras["qwen"]
    if loras.get("wan"):
        workflow[nodes["wan_lora"]]["inputs"]["lora_name"] = loras["wan"]
    
    # Set seed (same across all models for fair comparison)
    seed = seed or random.randint(0, 2**32)
    for seed_node in ["flux_seed", "wan_seed", "qwen_seed", "zimage_seed"]:
        node_id = nodes.get(seed_node)
        if node_id and node_id in workflow:
            workflow[node_id]["inputs"]["seed"] = seed
    
    # Set batch size
    if batch_size:
        workflow[nodes["batch_size"]]["inputs"]["Number"] = str(batch_size)
    
    return workflow


def list_loras(lora_path: str) -> dict:
    """List LoRAs grouped by architecture based on naming convention."""
    result = {"flux": [], "zimage": [], "qwen": [], "wan": []}
    
    # Option 1: Group by suffix naming convention
    # e.g., QueenCorgiFlux.safetensors, QueenCorgiQwen.safetensors
    
    lora_dir = Path(lora_path)
    if not lora_dir.exists():
        return result
    
    for file in lora_dir.glob("*.safetensors"):
        name = file.name
        name_lower = name.lower()
        
        if "flux" in name_lower:
            result["flux"].append(name)
        elif "zimage" in name_lower or "z-image" in name_lower:
            result["zimage"].append(name)
        elif "qwen" in name_lower:
            result["qwen"].append(name)
        elif "wan" in name_lower:
            result["wan"].append(name)
    
    return result
```

---

### backend/requirements.txt

```
fastapi>=0.100.0
uvicorn>=0.22.0
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

---

## Deployment Notes

### Railway Setup

1. **Backend service:**
   - Connect repo
   - Set build command: `pip install -r backend/requirements.txt`
   - Set start command: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Add env vars: `COMFYUI_URL`, `LORA_PATH`

2. **Frontend service:**
   - Connect same repo
   - Set root directory: `frontend`
   - SvelteKit will auto-detect build settings

3. **ComfyUI:**
   - Runs on same server (production)
   - Start with: `python main.py --listen 127.0.0.1 --port 8188`

---

## Implementation Checklist

### Phase 1: Backend Core — COMPLETE
- [x] Create FastAPI app skeleton
- [x] Implement config.py with all node IDs from workflow
- [x] Implement /api/generate endpoint
- [x] Implement /api/status endpoint (with reference image extraction)
- [x] Implement /api/image proxy (with type whitelist validation)
- [x] Implement /api/loras listing (all LoRAs shown, architecture-matched first)
- [x] Implement /api/prompts endpoint
- [x] Implement /health endpoint
- [x] Test against local ComfyUI

### Phase 2: Frontend Core — COMPLETE
- [x] Scaffold SvelteKit 5 + Tailwind v4
- [x] Create LoraSelector component (with LED toggle switches)
- [x] Create main page layout (dark metal control panel aesthetic)
- [x] Implement API fetch calls
- [x] Implement polling logic (exponential backoff, cancel button)
- [x] Display results grid (combined + per-model, lightbox, reference image)
- [x] Create PromptPanel (slider 0-9, editable textareas)

### Phase 3: PDF Export — COMPLETE
- [x] Install jsPDF
- [x] Create exportValidationPDF function (multi-page: reference image + combined grid + per-model grids)
- [x] Wire up export button
- [x] Test with actual output images

### Phase 4: Polish — COMPLETE
- [x] Error handling (ComfyUI down, invalid LoRA, timeout → 504, connection → 503)
- [x] Loading states and progress feedback (LED spinner, status indicator)
- [x] Industrial metal UI design (8 polish tasks)
- [x] Security hardening (CORS, input validation, type whitelisting)
- [x] Structured logging

### Phase 5: Deployment
- [ ] Test on work server
- [ ] Adjust config.py for production paths
- [ ] Deploy to Railway
- [ ] Verify end-to-end flow

---

## Workflow Node Reference

From `Lora-v3-API.json`:

| Node ID | Class | Purpose | Dynamic? |
|---------|-------|---------|----------|
| 146 | JWStringConcat | Trigger word prefix | ✅ Yes |
| 447 | LoraLoader | FLUX LoRA | ✅ Yes |
| 480 | LoraLoader | Z-Image LoRA | ✅ Yes |
| 509 | LoraLoaderModelOnly | Qwen LoRA | ✅ Yes |
| 467 | LoraLoaderModelOnly | WAN LoRA | ✅ Yes |
| 445 | KSampler | FLUX seed/steps | ✅ Seed |
| 476 | KSampler | Z-Image seed/steps | ✅ Seed |
| 488 | KSampler | Qwen seed/steps | ✅ Seed |
| 472 | KSampler | WAN seed/steps | ✅ Seed |
| 544 | Int | Batch size | ✅ Yes |
| 412 | FL_ImageBatchToGrid | Combined output grid | Output |
| 537 | ImageTextGrid | FLUX output grid | Output |
| 538 | ImageTextGrid | WAN output grid | Output |
| 539 | ImageTextGrid | Z-Image output grid | Output |
| 541 | ImageTextGrid | Qwen output grid | Output |
| 535 | SaveImage | Final saved image | Output |

---

## Test Prompts (Built into Workflow)

The workflow includes 9 standardized test prompts:

1. Golden hour portrait, shallow DOF, 35mm film grain
2. Rain-slicked Tokyo street at night, neon reflections
3. Corporate headshot, studio lighting
4. Running through forest, motion blur, dynamic pose
5. Leather armchair by firelight, reading a book
6. Warehouse chiaroscuro, dust particles, cinematic
7. Outdoor café, Mediterranean, candid laughter
8. 1970s film photo, vintage car, nostalgic
9. Cliff overlooking mountains at dawn, epic LOTR atmosphere

These test a range of lighting, settings, motion, and styles.

---

## Future Enhancements (Out of Scope for V1)

- [ ] LoRA upload (drag & drop .safetensors)
- [x] Custom prompt injection (override test prompts) — DONE: editable prompts with slider
- [ ] Side-by-side comparison mode
- [ ] History/saved validations
- [ ] Batch validation (multiple LoRAs at once)
- [ ] WebSocket for real-time progress
- [ ] Reference image upload (currently hardcoded in workflow as node 143)
