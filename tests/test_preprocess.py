# tests/test_preprocess.py
"""Tests for the bracket-shorthand preprocessor (file/directory transforms
and the Ren'Py init-time entry point)."""

import sys
import types

import pytest

from wod_core import preprocess

BRACKET_SRC = '''menu:
    "Cast spell" [Forces >= 3]:
        jump cast
    "Run away":
        jump flee
'''

PLAIN_SRC = '''menu:
    "Cast spell" if pc.gate("Forces", ">=", 3):
        jump cast
'''


class TestProcessFile:
    """Single-file, in-place transformation."""

    def test_transforms_brackets(self, tmp_path):
        src = tmp_path / "script.rpy"
        src.write_text(BRACKET_SRC)

        changed = preprocess.process_file(str(src))

        assert changed is True
        assert 'wod_core.gate("Forces", ">=", 3)' in src.read_text()
        assert "[Forces >= 3]" not in src.read_text()

    def test_idempotent(self, tmp_path):
        src = tmp_path / "script.rpy"
        src.write_text(BRACKET_SRC)

        assert preprocess.process_file(str(src)) is True
        after_first = src.read_text()
        # Second pass has no shorthand left to transform.
        assert preprocess.process_file(str(src)) is False
        assert src.read_text() == after_first

    def test_no_brackets_unchanged(self, tmp_path):
        src = tmp_path / "script.rpy"
        src.write_text(PLAIN_SRC)

        assert preprocess.process_file(str(src)) is False
        assert src.read_text() == PLAIN_SRC

    def test_dry_run_does_not_write(self, tmp_path):
        src = tmp_path / "script.rpy"
        src.write_text(BRACKET_SRC)

        changed = preprocess.process_file(str(src), dry_run=True)

        assert changed is True  # reports that it *would* change
        assert src.read_text() == BRACKET_SRC  # but disk is untouched


class TestIterRpyFiles:
    """Recursive .rpy discovery with exclusions."""

    def test_walks_recursively(self, tmp_path):
        (tmp_path / "a.rpy").write_text("")
        sub = tmp_path / "chapters"
        sub.mkdir()
        (sub / "b.rpy").write_text("")

        found = {p.replace(str(tmp_path), "") for p in preprocess.iter_rpy_files(str(tmp_path))}

        assert any(p.endswith("a.rpy") for p in found)
        assert any(p.endswith("b.rpy") for p in found)

    def test_skips_non_rpy(self, tmp_path):
        (tmp_path / "keep.rpy").write_text("")
        (tmp_path / "skip.py").write_text("")
        (tmp_path / "skip.txt").write_text("")

        found = list(preprocess.iter_rpy_files(str(tmp_path)))

        assert len(found) == 1
        assert found[0].endswith("keep.rpy")

    def test_skips_own_shim(self, tmp_path):
        (tmp_path / preprocess.PREPROCESSOR_FILENAME).write_text("")
        (tmp_path / "script.rpy").write_text("")

        found = [p for p in preprocess.iter_rpy_files(str(tmp_path))]

        assert all(not p.endswith(preprocess.PREPROCESSOR_FILENAME) for p in found)
        assert any(p.endswith("script.rpy") for p in found)

    def test_skips_excluded_dirs(self, tmp_path):
        (tmp_path / "script.rpy").write_text("")
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "stale.rpy").write_text("")

        found = list(preprocess.iter_rpy_files(str(tmp_path)))

        assert len(found) == 1
        assert found[0].endswith("script.rpy")


class TestPreprocessDirectory:
    """Whole-tree transformation."""

    def test_transforms_nested_files(self, tmp_path):
        (tmp_path / "a.rpy").write_text(BRACKET_SRC)
        sub = tmp_path / "chapters"
        sub.mkdir()
        (sub / "b.rpy").write_text(BRACKET_SRC)
        (tmp_path / "plain.rpy").write_text(PLAIN_SRC)

        changed = preprocess.preprocess_directory(str(tmp_path))

        assert len(changed) == 2  # a.rpy and chapters/b.rpy, not plain.rpy
        assert 'wod_core.gate("Forces", ">=", 3)' in (tmp_path / "a.rpy").read_text()
        assert 'wod_core.gate("Forces", ">=", 3)' in (sub / "b.rpy").read_text()

    def test_dry_run_reports_without_writing(self, tmp_path):
        src = tmp_path / "a.rpy"
        src.write_text(BRACKET_SRC)

        changed = preprocess.preprocess_directory(str(tmp_path), dry_run=True)

        assert [p for p in changed if p.endswith("a.rpy")]
        assert src.read_text() == BRACKET_SRC  # untouched

    def test_idempotent_second_pass_is_noop(self, tmp_path):
        (tmp_path / "a.rpy").write_text(BRACKET_SRC)

        assert preprocess.preprocess_directory(str(tmp_path))  # first pass changes
        assert preprocess.preprocess_directory(str(tmp_path)) == []  # second is no-op


class TestRunInitPreprocess:
    """The Ren'Py init-time entry point (with a stubbed `renpy` module)."""

    def _install_fake_renpy(self, monkeypatch, tmp_path, developer=True):
        fake = types.ModuleType("renpy")
        fake.config = types.SimpleNamespace(developer=developer, gamedir=str(tmp_path))
        monkeypatch.setitem(sys.modules, "renpy", fake)
        return fake

    def test_transforms_in_developer_mode(self, monkeypatch, tmp_path):
        self._install_fake_renpy(monkeypatch, tmp_path, developer=True)
        (tmp_path / "script.rpy").write_text(BRACKET_SRC)

        changed = preprocess.run_init_preprocess(verbose=False)

        assert len(changed) == 1
        assert 'wod_core.gate("Forces", ">=", 3)' in (tmp_path / "script.rpy").read_text()

    def test_skips_outside_developer_mode(self, monkeypatch, tmp_path):
        self._install_fake_renpy(monkeypatch, tmp_path, developer=False)
        (tmp_path / "script.rpy").write_text(BRACKET_SRC)

        changed = preprocess.run_init_preprocess(verbose=False)

        assert changed == []
        assert (tmp_path / "script.rpy").read_text() == BRACKET_SRC  # untouched

    def test_respects_disable_flag(self, monkeypatch, tmp_path):
        import wod_core

        self._install_fake_renpy(monkeypatch, tmp_path, developer=True)
        monkeypatch.setattr(wod_core.config, "auto_preprocess", False)
        (tmp_path / "script.rpy").write_text(BRACKET_SRC)

        changed = preprocess.run_init_preprocess(verbose=False)

        assert changed == []
        assert (tmp_path / "script.rpy").read_text() == BRACKET_SRC  # untouched

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", " OFF "])
    def test_env_var_disables_regardless_of_flag(self, monkeypatch, tmp_path, value):
        # The env var opt-out must work even with the config flag at its default
        # True — that's the whole point: it doesn't depend on load order.
        self._install_fake_renpy(monkeypatch, tmp_path, developer=True)
        monkeypatch.setenv(preprocess.ENV_OPT_OUT, value)
        (tmp_path / "script.rpy").write_text(BRACKET_SRC)

        changed = preprocess.run_init_preprocess(verbose=False)

        assert changed == []
        assert (tmp_path / "script.rpy").read_text() == BRACKET_SRC  # untouched

    @pytest.mark.parametrize("value", ["1", "true", "yes", ""])
    def test_env_var_non_falsey_does_not_disable(self, monkeypatch, tmp_path, value):
        self._install_fake_renpy(monkeypatch, tmp_path, developer=True)
        monkeypatch.setenv(preprocess.ENV_OPT_OUT, value)
        (tmp_path / "script.rpy").write_text(BRACKET_SRC)

        changed = preprocess.run_init_preprocess(verbose=False)

        assert len(changed) == 1
        assert 'wod_core.gate("Forces", ">=", 3)' in (tmp_path / "script.rpy").read_text()

    def test_does_not_raise_on_bad_file(self, monkeypatch, tmp_path):
        # Runs in python early on every launch / `renpy lint`, so a non-UTF-8
        # .rpy must degrade to a no-op rather than crash the load.
        self._install_fake_renpy(monkeypatch, tmp_path, developer=True)
        (tmp_path / "bad.rpy").write_bytes(b"\xff\xfe menu: not utf-8")

        changed = preprocess.run_init_preprocess(verbose=False)

        assert changed == []  # swallowed, no exception raised
