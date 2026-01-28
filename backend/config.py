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
    # WARNING: These IDs are tied to the specific workflow_api.json export.
    # If the workflow is re-exported from ComfyUI, all node IDs may change.
    # Verify IDs match by checking workflow_api.json after any workflow update.
    "nodes": {
        # LoRA inputs
        "flux_lora": "447",
        "zimage_lora": "480",
        "qwen_lora": "509",
        "wan_lora": "467",

        # Reference image (LoadImage node)
        "reference_image": "143",

        # Trigger word
        "trigger_word": "146",

        # Seeds (for reproducibility)
        "flux_seed": "445",
        "wan_seed": "472",
        "zimage_seed": "476",
        "qwen_seed": "488",

        # Prompt limit (controls StringListCowboy count, not image batch size)
        "prompt_limit": "544",

        # Prompt list node (StringListCowboy)
        "prompt_list": "430",

        # Individual prompt nodes (order matches value_1..value_9 in node 430)
        "prompt_nodes": ["151", "150", "229", "232", "233", "234", "230", "231", "235"],

        # Model pipeline nodes (for removal when disabled)
        "model_nodes": {
            "flux":   ["409", "441", "442", "443", "444", "445", "446", "447", "448", "449", "450", "537", "540", "550"],
            "wan":    ["463", "464", "465", "466", "467", "468", "469", "470", "472", "473", "536", "538", "397", "552"],
            "zimage": ["474", "475", "476", "477", "478", "479", "480", "481", "482", "483", "539", "137", "551"],
            "qwen":   ["484", "485", "487", "488", "491", "493", "494", "495", "497", "498", "509", "541", "542", "553"],
        },

        # ImageTextGrid nodes (compose individual images into a grid)
        "grid_nodes": ["537", "538", "539", "541"],

        # Output nodes (PreviewImage that ComfyUI reports in /history)
        "output_flux_grid": "540",
        "output_wan_grid": "397",
        "output_zimage_grid": "137",
        "output_qwen_grid": "542",
    },
}
