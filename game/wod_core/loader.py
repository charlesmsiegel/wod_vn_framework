# game/wod_core/loader.py
"""YAML file loading — splat discovery, schema loading, character loading."""

from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

from wod_core.engine import Schema, Character, MaxLinkedConstraint
from wod_core.resources import ResourceManager


def _apply_overrides(schema_data: dict, resource_config: dict, overrides: dict) -> None:
    """Apply author-level overrides to schema and resource data."""
    # Override trait categories
    if "trait_categories" in overrides:
        for cat_name, cat_overrides in overrides["trait_categories"].items():
            if cat_name in schema_data.get("trait_categories", {}):
                cat = schema_data["trait_categories"][cat_name]
                for key, value in cat_overrides.items():
                    if isinstance(value, dict) and "append" in value:
                        # Append to existing list within a group
                        if "groups" in cat and key in cat["groups"]:
                            cat["groups"][key].extend(value["append"])
                        elif "traits" in cat:
                            cat["traits"].extend(value["append"])
                    else:
                        cat[key] = value

    # Override resources
    if "resources" in overrides:
        for res_name, res_overrides in overrides["resources"].items():
            if res_name in resource_config.get("resources", {}):
                resource_config["resources"][res_name].update(res_overrides)


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

        # Apply overrides if provided
        if overrides:
            if not os.path.isabs(overrides):
                overrides = os.path.join(self.game_dir, overrides)
            with open(overrides) as f:
                override_data = yaml.safe_load(f)
            if override_data and "overrides" in override_data:
                _apply_overrides(schema_data, resource_config, override_data["overrides"])

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

    def load_character_from_template(
        self, splat_id: str, template_path: str,
        identity_override: dict | None = None,
    ) -> Character:
        """Load a character from a template, supporting extends/overrides."""
        if splat_id not in self.loaded_splats:
            raise ValueError(f"Splat {splat_id!r} not loaded.")
        splat = self.loaded_splats[splat_id]
        splat_dir = os.path.dirname(splat.templates_dir.rstrip("/"))
        full_path = os.path.join(splat_dir, template_path)

        with open(full_path) as f:
            template_data = yaml.safe_load(f)

        # Handle extends
        if "extends" in template_data:
            base_name = template_data["extends"]
            base_path = os.path.join(splat.templates_dir, f"{base_name}.yaml")
            with open(base_path) as f:
                base_data = yaml.safe_load(f)

            # Apply overrides from the extending template
            if "overrides" in template_data:
                overrides = template_data["overrides"]
                # Create modified schema data
                schema_data_copy = self._schema_to_dict(splat.schema)
                _apply_overrides(schema_data_copy, splat.resource_config, overrides)
                schema = Schema(schema_data_copy)
            else:
                schema = splat.schema

            char_data = base_data
        else:
            schema = splat.schema
            char_data = template_data

        # Flatten traits
        flat_traits: dict[str, int] = {}
        for category_traits in char_data.get("traits", {}).values():
            if isinstance(category_traits, dict):
                flat_traits.update(category_traits)

        # Apply identity override
        identity = char_data.get("identity", {})
        if identity_override:
            identity.update(identity_override)

        char = Character(
            schema=schema,
            traits=flat_traits,
            merits_flaws=char_data.get("merits_flaws", []),
            identity=identity,
        )

        # Attach resources
        char.resources = ResourceManager(dict(splat.resource_config))
        for res_name, res_value in char_data.get("resources", {}).items():
            if char.resources.has_resource(res_name) and isinstance(res_value, int):
                pool = char.resources.pools[res_name]
                pool.current_value = res_value
                if res_value > pool.max:
                    pool.max = res_value

        return char

    @staticmethod
    def _schema_to_dict(schema: Schema) -> dict:
        """Convert a Schema back to a raw dict for override merging."""
        data: dict = {"trait_categories": {}, "trait_constraints": []}
        for cat_name, cat in schema.categories.items():
            cat_data: dict = {
                "display_name": cat.display_name,
                "range": list(cat.range),
                "default": cat.default,
            }
            if cat.groups is not None:
                cat_data["groups"] = {k: list(v) for k, v in cat.groups.items()}
            else:
                cat_data["traits"] = list(cat.trait_names)
            data["trait_categories"][cat_name] = cat_data
        for constraint in schema.constraints:
            if isinstance(constraint, MaxLinkedConstraint):
                data["trait_constraints"].append({
                    "type": "max_linked",
                    "target_category": constraint.target_category,
                    "limited_by": constraint.limited_by,
                    "rule": constraint.rule,
                })
        return data
