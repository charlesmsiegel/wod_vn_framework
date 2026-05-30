# tests/test_template_resonance.py
"""Regression: every bundled template ships a beginning-mage Resonance dot.

The Resonance system (Dynamic / Entropic / Static) defaults every Resonance
trait to 0. In template-mode chargen the identity screen suppresses the
Resonance picker because the template file is expected to supply it, and
``_build_from_template`` only copies the dots present in the YAML. A template
that omits Resonance therefore yields a mage with no Resonance at all, which
breaks story gates and sheet display that rely on the starting dot.

This guards all current and future templates against that gap.
"""

import os

import pytest

from wod_core.chargen import ChargenState, build_character
from wod_core.loader import SplatLoader

GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "game")
RESONANCE_TRAITS = ("Dynamic", "Entropic", "Static")


def _all_tradition_templates():
    """(tradition, template) pairs for every template referenced in chargen.yaml."""
    splat = SplatLoader(GAME_DIR).load_splat("mage")
    return [
        (trad, tmpl)
        for trad in splat.chargen_config.get("traditions", [])
        for tmpl in trad.get("templates", [])
    ]


_PARAMS = _all_tradition_templates()
_IDS = [f"{trad['id']}-{os.path.basename(tmpl['file'])}" for trad, tmpl in _PARAMS]


@pytest.fixture
def mage_splat():
    return SplatLoader(GAME_DIR).load_splat("mage")


@pytest.mark.parametrize("tradition,template", _PARAMS, ids=_IDS)
def test_template_has_starting_resonance(mage_splat, tradition, template):
    """A character built from the template has at least one Resonance dot."""
    state = ChargenState(
        "mage", "template", mage_splat.schema, mage_splat.chargen_config, mage_splat,
    )
    state.save_step("identity", {"name": "Test Hero"})
    state.save_step("template_pick", {
        "tradition": tradition["id"],
        "template_file": template["file"],
    })

    char = build_character(state)

    total = sum(char.get(r) for r in RESONANCE_TRAITS)
    assert total >= 1, (
        f"{template['file']} produces a mage with no Resonance dots; "
        "beginning mages should start with one."
    )


@pytest.mark.parametrize("tradition,template", _PARAMS, ids=_IDS)
def test_template_identity_resonance_matches_dot(mage_splat, tradition, template):
    """identity.resonance names a real Resonance type that the mage has a dot in."""
    state = ChargenState(
        "mage", "template", mage_splat.schema, mage_splat.chargen_config, mage_splat,
    )
    state.save_step("identity", {"name": "Test Hero"})
    state.save_step("template_pick", {
        "tradition": tradition["id"],
        "template_file": template["file"],
    })

    char = build_character(state)

    declared = char.identity.get("resonance")
    assert declared in RESONANCE_TRAITS, (
        f"{template['file']} identity.resonance={declared!r} is not one of "
        f"{RESONANCE_TRAITS}"
    )
    assert char.get(declared) >= 1, (
        f"{template['file']} declares Resonance {declared!r} in identity but has "
        "no matching dot in traits.resonance"
    )
