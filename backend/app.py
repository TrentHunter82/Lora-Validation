import os
import re
import logging

from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import requests

from config import CONFIG
from workflow_loader import load_workflow, list_loras, get_default_prompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30  # seconds

app = FastAPI(title="LoRA Validation API")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
SAFE_IMAGE_SUBTYPES = {"output", "input", "temp"}


class GenerateRequest(BaseModel):
    trigger_word: str = Field(..., max_length=200)
    loras: dict[str, str]
    seed: Optional[int] = None
    prompt_limit: Optional[int] = Field(None, ge=1, le=9)
    prompts: Optional[list[dict]] = None  # [{text, enabled}, ...]
    models_enabled: Optional[dict[str, bool]] = None  # {flux, zimage, qwen, wan}
    reference_image: Optional[str] = None  # Filename from /api/upload-image


@app.get("/health")
def health_check():
    try:
        r = requests.get(
            f"{CONFIG['comfyui_url']}/system_stats", timeout=5
        )
        r.raise_for_status()
        return {"status": "healthy", "comfyui": "connected"}
    except Exception:
        return {"status": "unhealthy", "comfyui": "disconnected"}


@app.get("/api/config")
def get_config():
    return {
        "comfyui_url": CONFIG["comfyui_url"],
        "available_prompts": 9,
        "default_prompt_limit": 9,
    }


@app.get("/api/prompts")
def get_prompts():
    return get_default_prompts()


@app.get("/api/loras")
def get_loras():
    return list_loras()


@app.post("/api/upload-image")
async def upload_image(file: UploadFile):
    """Upload an image to ComfyUI's input folder."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        content = await file.read()
        files = {"image": (file.filename, content, file.content_type)}
        r = requests.post(
            f"{CONFIG['comfyui_url']}/upload/image",
            files=files,
            data={"type": "input"},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()  # {"name": "filename.png", "subfolder": "", "type": "input"}
    except requests.RequestException as e:
        logger.error("ComfyUI error on /upload/image: %s", type(e).__name__)
        raise HTTPException(status_code=502, detail="ComfyUI upload failed")


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        workflow = load_workflow(
            trigger_word=req.trigger_word,
            loras=req.loras,
            seed=req.seed,
            prompt_limit=req.prompt_limit,
            prompts=req.prompts,
            models_enabled=req.models_enabled,
            reference_image=req.reference_image,
        )

        r = requests.post(
            f"{CONFIG['comfyui_url']}/prompt",
            json={"prompt": workflow},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()

        return {"prompt_id": r.json()["prompt_id"], "status": "queued"}
    except requests.Timeout:
        logger.error("ComfyUI timeout on /prompt")
        raise HTTPException(status_code=504, detail="ComfyUI request timed out")
    except requests.ConnectionError:
        logger.error("ComfyUI connection failed on /prompt")
        raise HTTPException(status_code=503, detail="ComfyUI unavailable")
    except requests.RequestException as e:
        logger.error("ComfyUI error on /prompt: %s", type(e).__name__)
        raise HTTPException(status_code=502, detail="ComfyUI request failed")


# Map model pipeline node IDs to model names for progress tracking
MODEL_OUTPUT_NODES = {
    "flux_grid": CONFIG["nodes"]["output_flux_grid"],
    "zimage_grid": CONFIG["nodes"]["output_zimage_grid"],
    "qwen_grid": CONFIG["nodes"]["output_qwen_grid"],
    "wan_grid": CONFIG["nodes"]["output_wan_grid"],
}

# Map node IDs to model names for queue progress
MODEL_NODE_MAPPING = {}
for model_name, node_ids in CONFIG["nodes"].get("model_nodes", {}).items():
    for node_id in node_ids:
        MODEL_NODE_MAPPING[node_id] = model_name


def _get_queue_progress(prompt_id: str) -> dict:
    """Check ComfyUI queue to determine current execution progress."""
    try:
        r = requests.get(f"{CONFIG['comfyui_url']}/queue", timeout=5)
        r.raise_for_status()
        queue_data = r.json()
    except requests.RequestException:
        return {"completed": [], "current_model": None, "percent": 0}

    # Check if prompt is in pending queue
    pending = queue_data.get("queue_pending", [])
    for item in pending:
        if len(item) > 1 and item[1] == prompt_id:
            return {"completed": [], "current_model": None, "percent": 0, "status": "queued"}

    # Check if prompt is currently running
    running = queue_data.get("queue_running", [])
    for item in running:
        if len(item) > 1 and item[1] == prompt_id:
            # Try to get current node from execution info
            current_model = None
            if len(item) > 3 and isinstance(item[3], dict):
                current_nodes = item[3].get("nodes", [])
                for node_id in current_nodes:
                    if node_id in MODEL_NODE_MAPPING:
                        current_model = MODEL_NODE_MAPPING[node_id]
                        break
            return {"completed": [], "current_model": current_model, "percent": 10, "status": "generating"}

    # Not in queue - might be finishing up
    return {"completed": [], "current_model": None, "percent": 5, "status": "processing"}


@app.get("/api/status/{prompt_id}")
def get_status(prompt_id: str):
    try:
        r = requests.get(
            f"{CONFIG['comfyui_url']}/history/{prompt_id}",
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
    except requests.Timeout:
        logger.error("ComfyUI timeout on /history")
        raise HTTPException(status_code=504, detail="ComfyUI request timed out")
    except requests.ConnectionError:
        logger.error("ComfyUI connection failed on /history")
        raise HTTPException(status_code=503, detail="ComfyUI unavailable")
    except requests.RequestException as e:
        logger.error("ComfyUI error on /history: %s", type(e).__name__)
        raise HTTPException(status_code=502, detail="ComfyUI request failed")

    history = r.json()

    if prompt_id not in history:
        # Job still running - check queue for progress info
        progress = _get_queue_progress(prompt_id)
        return {"done": False, "status": "running", "progress": progress}

    outputs = history[prompt_id].get("outputs", {})
    nodes = CONFIG["nodes"]

    # Track which model grids are complete
    completed_models = []
    for model_name, node_id in MODEL_OUTPUT_NODES.items():
        if node_id in outputs and "images" in outputs[node_id]:
            completed_models.append(model_name)

    result = {
        "done": True,
        "status": "complete",
        "outputs": {},
        "progress": {
            "completed": completed_models,
            "current_model": None,
            "percent": 100,
        },
    }

    # Include reference image from the workflow's LoadImage node
    prompt_data = history[prompt_id].get("prompt", [None, None])
    if isinstance(prompt_data, list) and len(prompt_data) > 1 and isinstance(prompt_data[1], dict):
        ref_node_id = nodes.get("reference_image", "")
        ref_node = prompt_data[1].get(ref_node_id, {})
        ref_filename = ref_node.get("inputs", {}).get("image", "")
        logger.debug("Reference image: node_id=%s, filename='%s'", ref_node_id, ref_filename)
        if ref_filename:
            result["outputs"]["reference_image"] = {
                "filename": ref_filename,
                "subfolder": "",
                "type": "input",
            }
    else:
        logger.warning("Could not extract prompt data from history for reference image")

    output_map = {
        nodes["output_flux_grid"]: "flux_grid",
        nodes["output_wan_grid"]: "wan_grid",
        nodes["output_zimage_grid"]: "zimage_grid",
        nodes["output_qwen_grid"]: "qwen_grid",
    }

    for node_id, key in output_map.items():
        if node_id in outputs and "images" in outputs[node_id]:
            images = outputs[node_id]["images"]
            logger.debug("Node %s (%s): %d images", node_id, key, len(images))
            # Return all images for this output
            result["outputs"][key] = [
                {
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                }
                for img in images
            ]

    return result


_SAFE_FILENAME = re.compile(r'^[a-zA-Z0-9_\-][a-zA-Z0-9_\-. ]*$')


@app.get("/api/image/{filename}")
def get_image(filename: str, subfolder: str = "", type: str = "output"):
    if not _SAFE_FILENAME.match(filename) or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if subfolder and (not _SAFE_FILENAME.match(subfolder) or ".." in subfolder):
        raise HTTPException(status_code=400, detail="Invalid subfolder")
    if type not in SAFE_IMAGE_SUBTYPES:
        raise HTTPException(status_code=400, detail="Invalid type parameter")

    params = {"filename": filename, "subfolder": subfolder, "type": type}
    try:
        r = requests.get(
            f"{CONFIG['comfyui_url']}/view",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        logger.error("ComfyUI error on /view: %s", e.__class__.__name__)
        raise HTTPException(status_code=502, detail="ComfyUI request failed")

    content_type = r.headers.get("content-type", "image/png")
    if content_type not in ALLOWED_IMAGE_TYPES:
        content_type = "image/png"
    return Response(content=r.content, media_type=content_type)
