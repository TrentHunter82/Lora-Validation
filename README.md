# LoRA Validation Tool

Internal tool for **Trent Films** to validate trained LoRA models across multiple image generation architectures.

## Overview

This tool generates comparison grids for LoRA models across four different architectures:
- **FLUX**
- **Z-Image**
- **Qwen**
- **WAN**

Upload a reference image, configure your LoRA, and generate a single-page PDF report with side-by-side comparisons.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SvelteKit 5   │────▶│   FastAPI       │────▶│   ComfyUI       │
│   Frontend      │     │   Backend       │     │   (WSL2)        │
│   :5173         │     │   :8000         │     │   :8188         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Frontend**: SvelteKit 5 with Tailwind CSS v4
- **Backend**: Python FastAPI proxy to ComfyUI
- **Workflow**: ComfyUI workflow with multi-model validation pipeline

## Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.10+
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) running in WSL2

## Quick Start

### 1. Start ComfyUI (WSL2)

```bash
cd ~/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Configuration

Copy `.env.example` to `.env` in the backend folder:

```bash
cp .env.example backend/.env
```

Environment variables:
- `COMFYUI_URL` - ComfyUI server URL (default: `http://localhost:8188`)
- `LORA_PATH` - Path to LoRA models in ComfyUI
- `ALLOWED_ORIGINS` - CORS origins (default: `http://localhost:5173`)

## Features

- **Progress Tracking** - Real-time progress bar showing which model is currently generating
- **Model Status** - Visual indicators (✓ complete, ⏳ active, ○ pending) for each architecture
- **PDF Export** - Portrait A4 report with all 4 models stacked vertically
- **Reference Image** - Upload and preview reference images (320px preview)

## Usage

1. **Select LoRA** - Choose your trained LoRA model for each architecture
2. **Set Trigger Word** - Enter the activation trigger word
3. **Upload Reference** - Upload a reference image for comparison
4. **Configure Prompts** - Enable/disable test prompts (up to 9)
5. **Select Models** - Toggle which architectures to test
6. **Generate** - Run validation with live progress tracking
7. **Export PDF** - Download portrait report with all model comparisons

## Project Structure

```
├── backend/
│   ├── app.py              # FastAPI application
│   ├── config.py           # Node IDs and configuration
│   ├── workflow_api.json   # ComfyUI workflow
│   ├── workflow_loader.py  # Workflow manipulation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.js      # API client
│   │   │   ├── pdf.js      # PDF export
│   │   │   └── components/ # Svelte components
│   │   └── routes/
│   │       └── +page.svelte
│   └── package.json
├── .env.example
├── CLAUDE.md               # AI assistant context
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/loras` | GET | List available LoRA models by architecture |
| `/api/prompts` | GET | Get default test prompts |
| `/api/upload-image` | POST | Upload reference image to ComfyUI |
| `/api/generate` | POST | Start validation workflow |
| `/api/status/{id}` | GET | Check status with progress data |
| `/api/image/{filename}` | GET | Proxy images from ComfyUI |
| `/health` | GET | Health check |

### Status Response

```json
{
  "done": false,
  "status": "running",
  "progress": {
    "completed": ["flux_grid", "zimage_grid"],
    "current_model": "qwen",
    "percent": 50
  }
}
```

## Tech Stack

- **Frontend**: SvelteKit 5, Tailwind CSS v4, jsPDF
- **Backend**: FastAPI, Pydantic, requests
- **Workflow**: ComfyUI with custom nodes

## Development Notes

- Svelte 5 uses runes syntax (`$state()`, `$props()`, `$derived()`)
- Tailwind v4 uses `@theme` directive in `app.css`
- Node IDs in `config.py` must match `workflow_api.json`
- All ComfyUI requests use 30-second timeout

## License

Internal use only - Trent Films
