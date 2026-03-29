"""WoD VN Framework — Core Engine."""

__version__ = "0.1.0"

from wod_core.gating import gate, has, set_active, get_active
from wod_core.loader import SplatLoader

_loader: SplatLoader | None = None


def init(game_dir: str) -> None:
    global _loader
    _loader = SplatLoader(game_dir)


def get_loader() -> SplatLoader:
    if _loader is None:
        raise RuntimeError("wod_core not initialized. Call wod_core.init(game_dir) first.")
    return _loader


def load_splat(splat_id: str):
    return get_loader().load_splat(splat_id)


def load_all_splats():
    loader = get_loader()
    for splat_id in loader.discover_splats():
        loader.load_splat(splat_id)


def load_character(char_path: str):
    return get_loader().load_character(char_path)
