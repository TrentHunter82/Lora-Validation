import json
import re
import random
import logging
from pathlib import Path

import requests

from config import CONFIG

logger = logging.getLogger(__name__)

WORKFLOW_PATH = Path(__file__).parent / "workflow_api.json"

# Match architecture suffix before .safetensors (e.g. "QueenCorgiFlux.safetensors")
_ARCH_PATTERNS = {
    "flux":   re.compile(r'(?<![a-z])flux', re.IGNORECASE),
    "zimage": re.compile(r'(?<![a-z])z[-_]?image', re.IGNORECASE),
    "qwen":   re.compile(r'(?<![a-z])qwen', re.IGNORECASE),
    "wan":    re.compile(r'(?<![a-z])wan', re.IGNORECASE),
}


def get_default_prompts() -> list[dict]:
    """Read the 9 default prompts from the workflow JSON."""
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        workflow = json.load(f)

    nodes = CONFIG["nodes"]
    prompts = []
    for node_id in nodes["prompt_nodes"]:
        node = workflow.get(node_id, {})
        text = node.get("inputs", {}).get("value", "")
        title = node.get("_meta", {}).get("title", "Prompt")
        prompts.append({"text": text.strip(), "title": title, "enabled": True})
    return prompts


def load_workflow(
    trigger_word: str,
    loras: dict,
    seed: int = None,
    prompt_limit: int = None,
    prompts: list[dict] = None,
    models_enabled: dict = None,
    reference_image: str = None,
):
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        workflow = json.load(f)

    nodes = CONFIG["nodes"]

    # Set trigger word
    workflow[nodes["trigger_word"]]["inputs"]["a"] = trigger_word

    # Set reference image if provided
    if reference_image:
        workflow[nodes["reference_image"]]["inputs"]["image"] = reference_image

    # Set LoRAs
    lora_map = {
        "flux": nodes["flux_lora"],
        "zimage": nodes["zimage_lora"],
        "qwen": nodes["qwen_lora"],
        "wan": nodes["wan_lora"],
    }
    for arch, node_id in lora_map.items():
        if loras.get(arch):
            workflow[node_id]["inputs"]["lora_name"] = loras[arch]

    # Set seed (same across all models for fair comparison)
    seed = seed or random.randint(0, 2**32)
    for seed_key in ["flux_seed", "wan_seed", "zimage_seed", "qwen_seed"]:
        node_id = nodes.get(seed_key)
        if node_id and node_id in workflow:
            workflow[node_id]["inputs"]["seed"] = seed

    # Inject custom prompts and set limit to active count
    if prompts:
        prompt_node_ids = nodes["prompt_nodes"]

        # Reorder: enabled prompts first, disabled last
        enabled = [p for p in prompts if p.get("enabled", True)]
        disabled = [p for p in prompts if not p.get("enabled", True)]
        ordered = enabled + disabled

        for i, node_id in enumerate(prompt_node_ids):
            if i < len(ordered):
                workflow[node_id]["inputs"]["value"] = ordered[i]["text"]

        active_count = len(enabled)

        # Set limit on StringListCowboy to only use active prompts
        workflow[nodes["prompt_limit"]]["inputs"]["Number"] = str(active_count)
    elif prompt_limit:
        workflow[nodes["prompt_limit"]]["inputs"]["Number"] = str(prompt_limit)

    # Remove disabled model pipelines
    if models_enabled:
        disabled_models = [m for m, on in models_enabled.items() if not on]
        if disabled_models:
            _remove_model_pipelines(workflow, nodes, disabled_models)

    return workflow


def _remove_model_pipelines(workflow: dict, nodes: dict, disabled_models: list[str]):
    """Remove all nodes for disabled models."""
    model_nodes = nodes["model_nodes"]

    for model in disabled_models:
        for node_id in model_nodes.get(model, []):
            workflow.pop(node_id, None)


def list_loras() -> dict:
    """List LoRAs grouped by architecture by querying ComfyUI's API."""
    result = {"flux": [], "zimage": [], "qwen": [], "wan": []}

    try:
        r = requests.get(
            f"{CONFIG['comfyui_url']}/object_info/LoraLoader",
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        all_loras = sorted(data["LoraLoader"]["input"]["required"]["lora_name"][0])
    except requests.RequestException as e:
        logger.warning("Failed to fetch LoRAs from ComfyUI: %s", e)
        return result
    except (KeyError, IndexError) as e:
        logger.error("Unexpected ComfyUI API response format: %s", e)
        return result

    # Every dropdown gets all LoRAs — architecture-matched ones are listed first
    for arch, pattern in _ARCH_PATTERNS.items():
        matched = [n for n in all_loras if pattern.search(n)]
        unmatched = [n for n in all_loras if not pattern.search(n)]
        result[arch] = matched + unmatched

    return result
