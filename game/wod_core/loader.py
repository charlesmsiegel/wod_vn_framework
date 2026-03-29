# game/wod_core/loader.py
"""YAML file loading — splat discovery, schema loading, character loading."""

from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

from wod_core.engine import Schema, Character
from wod_core.resources import ResourceManager


@dataclass
class SplatData:
    """Loaded splat — schema, resource config, manifest."""

    splat_id: str
    schema: Schema
    resource_config: dict
    manifest: dict
    templates_dir: str
    chargen_config: dict | None = None


class SplatLoader:
    """Discovers and loads splat packs from the game directory."""

    def __init__(self, game_dir: str):
        self.game_dir = game_dir
        self.splats_dir = os.path.join(game_dir, "splats")
        self.loaded_splats: dict[str, SplatData] = {}

    def discover_splats(self) -> list[str]:
        splat_ids = []
        if not os.path.isdir(self.splats_dir):
            return splat_ids
        for name in os.listdir(self.splats_dir):
            manifest_path = os.path.join(self.splats_dir, name, "manifest.yaml")
            if os.path.isfile(manifest_path):
                splat_ids.append(name)
        return splat_ids

    def load_splat(self, splat_id: str, overrides: str | None = None) -> SplatData:
        splat_dir = os.path.join(self.splats_dir, splat_id)
        manifest_path = os.path.join(splat_dir, "manifest.yaml")

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        schema_file = manifest["splat"].get("schema", "schema.yaml")
        with open(os.path.join(splat_dir, schema_file)) as f:
            schema_data = yaml.safe_load(f)

        resources_file = manifest["splat"].get("resources", "resources.yaml")
        with open(os.path.join(splat_dir, resources_file)) as f:
            resource_config = yaml.safe_load(f)

        templates_dir = os.path.join(
            splat_dir, manifest["splat"].get("templates_dir", "templates")
        )

        schema = Schema(schema_data)

        # Load chargen config if present
        chargen_config = None
        chargen_file = manifest["splat"].get("chargen")
        if chargen_file:
            with open(os.path.join(splat_dir, chargen_file)) as f:
                chargen_config = yaml.safe_load(f)

        splat = SplatData(
            splat_id=splat_id,
            schema=schema,
            resource_config=resource_config,
            manifest=manifest,
            templates_dir=templates_dir,
            chargen_config=chargen_config,
        )
        self.loaded_splats[splat_id] = splat
        return splat

    def load_character(self, char_path: str) -> Character:
        # Resolve relative paths against game_dir
        if not os.path.isabs(char_path):
            char_path = os.path.join(self.game_dir, char_path)
        with open(char_path) as f:
            char_data = yaml.safe_load(f)

        splat_id = char_data["schema"]
        if splat_id not in self.loaded_splats:
            raise ValueError(f"Splat {splat_id!r} not loaded. Call load_splat() first.")
        splat = self.loaded_splats[splat_id]

        # Flatten nested traits dict
        flat_traits: dict[str, int] = {}
        for category_traits in char_data.get("traits", {}).values():
            if isinstance(category_traits, dict):
                flat_traits.update(category_traits)

        char = Character(
            schema=splat.schema,
            traits=flat_traits,
            merits_flaws=char_data.get("merits_flaws", []),
            identity=char_data.get("identity", {}),
        )

        # Set up resources
        resource_config = dict(splat.resource_config)  # shallow copy
        char.resources = ResourceManager(resource_config)

        # Apply character-specific resource overrides
        for res_name, res_value in char_data.get("resources", {}).items():
            if char.resources.has_resource(res_name) and isinstance(res_value, int):
                pool = char.resources.pools[res_name]
                pool.current_value = res_value
                if res_value > pool.max:
                    pool.max = res_value

        return char
