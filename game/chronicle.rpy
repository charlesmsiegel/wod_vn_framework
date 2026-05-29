## game/chronicle.rpy
## ===========================================================================
##  THE HOLLOW VIGIL  --  a Mage: The Ascension demo chronicle (5 scenes)
## ===========================================================================
##
##  A complete, branching short story for the WoD VN Framework. It exercises:
##    * Character loading from YAML + set_active + the resource HUD
##    * Stat-gated menu choices (Spheres, Abilities, Backgrounds, resources),
##      including "premium" gates that stay hidden for the demo protagonist
##    * Merit / Flaw checks via pc.has() (Natural Channel, Nightmares)
##    * Resource spend / gain: Quintessence, Willpower, Health
##    * The linked Quintessence/Paradox Wheel (gaining Paradox pushes the Wheel)
##    * Mid-story trait advancement (pc.advance)
##    * Toast notifications and identity-field interpolation
##    * Multi-ending outcome branching
##
##  ART: every `scene`/`show` below resolves through game/images.rpy. With no
##  art installed, each renders a labelled PLACEHOLDER, so the chronicle is
##  fully playable as-is. See game/images/manifest.yaml for the asset list.
##
##  Reached from the launcher in script.rpy:  label start -> chronicle_start.

## ---- Speakers --------------------------------------------------------------
define soraya = Character("Soraya", color="#c9a96e")
define vance  = Character("Vance",  color="#b9c0c9")
define wraith = Character("Vance",  color="#a85f86")   # the Paradox-touched form
define corvin = Character("Corvin", color="#8fb9a9")

## ---- Chronicle state (shared with save/load) -------------------------------
default hv_knows_node   = False    # learned the Node is the key (Scene 1)
default hv_saw_familiar = False    # perceived Corvin via Spirit (Scene 2)
default hv_clue         = None     # what Scene 2 investigation revealed
default hv_studied      = False    # one-time advancement guard (Scene 2)
default hv_battered     = False    # took the breach the hard way (Scene 3)
default hv_mentor_fate  = None     # released / anchored / reconciled / fled


## ===========================================================================
##  SCENE 1  --  THE SUMMONS
## ===========================================================================
label chronicle_start:

    $ pc = wod_core.load_character("demo/soraya.yaml")
    $ wod_core.set_active(pc)
    $ wod_core.show_hud()
    $ wod_core.show_toast("The Hollow Vigil")

    $ pcname = pc.identity["name"]
    $ pctrad = pc.identity.get("tradition", "a willworker")

    scene apartment_night with fade
    show chronicle_title at truecenter with dissolve
    "{i}The Hollow Vigil{/i} — a Mage: The Ascension demo chronicle."
    hide chronicle_title with dissolve

    "Rain works the window like fingers. On your desk the ward-bell sits silent — and a silent ward-bell is the loudest thing in the world."

    show soraya neutral at center with dissolve

    soraya "Thirty years he's kept the new-moon vigil, and tonight the bell goes still."

    "You are [pcname], of the [pctrad]. Magister Aurelio Vance took you as apprentice when no one else would. His wards have never once gone dark."

    "They are dark now."

    if pc.has("Nightmares"):
        "Last night the dream came again: a candle that would not gutter, and your teacher's voice reciting coordinates you could not write down fast enough."
        soraya "...I should have listened to the dream."

    "There are a few ways to begin."

    menu:
        "Reach along the bond you share with your mentor" if pc.gate("Mentor", ">=", 3):
            soraya "He taught me that a teacher leaves a thread in the student. Let me follow it."
            "You quiet your mind and feel for him. The thread runs taut — downward, toward stone, toward the Node beneath his chantry."
            $ hv_knows_node = True

        "Comb his last letter for a cipher" if pc.gate("Investigation", ">=", 2):
            "You spread his final letter under the lamp. Beneath the pleasantries, an acrostic: NODE FAILING. HELD IT MYSELF."
            soraya "He was holding the Node open by hand. Oh, you stubborn old man."
            $ hv_knows_node = True

        # Premium gate — hidden for the demo protagonist (Correspondence 1).
        "Scry his exact location across the city" if pc.gate("Correspondence", ">=", 3):
            "Distance folds. You stand, for a heartbeat, in his sanctum's air."
            $ hv_knows_node = True

        "Stop guessing. Go to the chantry now.":
            soraya "Enough. I'll find out when I get there."

    "Either way, the answer is the same: his chantry, across the rain-dark city."

    jump hv_travel


## ===========================================================================
##  SCENE 2  --  THE SANCTUM
## ===========================================================================
label hv_travel:

    scene rain_street with fade
    "The streets give you nothing but reflections. The chantry waits at the end of the row, hunched against the storm."

    scene chantry_exterior with fade
    "The iron gate stands ajar. One upper window burns amber. The steps are slick with fog that has no business being this thick."

    soraya "The wards should have stopped me at the gate. They don't even notice me."

    scene sanctum_library with fade
    show soraya neutral at right with dissolve

    "His sanctum library: two storeys of shelves, the great brass orrery — stopped — and a worktable drowned in star-charts. No Vance."

    if pc.gate("Spirit", ">=", 2):
        $ hv_saw_familiar = True
        show corvin at left with dissolve
        "A weight settles on the orrery. To your Spirit-sight a raven resolves out of the gloom, limned in cold silver."
        corvin "Apprentice. He told me you'd come, or no one would."
        corvin "He went {i}down{/i}. He's been holding the vigil three days. There's not enough of him left to hold it three more."
        soraya "Corvin. Where — the Node?"
        corvin "Where else. Look first. He left you reasons."
    else:
        "A raven watches you from the stopped orrery. You cannot quite hear what it is trying to say."

    "Something below pulls at the edge of your attention. But Vance never did anything without leaving his reasons in the room."

    menu:
        "Read the residue of his last working" if pc.gate("Prime", ">=", 2):
            soraya "Prime first. Let me see what he spent himself on."
            $ ok = pc.spend("quintessence", 2)
            if ok:
                scene sanctum_residue with dissolve
                show soraya focused at right with dissolve
                if hv_saw_familiar:
                    show corvin at left
                "You burn two motes of Quintessence and the room blooms into Awakened sight: violet residue everywhere, all of it pouring {i}down{/i}."
                $ gained = pc.gain("paradox", 1)
                "A thread of someone else's Paradox clings to you on the way out — [gained] point of it."
                $ hv_clue = "He poured his whole Pattern into the Node to keep it open."
                soraya "He's been feeding it himself. Pattern and all."
            else:
                "Your reserves are too thin to spare even that. The residue stays just out of focus."
                $ hv_clue = "His working led downward, toward the Node."

        "Decipher the sigils burned into the desk" if pc.gate("Occult", ">=", 3):
            "The scorched sigils name the working in old Hermetic shorthand: {i}Vigil of the Hollow Hour{/i} — to hold a dying Node open by will alone."
            $ hv_clue = "The working is the Hollow Vigil: holding a dying Node open by will alone."
            soraya "A working with no end condition. It only stops when {i}you{/i} do."

        "Search the worktable and shelves" if pc.gate("Investigation", ">=", 3):
            "His journal lies open to the last entry: {i}The Technocrats found the Node. They mean to bleed it dry. I will not let them. If I must be the wall, I will be the wall.{/i}"
            $ hv_clue = "The Technocracy was draining the Node; Vance made himself its wall."
            soraya "You didn't call for help. You never call for help."

        "Open your senses to the whole room" if pc.gate("Awareness", ">=", 3):
            "You let your Awareness widen. The library is a held breath. Far below, something is straining — a chord pulled a half-step sharp and never released."
            $ hv_clue = "Something far below is straining, about to give."
            soraya "Whatever he's doing, it's about to break."

        "Skip the reading — go straight down.":
            soraya "No time for forensics. Down."
            $ hv_clue = None

    if not hv_studied:
        $ hv_studied = True
        $ pc.advance("Cosmology")
        $ wod_core.show_toast("Cosmology advanced to %d" % pc.get("Cosmology"))
        "Piecing his logic together sharpens your own grasp of how Nodes and ley-lines truly knit. (Cosmology is now [pc.get('Cosmology')].)"

    "The pull from the stairwell is a cold hand on the back of your neck now. You go down."

    jump hv_scene3


## ===========================================================================
##  SCENE 3  --  THE BREACH
## ===========================================================================
label hv_scene3:

    scene node_chamber with fade
    show soraya neutral at center with dissolve

    "The undercroft should glow. The Node — a spring of pure Quintessence in the living rock — should fill this chamber with steady gold."

    "Instead it gutters like a candle in a draught, and the draught is coming from a {i}wound{/i} in the air above it."

    if hv_knows_node:
        soraya "Just as the thread warned me. The vigil's failing — and the Node is tearing open."
    else:
        soraya "So {i}this{/i} is what he hid down here. The vigil's failing, and the Node is tearing open."

    # Merit beat: Natural Channel lets her draw on the Node before acting.
    if pc.has("Natural Channel"):
        "As a Natural Channel, you feel the Node's Quintessence lean toward you, eager, even now."
        menu:
            "Draw on the Node to steady your reserves" if pc.gate("quintessence", "<", 18):
                $ got = pc.gain("quintessence", 3)
                $ wod_core.show_toast("Channelled +%d Quintessence" % got)
                "Gold floods your Pattern. You hold [pc.resources.current('quintessence')] now."
                soraya "Forgive me. I'll give it back if there's anything left to give it to."

            "Leave the dying Node its strength":
                soraya "No. It's bleeding out. I won't be one more thing draining it."

    "The tear yawns wider. Charts lift off the floor. You have one move before it floods the chantry above."

    scene cg_breach with dissolve
    "Light the colour of a bruise blossoms out of the wound. It is now or not at all."
    scene node_breach with dissolve
    show soraya focused at center with dissolve

    menu:
        "Damp the surge with raw Forces" if pc.gate("Forces", ">=", 3):
            jump hv_stab_forces

        # Premium gate — hidden for the demo protagonist (Correspondence 1).
        "Reroute the flow through Correspondence" if pc.gate("Correspondence", ">=", 2):
            jump hv_stab_corr

        "Seal the spirit-breach with a ward" if pc.gate("Spirit", ">=", 2):
            jump hv_stab_spirit

        "No finesse left — raise a shield and ride it out":
            jump hv_stab_shield


label hv_stab_forces:
    soraya "Forces, then. Pull the heat out of it before it blows."
    $ ok = pc.spend("quintessence", 3)
    if ok:
        "You reach into the surge and {i}wrench{/i}. The wound's roar drops to a sullen hiss."
        $ gained = pc.gain("paradox", 2)
        "But reality keeps its ledger. [gained] points of Paradox crackle into your Pattern."
        if pc.gate("paradox", ">=", 4):
            show soraya strained at center with dissolve
            $ pc.spend("health", 1)
            $ wod_core.show_toast("Paradox backlash!")
            $ hv_battered = True
            "The static lashes back across your skin. It {i}hurts.{/i}"
        soraya "Held. Barely."
    else:
        "Your reserves gutter out mid-cast — not enough Quintessence to bend it."
        $ pc.spend("willpower", 1)
        $ pc.spend("health", 1)
        $ hv_battered = True
        "You take the surge on your own Pattern instead. It leaves a mark."
    jump hv_after_breach


label hv_stab_corr:
    # Hidden for Soraya; present for characters with Correspondence 2+.
    soraya "Don't fight it — move it. Send the overflow somewhere it can do no harm."
    $ pc.spend("quintessence", 2)
    "You fold the torn space against itself and route the surge out into the empty dark between places. The wound closes seamlessly."
    jump hv_after_breach


label hv_stab_spirit:
    soraya "A spirit-breach needs a spirit-ward. Hold still."
    $ ok = pc.spend("quintessence", 2)
    if ok:
        $ pc.spend("willpower", 1)
        "You weave a lattice of Spirit across the tear. Edge by edge it knits shut, sealed in cold silver."
        if hv_saw_familiar:
            corvin "Clean work. He'd have said so himself."
        soraya "It'll hold. For now."
    else:
        $ pc.spend("willpower", 1)
        $ pc.spend("health", 1)
        $ hv_battered = True
        "You haven't the Quintessence to anchor the ward, so you anchor it with yourself. It holds — and it costs."
    jump hv_after_breach


label hv_stab_shield:
    show soraya strained at center with dissolve
    soraya "No finesse left. Just endure."
    $ pc.spend("willpower", 1)
    $ pc.spend("health", 1)
    $ hv_battered = True
    "You wrap yourself in a flat wall of will and let the wound scream itself hoarse. When it finally sags shut, so do you, almost."
    jump hv_after_breach


label hv_after_breach:
    "The breach quiets to a seam. But the chamber is not empty now."
    if hv_clue:
        "What you pieced together upstairs settles into place: [hv_clue]"
    "Something stands over the guttering Node — a figure of candle-shadow and static, still holding a working that should have ended days ago."
    soraya "...Vance."
    jump hv_scene4


## ===========================================================================
##  SCENE 4  --  THE VIGIL  (climax)
## ===========================================================================
label hv_scene4:

    scene vigil_threshold with fade
    show vance wraith at center with dissolve

    "The chamber thins into a threshold — an endless candle-lit corridor folding into starless dark. Here the vigil is being kept, and the one keeping it has paid for every hour in Pattern."

    wraith "Not... finished. The wall holds. I hold. Go back, apprentice, the wall holds —"

    "Paradox has him by the seams. Half Vance, half blown-out screen. He has held the Node open so long he has forgotten he is allowed to stop."

    if hv_saw_familiar:
        show corvin at left with dissolve
        corvin "He can't hear reason as reason anymore. You'll have to mean it with everything you've got."

    soraya "Magister. The Technocrats are gone. The vigil's over. You can let go."
    wraith "Can't. If I let go the Node dies. If the Node dies they win. Can't, can't —"

    "You will have to steady yourself before you do anything in this place."

    menu:
        "Sever the vigil — release him and the Node together" if pc.gate("Spirit", ">=", 2) and pc.gate("Prime", ">=", 2):
            $ ok = pc.spend("quintessence", 3)
            if ok:
                $ pc.spend("willpower", 1)
                scene cg_severance with dissolve
                "You shape a blade of Prime and Spirit and bring it down on the tether binding him to the Node. For one instant his face is wholly his own."
                vance "...Ah. {i}There{/i} you are. Good girl. Let it go, both of us — let it —"
                "The tether parts. The Node sighs out its last gold light and goes quiet, whole. Vance goes with it, freed."
                $ hv_mentor_fate = "released"
            else:
                "You haven't the Quintessence to shape the blade. The working stutters and dies in your hands."
                soraya "No — not enough —"
                $ hv_mentor_fate = "fled"
                jump hv_scene5

        "Anchor him — pour your own Pattern into his" if pc.gate("Prime", ">=", 2):
            $ ok = pc.spend("quintessence", 4)
            if ok:
                $ pc.spend("willpower", 2)
                show soraya strained at center with dissolve
                "You drive your own Pattern into the gaps in his, a splint of living Prime. It is reckless and it half-works."
                $ pc.gain("paradox", 2)
                "The wraith-static recedes. What's left of Vance sags into something that can, at least, be carried out."
                vance "...shouldn't have. Foolish... thank you."
                $ hv_mentor_fate = "anchored"
            else:
                "You reach for the Quintessence to anchor him and close on nothing. There isn't enough of you to splint him with."
                $ pc.spend("willpower", 1)
                $ hv_mentor_fate = "fled"
                jump hv_scene5

        "Reach him through the bond he left in you" if pc.gate("Mentor", ">=", 3):
            $ pc.spend("willpower", 2)
            "You stop casting. You follow the teacher's-thread instead, the one he tied in you years ago, and you {i}pull{/i} — not the Node, him."
            soraya "You taught me a vigil is a promise to {i}watch{/i}, not to become the wall. Keep your own teaching. I'll watch now. Rest."
            "Something in the static stills. Listens. Remembers it has a name."
            show vance calm at center with dissolve
            vance "...Soraya. Yes. Yes — I can put it down. {i}You'll{/i} watch."
            "He lets go by his own hand, and the Node closes gently around the choice."
            $ hv_mentor_fate = "reconciled"

        # Premium gate — hidden for the demo protagonist (Forces 3).
        "Overpower the wraith outright" if pc.gate("Forces", ">=", 4):
            $ pc.spend("quintessence", 4)
            "You hit the working like a hammer and it simply comes apart."
            $ hv_mentor_fate = "released"

        "You can't do this. Flee the threshold.":
            soraya "I'm sorry. I'm not strong enough for this."
            "You turn and run. Behind you the vigil finally fails on its own terms, and the Node tears wide before it dies."
            $ pc.gain("paradox", 3)
            $ hv_mentor_fate = "fled"

    jump hv_scene5


## ===========================================================================
##  SCENE 5  --  AFTERMATH
## ===========================================================================
label hv_scene5:

    scene dawn_rooftop with fade
    if hv_battered:
        show soraya strained at center with dissolve
    else:
        show soraya neutral at center with dissolve

    "Dawn finds the rooftop the colour of weak tea. The storm has wrung itself out. Below, the city has no idea how close it came."

    if hv_mentor_fate == "reconciled":
        "He is gone, but he went as himself — by his own choice, at the end of a promise kept. That is as much as any mage gets."
        soraya "You watched over me. I watched you out. We're square, old man."
    elif hv_mentor_fate == "released":
        "You freed him with a blade of his own teaching. Clean, and final, and kinder than the alternative."
        soraya "Rest. The vigil's mine now, and I'll keep it the way you should have — by knowing when to stop."
    elif hv_mentor_fate == "anchored":
        "He breathes. Diminished, hollowed, but breathing — and the Paradox you took on to do it sits in your chest like a swallowed coal."
        soraya "You'll hate being saved. I'll live with that. We both will."
    else:  # fled
        "You ran, and the Node died screaming, and Vance with it. The chantry stands empty above a dark spring. You will carry that."
        soraya "...I'll be ready next time. I have to be."

    if hv_saw_familiar:
        show corvin at left with dissolve
        if hv_mentor_fate == "fled":
            corvin "He chose his vigil. You'll choose a better one. I'll be watching to make sure."
        else:
            corvin "A familiar outlives its mage. I'll keep your hours now, apprentice — Magister."
        soraya "...I'd like that, Corvin."

    "You take stock of what the night cost you."

    scene black with fade

    "{i}— The Hollow Vigil —{/i}"

    # Precompute final-state values to keep interpolation simple and safe.
    $ final_name = pc.identity["name"]
    $ final_trad = pc.identity.get("tradition", "")
    $ q_now = pc.resources.current("quintessence")
    $ p_now = pc.resources.current("paradox")
    $ wp_now = pc.resources.current("willpower")
    $ wp_max = pc.resources.pools["willpower"].max
    $ hp_now = pc.resources.current("health")
    $ hp_max = pc.resources.pools["health"].max
    $ cosmo = pc.get("Cosmology")
    $ arete = pc.get("Arete")

    "Final state of [final_name], [final_trad]:"
    "  Quintessence: [q_now]   Paradox: [p_now]"
    "  Willpower: [wp_now]/[wp_max]   Health: [hp_now]/[hp_max]"
    "  Cosmology: [cosmo]   Arete: [arete]"

    "This chronicle exercised the WoD VN Framework:"
    "  - YAML character loading, set_active, and the persistent resource HUD"
    "  - Stat-gated choices across Spheres, Abilities, Backgrounds, and resources"
    "  - Hidden 'premium' gates (Correspondence and Forces) the protagonist can't reach"
    "  - Merit and Flaw checks (Natural Channel, Nightmares)"
    "  - Quintessence / Willpower / Health spending and the Quintessence–Paradox Wheel"
    "  - Mid-story advancement (Cosmology) and multi-ending branching"

    $ wod_core.hide_hud()
    return
