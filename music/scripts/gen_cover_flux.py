#!/usr/bin/env python3
"""Render the "Erasing the Distance" cover art via ComfyUI FLUX.1-schnell.

Square 1024x1024, 4-step schnell. Prompt written per the FLUX prompting skill
(natural prose, no tag soup, no negative prompt). Typography (title + Reverb256)
is composited afterward with Pillow, NOT by FLUX — text rendering in FLUX is
unreliable, so the art stays clean and the words are added crisply.
"""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:32188"  # k8s comfyui-zephyr NodePort (the render target)

ART_PROMPT = (
    "Album cover art, square composition: two translucent humanoid figures made "
    "of glowing white wireframe and drifting particles, facing each other and "
    "reaching toward one another across a dark empty void, fingertips almost "
    "touching, a faint bridge of light forming between them. Deep black "
    "background with a subtle cool blue-to-violet gradient. Ethereal, intimate, "
    "cinematic, high contrast, minimalist electronic music aesthetic. Centered "
    "subject with generous negative space around it, no text, no words, no "
    "letters, no watermark."
)

graph = {
    # GGUF UNET (Apache-2.0 FLUX.1-schnell, 6.4 GB) — fits the 16 GiB cgroup
    # that the 17 GB fp8 UNET OOMKilled. Loaded via the ComfyUI-GGUF node's
    # UnetLoaderGGUF, not the stock UNETLoader.
    "1": {"class_type": "UnetLoaderGGUF",
          "inputs": {"unet_name": "flux1-schnell-Q4_K_S.gguf"}},
    "2": {"class_type": "CLIPLoader",
          "inputs": {"clip_name": "t5xxl_fp8_e4m3fn_scaled.safetensors", "type": "sd3"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": ART_PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "EmptySD3LatentImage",
          "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "6": {"class_type": "KSampler", "inputs": {
        "seed": int(time.time()) % (2**53), "steps": 4, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["4", 0],
        "latent_image": ["5", 0]}},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
    "8": {"class_type": "SaveImage",
          "inputs": {"images": ["7", 0], "filename_prefix": "erasing_cover"}},
}


def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read())


print("submitting workflow...")
res = post("/prompt", {"prompt": graph, "client_id": "cover-gen"})
pid = res["prompt_id"]
print("prompt_id:", pid)

# poll history until done
for _ in range(120):
    time.sleep(5)
    hist = get(f"/history/{pid}")
    if pid in hist and hist[pid].get("status", {}).get("completed"):
        outs = hist[pid]["outputs"]
        imgs = outs.get("8", {}).get("images", [])
        print("DONE. images:", json.dumps(imgs))
        break
else:
    print("TIMEOUT waiting for completion; check /history")
