# CLAUDE.md — Project Context for AI Assistants

## Project
LoRA Validation Tool — internal tool for Trent Films to validate trained LoRA models across multiple image generation architectures (FLUX, Z-Image, Qwen, WAN).

## Tech Stack
- **Frontend**: SvelteKit 5 (runes: `$props()`, `$state()`, `$derived()`, `$bindable()`) + Tailwind CSS v4 (`@theme` directive)
- **Backend**: Python FastAPI + requests + python-multipart (for file uploads)
- **PDF**: jsPDF (client-side, single-page landscape A4)
- **ComfyUI**: WSL2 on localhost:8188, workflow injected via REST API

## Key Conventions
- Svelte 5 runes syntax only — no `export let`, use `$props()` / `$state()` / `$derived()`
- `{@const}` can ONLY appear inside `{#if}`, `{#each}`, or `{#snippet}` blocks — never as direct child of elements
- Tailwind v4 — custom colors defined in `@theme` block in app.css, NOT in tailwind.config.js
- Backend uses Python `logging` module, structured error handling with typed exceptions
- All ComfyUI requests use `timeout=30`
- Image proxy validates `type` param against whitelist (output/input/temp)

## Important Files
- `backend/config.py` — All workflow node IDs. If workflow_api.json is re-exported, ALL node IDs may change
- `backend/workflow_api.json` — The ComfyUI workflow (node 143 = LoadImage for reference)
- `backend/app.py` — FastAPI app with `/api/upload-image` endpoint for reference images
- `frontend/src/lib/api.js` — `imageUrl()` builds URLs, `uploadImage()` for reference upload
- `frontend/src/lib/pdf.js` — Single-page PDF with 2x2 grid layout (reference image + 4 model grids)

## Running
1. ComfyUI (WSL): `cd ~/ComfyUI && python main.py --listen 0.0.0.0 --port 8188`
2. Backend: `cd backend && python -m uvicorn app:app --reload --port 8000`
3. Frontend: `cd frontend && npm run dev` (proxies /api/* to :8000)
