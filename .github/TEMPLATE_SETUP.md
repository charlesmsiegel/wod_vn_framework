# Template Setup

After creating a new repo from this template:

1. **Delete the demo content:**
   ```bash
   rm -rf game/demo game/script.rpy
   ```

2. **Delete internal development docs** (optional — framework design history):
   ```bash
   rm -rf docs/internal
   ```

3. **Delete this file and make-project.sh:**
   ```bash
   rm .github/TEMPLATE_SETUP.md make-project.sh
   ```

4. **Create your project structure:**
   ```bash
   mkdir -p game/my_story/characters
   ```

5. **Create your protagonist** in `game/my_story/characters/` — see `docs/author-guide.md` for the YAML format.

6. **Create your script** in `game/script.rpy` — see `docs/author-guide.md` Section 2 for a starter template.

7. **Update `game/options.rpy`** — change the game name, version, and save directory.

8. **Update `README.md`** — replace with your game's description.

Alternatively, use `./make-project.sh <name>` to automate steps 1-7.
