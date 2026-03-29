## game/script.rpy
## WoD VN Framework Demo — Elena vs. the Technocratic Ward

## Declare Elena's character for dialogue
define elena = Character("Elena", color="#c9a96e")

## Declare pc variable for save/load compatibility
default pc = None


label start:

    ## Load the demo character
    $ pc = wod_core.load_character("demo/elena.yaml")
    $ wod_core.set_active(pc)

    scene black with fade

    "The server room hums with cold fluorescence. Rows of black monoliths blink in the dark."

    elena "There it is. The ward."

    "You can feel it — a Technocratic Pattern woven into the network's firmware. It pulses with rigid, static Resonance."

    "Your Avatar stirs. There are several ways to approach this."

    menu ward_choice:
        "Analyze the ward's Pattern" if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
            jump analyze_ward

        "Brute-force the encryption" if pc.gate("Technology", ">=", 3):
            jump brute_force

        "Observe the pattern carefully" if pc.gate("Awareness", ">=", 2):
            jump observe

        "This is beyond me. Leave.":
            jump leave


label analyze_ward:

    elena "I can see the threads. Forces and Prime, woven together. I can unravel this."

    "You reach out with your Avatar, channeling Quintessence into the Pattern."

    $ success = pc.spend("quintessence", 3)

    if success:
        "Three points of Quintessence flow from you into the ward. The rigid Pattern begins to dissolve."

        if pc.gate("Forces", ">=", 3):
            "Your understanding of Forces lets you unravel the energy matrix cleanly."
            "But the Consensus pushes back. The ward was {i}expected{/i} to be there."
            $ pc.gain("paradox", 2)
            "You feel Paradox settle into your Pattern like static on a screen."
            elena "Done. But the Consensus noticed. [pc.resources.current('paradox')] points of Paradox."
            elena "And my Quintessence is down to [pc.resources.current('quintessence')]."
        else:
            "You manage to disrupt the ward, but the unraveling is rough."
            $ pc.gain("paradox", 4)
            elena "Sloppy. Too much Paradox."
    else:
        elena "Not enough Quintessence. I need to find another way."
        jump ward_choice

    jump epilogue


label brute_force:

    elena "I don't need magick for this. Good old-fashioned hacking."

    "Your fingers fly across the keyboard. Technology [pc.get('Technology')], don't fail me now."

    "The encryption is military-grade, but you know Technocratic patterns."

    if pc.gate("Science", ">=", 4):
        "Your deep understanding of the underlying Science lets you find a flaw in the algorithm."
        elena "There. Buffer overflow in the authentication layer. Classic."
        "You slip past the ward without triggering it. No Paradox. No trace."
    else:
        "You crack the outer layer, but the ward's core remains intact."
        elena "Partial access. Better than nothing, but they'll know someone was here."

    jump epilogue


label observe:

    elena "Let me watch it for a moment. There's always a pattern within the Pattern."

    "You quiet your mind and let your Awareness expand."

    "The ward pulses. Every seven seconds, there's a gap — a brief moment where the Pattern thins."

    "Your understanding deepens. You feel your Awareness sharpen."

    $ pc.advance("Awareness")

    elena "Awareness advanced to [pc.get('Awareness')]. I can see more clearly now."

    "With this new insight, you could try a more direct approach."

    menu:
        "Analyze the ward now" if pc.gate("Forces", ">=", 3) and pc.gate("Prime", ">=", 2):
            jump analyze_ward

        "Try the brute-force approach" if pc.gate("Technology", ">=", 3):
            jump brute_force

        "I've learned what I can. Time to go.":
            jump leave


label leave:

    elena "Not today. I'll be back when I'm ready."

    "You shut down your terminal and walk away. The ward continues to pulse, undisturbed."

    "Sometimes discretion is the better part of valor."

    jump epilogue


label epilogue:

    scene black with fade

    "— End of Demo —"

    "This demo exercised the WoD VN Framework's core features:"
    "  - Character loading from YAML"
    "  - Stat-gated menu choices (Forces, Prime, Technology, Awareness)"
    "  - Resource spending (Quintessence)"
    "  - Linked pool constraints (Paradox gain)"
    "  - Outcome branching based on stat levels"
    "  - Mid-story stat advancement (Awareness)"

    if pc is not None:
        "Final character state:"
        "  Quintessence: [pc.resources.current('quintessence')]"
        "  Paradox: [pc.resources.current('paradox')]"
        "  Awareness: [pc.get('Awareness')]"

    return
