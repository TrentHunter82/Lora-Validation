# LoRA Validation — Session Handoff

## Project Status
Fully functional with polished industrial UI. Backend serves ComfyUI workflows with configurable prompts and selectable models. Frontend features a dark metal control panel aesthetic with editable prompts, model toggles, LED indicators, lightbox image viewer, reference image display, and multi-page PDF export.

## Architecture

```
f:\Lora-Validation\
├── backend/                    # FastAPI (Python)
│   ├── app.py                  # Endpoints: /health, /api/config, /api/prompts, /api/loras, /api/generate, /api/status/{id}, /api/image/{filename}
│   ├── config.py               # CONFIG dict with ComfyUI URL, model paths, workflow node IDs, model pipeline node maps
│   ├── workflow_loader.py      # Loads workflow_api.json, injects trigger word/LoRAs/seed/prompts, removes disabled model pipelines
│   ├── workflow_api.json       # ComfyUI workflow (exported from ComfyUI)
│   └── requirements.txt        # fastapi, uvicorn, requests, python-dotenv, pydantic
├── frontend/                   # SvelteKit 5 + Tailwind v4
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte    # Main page: config panel, prompt panel, generate, poll, results
│   │   │   └── +layout.svelte  # App shell (dark metal bg + noise texture)
│   │   ├── lib/
│   │   │   ├── api.js          # fetchLoras, fetchPrompts, generate, pollStatus, imageUrl
│   │   │   ├── pdf.js          # exportValidationPDF (landscape A4, multi-page, jsPDF)
│   │   │   └── components/
│   │   │       ├── LoraSelector.svelte      # Dropdown per architecture + LED enable/disable toggle
│   │   │       ├── GenerateButton.svelte    # Metal gradient button with shimmer + dynamic label
│   │   │       ├── StatusIndicator.svelte   # LED-orange spinner + status text
│   │   │       ├── ResultGrid.svelte        # Dark glass card with reference image, combined + 2x2 model grids, lightbox, PDF export
│   │   │       └── PromptPanel.svelte       # Slider (0-9) for prompt count + editable textareas
│   │   └── app.css             # Tailwind v4 @theme (metal colors, LED colors) + custom utilities
│   ├── vite.config.js          # Tailwind plugin + /api proxy → localhost:8000
│   └── package.json
├── .env.example
├── LoRA_Validation_Website_PRD.md
├── CLAUDE.md
└── HANDOFF.md
```

## How to Run

1. **ComfyUI** (WSL): `cd ~/ComfyUI && python main.py --listen 0.0.0.0 --port 8188`
2. **Backend** (Windows): `cd backend && uvicorn app:app --reload --port 8000`
3. **Frontend** (Windows): `cd frontend && npm run dev` → opens at `http://localhost:5173`

The vite dev server proxies `/api/*` to `localhost:8000`.

## Tech Stack
- **Frontend**: SvelteKit (Svelte 5 runes syntax — `$props()`, `$state()`, `$bindable()`, `$derived()`, `{@render}`)
- **Styling**: Tailwind CSS v4 (via `@tailwindcss/vite` plugin, `@import "tailwindcss"` + `@theme` directive for custom colors)
- **PDF**: jsPDF (client-side, multi-page with reference image + per-model grids)
- **Backend**: FastAPI + requests (proxies to ComfyUI)
- **ComfyUI**: WSL2, conda env `radial`, port 8188

## What Works

### Core Functionality
- LoRA dropdowns populate from ComfyUI's `/object_info/LoraLoader` API
- LoRAs auto-grouped by architecture keyword (flux/zimage/qwen/wan); all LoRAs shown in every dropdown, architecture-matched ones listed first
- **Model toggles**: Each LoRA selector has an LED toggle switch to enable/disable that model pipeline
- Disabled models are fully removed from the workflow (all pipeline nodes stripped, combined grid rewired)
- Generate submits workflow to ComfyUI, returns prompt_id
- Polls `/api/status/{prompt_id}` with exponential backoff (2s → 30s max) until done
- Cancel button appears during generation to abort polling
- **Results display**: Combined grid (full width) + individual model grids (2x2), each clickable to open lightbox
- **Reference image**: Displayed as 64x64 thumbnail in results header (top-left), clickable for lightbox. Extracted from ComfyUI history's workflow prompt data (node 143 LoadImage)
- **Lightbox**: Full-screen image viewer with click-to-close and Escape key support
- **PDF export**: Multi-page landscape A4 — page 1 has reference image + title + combined grid, subsequent pages have one per-model grid each
- Image proxy passes full ComfyUI params (filename, subfolder, type) through `/api/image/{filename}`

### Prompt System
- **9 default prompts** loaded from the workflow JSON via `GET /api/prompts`
- **Slider control** (0-9) dynamically shows/hides prompt textareas
- Each visible prompt is editable — changes are sent to the backend on generate
- Backend reorders prompts (enabled first) and sets the StringListCowboy node limit to active count
- Generate button shows active counts: "Run Validation (5 prompts, 3 models)"

### Industrial UI Design
All 8 polish tasks completed. The frontend uses a dark metal control panel aesthetic:

- **Dark metal background**: `bg-metal-950` with SVG noise texture overlay
- **Glass panels**: Gradient `from-metal-800/80 to-metal-900/90` with `backdrop-blur-sm`, `border-white/5`, brushed metal texture
- **LED indicators**: Green (connected/active), orange (in-progress), red (error/disconnected) with 2s pulse glow animation
- **Metal buttons**: Gradient `metal-600→700`, raised shadow, shimmer sweep on hover, proper active/disabled states
- **Recessed inputs**: Dark `bg-metal-900` with inset shadow (`recessed` class), subtle focus ring
- **LED toggle switches**: Mini pill toggles with glowing green dot for enabled state
- **Custom scrollbar**: 8px, `metal-700` thumb on `metal-900` track
- **Status spinner**: Orange LED-colored with glow box-shadow

### Design System (app.css)
Tailwind v4 `@theme` block defines:
- **Metal color scale**: metal-50 through metal-950 (zinc-based dark palette)
- **LED colors**: `--color-led-green: #22c55e`, `--color-led-orange: #f97316`, `--color-led-red: #ef4444`

Custom CSS utilities:
- `.brushed-metal` — Diagonal cross-hatch pattern at 2% white
- `.noise-texture` — SVG fractalNoise pseudo-element at 3% opacity
- `.led-glow` — 2s pulsing box-shadow animation
- `.metal-shimmer` — Hover-activated gradient sweep (pointer-events: none on pseudo)
- `.recessed` — Inset shadow for sunken appearance
- `.raised-metal` — Highlight/shadow combo for 3D raised effect
- `.focus-metal` — Custom focus ring in metal-500

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check — verifies ComfyUI connectivity |
| GET | `/api/config` | App metadata (ComfyUI URL, prompt count, prompt limit) |
| GET | `/api/prompts` | Returns 9 default prompts from workflow JSON |
| GET | `/api/loras` | Lists LoRAs grouped by architecture (all shown, matched first) |
| POST | `/api/generate` | Submits workflow; accepts `trigger_word`, `loras`, `prompts`, `models_enabled` |
| GET | `/api/status/{prompt_id}` | Polls for completion; returns image objects with filename/subfolder/type + reference_image |
| GET | `/api/image/{filename}` | Proxies images from ComfyUI with subfolder/type query params (type whitelist: output/input/temp) |

## Backend Details

### Workflow Node IDs (config.py)

**Reference image:** node 143 (LoadImage, "DataSet Reference Image")
**LoRA loaders:** 447 (FLUX), 480 (Z-Image), 509 (Qwen), 467 (WAN)
**Trigger word:** node 146, field `a`
**Seeds:** 445 (FLUX), 472 (WAN), 476 (Z-Image), 488 (Qwen)
**Prompt limit:** node 544 (Int, "Batch Size"), field `Number` (string) — controls StringListCowboy limit
**Prompt list:** node 430 (StringListCowboy) — takes 9 prompt inputs (value_1..value_9) with prefix from trigger word
**Prompt nodes:** 151, 150, 229, 232, 233, 234, 230, 231, 235 (PrimitiveStringMultiline)

**Grid composition:**
- Nodes 537/538/539/541 (ImageTextGrid) compose per-model images into labeled grids (images_per_row=3)
- Node 534 (ImpactMakeImageBatch) collects model grids
- Node 412 (FL_ImageBatchToGrid) creates combined grid (images_per_row from node 544)
- Node 535 (SaveImage) saves combined grid

**Output nodes (PreviewImage/SaveImage):**
- 535: combined_grid (SaveImage)
- 540: flux_grid (PreviewImage)
- 397: wan_grid (PreviewImage)
- 137: zimage_grid (PreviewImage)
- 542: qwen_grid (PreviewImage)

### Model Pipeline Node Maps (for removal when disabled)

| Model | Exclusive Nodes |
|-------|----------------|
| FLUX | 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 537, 540 |
| WAN | 463, 464, 465, 466, 467, 468, 469, 470, 472, 473, 536, 538, 397 |
| Z-Image | 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 539, 137 |
| Qwen | 484, 485, 487, 488, 491, 493, 494, 495, 497, 498, 509, 541, 542 |

When a model is disabled, `_remove_model_pipelines()` in `workflow_loader.py`:
1. Removes all exclusive nodes for that model
2. Rewires node 534 (ImpactMakeImageBatch) to only reference remaining active grid outputs

### ComfyUI Environment
- User: `flipp@asteria1`
- Path: `~/ComfyUI`
- Conda env: `radial`
- GPU: NVIDIA RTX PRO 6000 Blackwell (98GB VRAM)
- Models on: `/mnt/t/models/`
- A full generation run (4 models, 9 prompts) takes ~356 seconds

### Known Issues / Open Items
- **Reference image not displaying**: Debug logging added to `app.py` status endpoint to trace `prompt_data` extraction from ComfyUI history. The reference image is extracted from the workflow prompt stored in history (`history[prompt_id]["prompt"][1]["143"]["inputs"]["image"]`). If history structure differs, this won't find it. Check backend logs for `prompt_data type=` and `Reference image:` lines.
- **Node 544 shared dependency**: Node 544 (Int, "Batch Size") feeds into: StringListCowboy limit (node 430), combined grid images_per_row (node 412). Previously also fed FLUX grid images_per_row (node 537, now hardcoded to 3) and WAN video length (node 469, now hardcoded to 1).
- ComfyUI tries to import `custom_nodes/.claude` as a node (harmless error, can delete that folder)
- FLUX LoRA keys show "not loaded" warnings — normal, architecture mismatch on shared LoRA weights

## Completed Work Log

### Session 1: Core Implementation
- Built FastAPI backend with 5 endpoints
- Built SvelteKit 5 frontend with basic white-on-gray styling
- Implemented ComfyUI workflow injection (trigger word, LoRAs, seeds, batch size)
- Implemented polling loop and image proxy
- Implemented PDF export with jsPDF

### Session 2: UI Overhaul + Features
1. **Industrial metal UI** — Ported dark control panel aesthetic from old React project to SvelteKit 5 + Tailwind v4. All 8 polish tasks completed.
2. **Editable prompts** — Added `GET /api/prompts` endpoint. PromptPanel with slider (0-9). Backend reorders enabled-first and sets StringListCowboy limit.
3. **Image proxy fix** — Backend returns full image objects. Frontend `imageUrl()` builds proper URLs with query params.
4. **PDF export fix** — Added `pointer-events: none` to `.metal-shimmer::after`.
5. **Model toggle switches** — LED toggles to enable/disable model pipelines. Backend strips nodes and rewires combined grid.

### Session 3: Code Review + Security/Reliability Hardening
- CORS restricted to `http://localhost:5173`
- All `requests` calls use `timeout=30`
- Typed exception handling: `Timeout` → 504, `ConnectionError` → 503, `RequestException` → 502
- Structured logging via Python `logging` module
- Image proxy: `type` param validated against whitelist, content-type forced to image types
- `prompt_limit` validated via Pydantic `Field(ge=1, le=9)`
- Added `GET /health` endpoint
- Polling rewritten with exponential backoff (2s → 30s max)
- Added Cancel button during generation

### Session 4: Bug Fixes + LoRA Display
- All LoRAs shown in every dropdown (architecture-matched listed first)
- Fixed disabled button state for model toggles
- Added tooltips showing image counts per model
- Fixed output node IDs in config.py (were pointing to grid compositors instead of PreviewImage/SaveImage nodes)
- Added lightbox image viewer to ResultGrid

### Session 5: Grid/PDF/Reference Image Fixes
1. **PDF export rework** — Multi-page: page 1 has reference image + title + combined grid, per-model pages with one grid image each
2. **Grid display fix** — Changed from showing all batch images to showing only the first (composed grid) image per section
3. **FLUX grid images_per_row** — Was linked to node 544 (prompt count), making all images in one wide row. Changed to hardcoded `3` in workflow_api.json
4. **WAN duplicate images** — Node 469 (EmptyHunyuanLatentVideo) `length` was linked to node 544, generating N video frames. Changed to hardcoded `1` in workflow_api.json
5. **Reference image** — Added to config.py (node 143), status API extracts filename from history prompt data, displayed as thumbnail in ResultGrid header and on PDF page 1
6. **Svelte `{@const}` fix** — Moved `{@const}` from direct child of `<div>` into `{#if}` block (Svelte requirement)
7. **ImageTextGrid node fix** — User updated the custom node behavior in ComfyUI so it outputs a single composed grid image instead of individual images
