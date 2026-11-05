"""White's model advisor (White 2.0, point 7): explain and use open-weight models, from live data.

- hardware(): RAM, GPU VRAM, local runtimes (Ollama, LM Studio) on this machine;
- open_models(): live trending open-weight text models from the Hugging Face API, with size, license,
  and whether a 4-bit build fits this machine;
- routing(home): what White itself runs on now (primary + fallbacks).
Advice only: changing White's own models is a config change the founder approves. Stdlib only.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

HF = "https://huggingface.co/api/models"
REPOST = re.compile(r"(gguf|uncensored|abliterat|obliterat|-awq|-gptq|-exl2|mlx|-q\d|-int\d|bnb|-fp8|imatrix)",
                    re.IGNORECASE)
BYTES_PER_PARAM_Q4 = 0.6   # ~4.5 bits/weight plus overhead
HEADROOM_GB = 2.0
MIN_LIKES = 100

Fetcher = Callable[[str], bytes]


def _http(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "white-models/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(5 * 1024 * 1024)


def _ram_gb() -> float:
    try:
        if platform.system() == "Windows":
            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 1e9, 1)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)
    except Exception:
        return 0.0


def _vram_gb() -> float:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return 0.0
    try:
        out = subprocess.run([exe, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return round(sum(float(x) for x in out.split()) / 1024, 1)
    except Exception:
        return 0.0


def hardware() -> dict:
    ram, vram = _ram_gb(), _vram_gb()
    apple = platform.system() == "Darwin" and platform.machine() == "arm64"
    # Unified memory on Apple Silicon; otherwise GPU VRAM if present, else CPU RAM (slow but works).
    budget = ram * 0.7 if apple else (vram if vram else ram * 0.6)
    return {"os": platform.system(), "cpu_threads": os.cpu_count(), "ram_gb": ram, "vram_gb": vram,
            "apple_silicon": apple, "model_budget_gb": round(max(0.0, budget - HEADROOM_GB), 1),
            "runs_on": "gpu" if (vram or apple) else "cpu (slow)",
            "runtimes": [r for r in ("ollama", "lms", "llama-server", "vllm") if shutil.which(r)]}


def fits(params: int, budget_gb: float) -> dict:
    need = round(params * BYTES_PER_PARAM_Q4 / 1e9, 1)
    return {"q4_gb": need, "fits_here": bool(params) and need <= budget_gb}


def open_models(fetch: Fetcher = _http, budget_gb: float | None = None, limit: int = 12) -> dict:
    """Live trending open-weight text models (originals, not quantized reposts)."""
    budget = hardware()["model_budget_gb"] if budget_gb is None else budget_gb
    q = urllib.parse.urlencode([("pipeline_tag", "text-generation"), ("sort", "trendingScore"), ("limit", "60"),
                                ("expand[]", "safetensors"), ("expand[]", "likes"), ("expand[]", "downloads"),
                                ("expand[]", "cardData"), ("expand[]", "lastModified")])
    rows = []
    for m in json.loads(fetch(f"{HF}?{q}")):
        mid = str(m.get("id") or "")
        params = int(((m.get("safetensors") or {}).get("total")) or 0)
        if not params or REPOST.search(mid) or int(m.get("likes") or 0) < MIN_LIKES:
            continue  # quantized reposts and one-person fine-tunes are noise for advice
        rows.append({"id": mid, "params_b": round(params / 1e9, 1), "license": (m.get("cardData") or {}).get("license"),
                     "likes": m.get("likes"), "downloads": m.get("downloads"), "updated": m.get("lastModified"),
                     "url": f"https://huggingface.co/{mid}", **fits(params, budget)})
    rows = rows[:limit]
    return {"budget_gb": budget, "source": "Hugging Face trending (live)", "models": rows,
            "runs_here": [r["id"] for r in rows if r["fits_here"]]}


def routing(home: Path) -> dict:
    cfg = home / "config.yaml"
    if not cfg.exists():
        return {}
    t = cfg.read_text(encoding="utf-8", errors="replace")
    model = re.search(r"^model:\s*\n((?:[ \t]+.*\n)+)", t, re.M)
    prim = {}
    if model:
        for k in ("provider", "default", "model", "base_url"):
            m = re.search(rf"^\s+{k}:\s*(\S+)", model.group(1), re.M)
            if m:
                prim[k] = m.group(1)
    fb = re.search(r"^fallback_providers:\s*\n((?:[ \t]+.*\n)+)", t, re.M)
    chain = re.findall(r"model:\s*(\S+)", fb.group(1)) if fb else []
    return {"primary": prim, "fallbacks": chain,
            "note": "Changing these is a config change: propose it with numbers and ask the founder."}
