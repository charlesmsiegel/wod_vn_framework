#!/usr/bin/env bash
#
# Create a new WoD VN Framework game project.
#
# Usage:
#   ./make-project.sh <project-name> [destination-dir]
#
# Examples:
#   ./make-project.sh my-mage-game
#   ./make-project.sh my-mage-game ~/projects/
#
# This script:
#   1. Copies the framework into a new directory
#   2. Strips the demo content (demo/, script.rpy)
#   3. Creates a starter script.rpy and character directory
#   4. Reinitializes git
#   5. Prints next steps

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <project-name> [destination-dir]"
    echo ""
    echo "Examples:"
    echo "  $0 my-mage-game"
    echo "  $0 my-mage-game ~/projects/"
    exit 1
fi

PROJECT_NAME="$1"
DEST_DIR="${2:-.}"
PROJECT_PATH="$DEST_DIR/$PROJECT_NAME"

if [ -d "$PROJECT_PATH" ]; then
    echo "Error: $PROJECT_PATH already exists."
    exit 1
fi

echo "Creating new WoD VN project: $PROJECT_NAME"
echo ""

# Copy framework
cp -r "$SCRIPT_DIR" "$PROJECT_PATH"

cd "$PROJECT_PATH"

# Remove framework development artifacts
rm -rf .git
rm -rf docs/internal
rm -rf .superpowers
rm -f make-project.sh

# Remove demo content
rm -rf game/demo
rm -f game/script.rpy

# Create starter project structure
mkdir -p game/my_story/characters

# Create starter character
cat > game/my_story/characters/protagonist.yaml << 'YAML'
# Your protagonist — customize this!
schema: mage
template: default_mage
character_type: pc

identity:
  name: "Your Character"
  tradition: "Virtual Adepts"
  essence: "Dynamic"
  nature: "Visionary"
  demeanor: "Architect"

traits:
  attributes:
    Strength: 2
    Dexterity: 2
    Stamina: 2
    Charisma: 2
    Manipulation: 2
    Appearance: 2
    Perception: 3
    Intelligence: 3
    Wits: 3
  abilities:
    Awareness: 2
    Occult: 2
    Technology: 2
  spheres:
    Forces: 1
    Prime: 1
  arete:
    Arete: 1
  backgrounds:
    Avatar: 2

resources:
  quintessence: 3
  paradox: 0
  willpower: 5

merits_flaws: []
YAML

# Create starter script
cat > game/script.rpy << 'RENPY'
## game/script.rpy
## Your WoD Visual Novel — start here!

define protagonist = Character("???", color="#b8860b")

default pc = None


label start:

    ## Load your character
    $ pc = wod_core.load_character("my_story/characters/protagonist.yaml")
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()

    scene black with fade

    "Your story begins here."

    ## Example: a stat-gated choice
    menu:
        "Use your knowledge of Forces" if pc.gate("Forces", ">=", 1):
            "The energies respond to your will."

        "Observe carefully" if pc.gate("Awareness", ">=", 2):
            "You notice something others would miss."

        "Do nothing":
            "You wait and watch."

    "To be continued..."

    return
RENPY

# Update options.rpy project name
sed -i "s/WoD VN Framework Demo/$PROJECT_NAME/" game/options.rpy
sed -i "s/wod_vn_demo/$(echo "$PROJECT_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')/" game/options.rpy

# Initialize fresh git repo
git init
git add -A
git commit -m "Initial commit — $PROJECT_NAME (from WoD VN Framework)"

echo ""
echo "========================================="
echo "  Project created: $PROJECT_PATH"
echo "========================================="
echo ""
echo "Next steps:"
echo "  cd $PROJECT_PATH"
echo "  renpy.sh game/                    # Run the game"
echo "  renpy.sh game lint                # Check for errors"
echo ""
echo "Start writing:"
echo "  game/script.rpy                   # Your story script"
echo "  game/my_story/characters/         # Your character files"
echo ""
echo "See docs/author-guide.md for the full reference."
echo ""
