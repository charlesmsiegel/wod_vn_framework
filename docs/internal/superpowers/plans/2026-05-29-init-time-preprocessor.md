# Init-Time Bracket Preprocessor — Design Note

**Issue:** #15 — *Bracket shorthand as Ren'Py init-time pre-processor*

**Goal:** Make the bracket shorthand (`[Forces >= 3]`) work without a separate
build step, by compiling it at Ren'Py init time. Previously the transform only
ran as a CLI tool (`python -m wod_core`).

---

## The constraint that shapes the design

Ren'Py **parses every `.rpy` file into an AST before any `init python` block
runs.** A menu choice like:

```renpy
menu:
    "Cast spell" [Forces >= 3]:
```

is a *parse error* — Ren'Py's menu grammar accepts `"text" (args) if cond:`, not
`"text" [cond]:`. So by the time `init python` could run a fixer, the file
containing the shorthand has already failed to parse. **The transform must
happen before Ren'Py parses the affected files.**

This rules out the obvious "run it in `init python`" approach.

## What does work: `python early` + file rewrite

Ren'Py loads `.rpy` files in **sorted filename order**, and a `python early`
block runs **before the files that sort after it are parsed**. This is the same
ordering guarantee that makes creator-defined statements work (the Ren'Py docs
note that a CDS-defining file "must be loaded before the file containing the
statement," which is why people name such files `00*.rpy`).

Per-file the loader does *parse-then-early* and moves to the next file, so:

1. `00_wod_preprocess.rpy` (sorts first) is parsed — it has no shorthand.
2. Its `python early` block runs and **rewrites the remaining `.rpy` files on
   disk**, turning shorthand into `if` expressions.
3. Ren'Py proceeds to load `script.rpy` etc., reading the **rewritten** source
   from disk, and parses it successfully — all in the same run.

File contents are read lazily, per file, at load time (the up-front scan only
lists filenames), so rewriting a not-yet-loaded file takes effect this run. The
`.rpyc` cache is keyed on mtime, so a rewrite forces a recompile from the new
source. This matches the mechanism hinted at in the issue ("reading/rewriting
.rpy files during `python early` phase").

### Why rewriting is safe to do on every launch

The transform is **idempotent**: once a line is `if wod_core.gate(...)`, there
is no bracket shorthand left to match, so a second pass changes nothing and
writes nothing. After the first launch that compiles a file, subsequent launches
are no-ops for it.

## Implementation

| Piece | Role |
|-------|------|
| `wod_core/syntax.py` | Unchanged. Line/source-level transform (`transform_source`). |
| `wod_core/preprocess.py` | New. `process_file`, `iter_rpy_files`, `preprocess_directory` (idempotent, in-place), and `run_init_preprocess()` — the Ren'Py-gated entry point. Pure Python, fully unit-tested. |
| `00_wod_preprocess.rpy` | New. A thin `python early` shim that calls `run_init_preprocess()`; guarded so an import failure degrades gracefully to "use the CLI." |
| `wod_core/__main__.py` | Refactored to share `preprocess` and to accept directories. |
| `wod_core/__init__.py` | `config.auto_preprocess` flag (default `True`). |

`run_init_preprocess()` is a no-op when any of these hold:

- `renpy.config.developer` is false. Distributed builds ship precompiled `.rpyc`,
  have no shorthand to compile, and may sit on a read-only tree.
- `WOD_AUTO_PREPROCESS` is set to a falsey value. This is the **ordering-independent
  opt-out**: it's an environment variable, read before any script runs, so it
  always takes effect — and it's the right switch for CI / `renpy lint` / CLI-only
  workflows.
- `wod_core.config.auto_preprocess` is disabled. **Caveat:** because the pass runs
  in `python early`, this flag only takes effect when set that early (a `python
  early` block in a file sorting before `00_wod_preprocess.rpy`); setting it in
  `init python` is too late, since `init` runs after `early`. The env var exists
  precisely so authors don't have to reason about that ordering.

`renpy` is imported *inside* the function so the module stays importable (and
testable) outside Ren'Py; tests stub a fake `renpy` module to exercise the gates.

## Known limitations (documented for authors)

- **In-place edits.** Like the CLI, it replaces shorthand with the equivalent
  `if` on disk. Authors keep projects under version control; the diff is the
  record. Adding brackets back recompiles them next launch.
- **File ordering.** A file that sorts *before* `00_wod_preprocess.rpy`
  (e.g. `000foo.rpy`) is parsed before the early block runs and is not
  auto-compiled. Keep the `00_` prefix ahead of author files, or use the CLI for
  those.
- **Untestable in CI here.** `.rpy`/`python early` behavior needs the Ren'Py SDK
  (the repo's standing strategy is "pytest for the Python engine, Ren'Py lint +
  manual playthrough for `.rpy`"). All transform logic — including the init-time
  gate — is covered by `tests/test_preprocess.py` against a stubbed `renpy`.

## Alternatives considered

- **`init python` rewrite** — too late; the file already failed to parse.
- **Monkeypatching the lexer/parser in `python early`** (transform source in
  memory, no disk writes) — also same-run and avoids touching files, but depends
  on private Ren'Py internals whose signatures drift across versions. Rejected in
  favor of the filesystem approach, which uses only documented behavior.
- **Generate `.rpy` from a separate source extension** (e.g. `*.rpy.in`) — clean
  separation, but changes the authoring model and is heavier than the issue asks.
  The CLI/init pass already operate on plain `.rpy`, so we kept that surface.
