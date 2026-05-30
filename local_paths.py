import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
CACHE_DIR = ROOT / ".cache"
HF_HOME = CACHE_DIR / "huggingface"
HF_HUB_CACHE = HF_HOME / "hub"
HF_ASSETS_CACHE = HF_HOME / "assets"
HF_XET_CACHE = HF_HOME / "xet"
TORCH_HOME = CACHE_DIR / "torch"
PIPER_MODELS_DIR = MODELS_DIR / "piper"


def ensure_local_dirs():
    for path in [
        MODELS_DIR,
        CACHE_DIR,
        HF_HOME,
        HF_HUB_CACHE,
        HF_ASSETS_CACHE,
        HF_XET_CACHE,
        TORCH_HOME,
        PIPER_MODELS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def configure_local_model_env():
    ensure_local_dirs()
    os.environ["ULTRA_TTS_MODELS_DIR"] = str(MODELS_DIR)
    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_CACHE"] = str(HF_HUB_CACHE)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_HUB_CACHE)
    os.environ["HF_ASSETS_CACHE"] = str(HF_ASSETS_CACHE)
    os.environ["HF_XET_CACHE"] = str(HF_XET_CACHE)
    os.environ["TRANSFORMERS_CACHE"] = str(HF_HUB_CACHE)
    os.environ["TORCH_HOME"] = str(TORCH_HOME)
    os.environ["XDG_CACHE_HOME"] = str(CACHE_DIR)
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
