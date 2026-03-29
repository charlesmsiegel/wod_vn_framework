## game/wod_screens/chargen.rpy
## WoD VN Framework — Character creation screens for all three modes.

################################################################################
## SHARED NAVIGATION BAR
################################################################################

screen chargen_nav(state, can_next=True, can_back=True, show_confirm=False):
    ## Top navigation bar with step indicator and nav buttons.
    frame:
        xfill True
        ysize 80
        background "#0d0d1a"
        padding (20, 10, 20, 10)

        hbox:
            yalign 0.5
            spacing 10

            # Step indicators
            for i, sname in enumerate(state.steps):
                $ step_label = sname.replace("_", " ").title()
                if i == state.current_step:
                    text "[step_label]" size 13 color "#c9a96e" bold True
                elif i in state.completed:
                    text "[step_label]" size 12 color "#6a9e6a"
                else:
                    text "[step_label]" size 12 color "#555555"

                if i < len(state.steps) - 1:
                    text ">" size 12 color "#333333"

            null width 0 xfill True

            # Navigation buttons
            if can_back and state.current_step > 0:
                textbutton "Back" action Return({"action": "back"}) text_size 16 text_color "#888888" text_hover_color "#ffffff"

            textbutton "Cancel" action Return({"action": "cancel"}) text_size 16 text_color "#884444" text_hover_color "#ff6666"

            if show_confirm:
                textbutton "Confirm" action Return({"action": "confirm"}) text_size 16 text_color "#6a9e6a" text_hover_color "#88cc88"


################################################################################
## 1. IDENTITY SCREEN (full + simplified + template modes)
################################################################################

screen chargen_identity(state):
    modal True
    default name_input = state.data.get("identity", {}).get("name", "")
    default selected_tradition = state.data.get("identity", {}).get("tradition", "")
    default selected_essence = state.data.get("identity", {}).get("essence", "")
    default selected_nature = state.data.get("identity", {}).get("nature", "")
    default selected_demeanor = state.data.get("identity", {}).get("demeanor", "")

    $ traditions = state.get_traditions()
    $ archetypes = state.get_archetypes()
    $ essences = state.get_essences()
    $ is_full = (state.mode == "full")

    # Check if we can proceed
    $ can_proceed = len(name_input) > 0 and len(selected_tradition) > 0

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=can_proceed, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Identity" size 28 color "#c9a96e"
                        null height 5

                        # Name input
                        text "Character Name:" size 16 color "#e0e0e0"
                        frame:
                            xsize 400
                            ysize 40
                            background "#2a2a3e"
                            padding (10, 5, 10, 5)
                            input:
                                value ScreenVariableInputValue("name_input")
                                size 18
                                color "#ffffff"

                        null height 10

                        # Tradition picker
                        text "Tradition:" size 16 color "#e0e0e0"
                        frame:
                            xfill True
                            background "#222238"
                            padding (10, 10, 10, 10)
                            vbox:
                                spacing 5
                                for trad in traditions:
                                    $ trad_name = trad["name"]
                                    $ trad_sphere = trad.get("affinity_sphere", "")
                                    $ trad_color = "#c9a96e" if selected_tradition == trad_name else "#888888"
                                    textbutton "[trad_name] (Affinity: [trad_sphere])":
                                        text_size 14
                                        text_color trad_color
                                        text_hover_color "#ffffff"
                                        action SetScreenVariable("selected_tradition", trad_name)

                        if is_full:
                            null height 10

                            # Essence picker
                            text "Essence:" size 16 color "#e0e0e0"
                            hbox:
                                spacing 15
                                for ess in essences:
                                    $ ess_color = "#c9a96e" if selected_essence == ess else "#888888"
                                    textbutton "[ess]":
                                        text_size 14
                                        text_color ess_color
                                        text_hover_color "#ffffff"
                                        action SetScreenVariable("selected_essence", ess)

                            null height 10

                            # Nature picker
                            text "Nature:" size 16 color "#e0e0e0"
                            frame:
                                xfill True
                                background "#222238"
                                padding (10, 10, 10, 10)
                                hbox:
                                    spacing 5
                                    box_wrap True
                                    for arch in archetypes:
                                        $ arch_color = "#c9a96e" if selected_nature == arch else "#888888"
                                        textbutton "[arch]":
                                            text_size 12
                                            text_color arch_color
                                            text_hover_color "#ffffff"
                                            action SetScreenVariable("selected_nature", arch)

                            null height 10

                            # Demeanor picker
                            text "Demeanor:" size 16 color "#e0e0e0"
                            frame:
                                xfill True
                                background "#222238"
                                padding (10, 10, 10, 10)
                                hbox:
                                    spacing 5
                                    box_wrap True
                                    for arch in archetypes:
                                        $ arch_color = "#c9a96e" if selected_demeanor == arch else "#888888"
                                        textbutton "[arch]":
                                            text_size 12
                                            text_color arch_color
                                            text_hover_color "#ffffff"
                                            action SetScreenVariable("selected_demeanor", arch)

                        null height 20

                        if can_proceed:
                            $ next_result = {"action": "next", "name": name_input, "tradition": selected_tradition, "essence": selected_essence, "nature": selected_nature, "demeanor": selected_demeanor}
                            textbutton "Next Step >>":
                                text_size 18
                                text_color "#c9a96e"
                                text_hover_color "#e0c080"
                                action Return(next_result)
                        else:
                            text "Please enter a name and select a Tradition to continue." size 14 color "#884444" italic True


################################################################################
## 2. ATTRIBUTE PRIORITY SCREEN (full mode)
################################################################################

screen chargen_attribute_priority(state):
    modal True
    default physical_rank = state.data.get("attribute_priority", {}).get("physical", 0)
    default social_rank = state.data.get("attribute_priority", {}).get("social", 0)
    default mental_rank = state.data.get("attribute_priority", {}).get("mental", 0)

    $ attr_cat = state.schema.categories.get("attributes")
    $ priorities = state.config["modes"]["full"]["attribute_priorities"]
    $ pri_labels = {priorities[0]: "Primary", priorities[1]: "Secondary", priorities[2]: "Tertiary"}

    # Determine which ranks are taken
    $ used_ranks = []
    python:
        used_ranks = []
        if physical_rank > 0:
            used_ranks.append(physical_rank)
        if social_rank > 0:
            used_ranks.append(social_rank)
        if mental_rank > 0:
            used_ranks.append(mental_rank)

    $ all_assigned = (physical_rank > 0 and social_rank > 0 and mental_rank > 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_assigned, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 30, 40, 30)

                vbox:
                    spacing 20
                    xfill True

                    text "Attribute Priorities" size 28 color "#c9a96e"
                    text "Assign Primary ([priorities[0]]), Secondary ([priorities[1]]), and Tertiary ([priorities[2]]) to your attribute groups." size 14 color "#aaaaaa"

                    null height 10

                    hbox:
                        spacing 30
                        xfill True

                        # Physical column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Physical" size 20 color "#c9a96e" xalign 0.5
                                if attr_cat is not None and attr_cat.groups is not None:
                                    for trait_name in attr_cat.groups.get("physical", []):
                                        text "[trait_name]" size 14 color "#bbbbbb" xalign 0.5
                                null height 5
                                if physical_rank > 0:
                                    $ phys_label = pri_labels.get(physical_rank, str(physical_rank))
                                    text "[phys_label] ([physical_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == physical_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("physical_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("physical_rank", p)

                        # Social column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Social" size 20 color "#c9a96e" xalign 0.5
                                if attr_cat is not None and attr_cat.groups is not None:
                                    for trait_name in attr_cat.groups.get("social", []):
                                        text "[trait_name]" size 14 color "#bbbbbb" xalign 0.5
                                null height 5
                                if social_rank > 0:
                                    $ soc_label = pri_labels.get(social_rank, str(social_rank))
                                    text "[soc_label] ([social_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == social_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("social_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("social_rank", p)

                        # Mental column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Mental" size 20 color "#c9a96e" xalign 0.5
                                if attr_cat is not None and attr_cat.groups is not None:
                                    for trait_name in attr_cat.groups.get("mental", []):
                                        text "[trait_name]" size 14 color "#bbbbbb" xalign 0.5
                                null height 5
                                if mental_rank > 0:
                                    $ men_label = pri_labels.get(mental_rank, str(mental_rank))
                                    text "[men_label] ([mental_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == mental_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("mental_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("mental_rank", p)

                    null height 10

                    if all_assigned:
                        $ next_result = {"action": "next", "physical": physical_rank, "social": social_rank, "mental": mental_rank}
                        textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5


################################################################################
## 3. ATTRIBUTE ALLOCATE SCREEN (full mode)
################################################################################

screen chargen_attribute_allocate(state):
    modal True

    $ attr_cat = state.schema.categories.get("attributes")
    $ priority_data = state.data.get("attribute_priority", {})
    $ prev_alloc = state.data.get("attribute_allocate", {})

    # Build group -> dot budget mapping
    $ group_budgets = {}
    python:
        group_budgets = {}
        if attr_cat is not None and attr_cat.groups is not None:
            for gname in attr_cat.groups:
                group_budgets[gname] = priority_data.get(gname, 0)

    # Use screen-local allocations dict
    # Initialize from previous data or defaults (attributes start at 1)
    default alloc = {}
    python:
        if not alloc:
            if prev_alloc:
                alloc = dict(prev_alloc)
            else:
                if attr_cat is not None:
                    for tn in attr_cat.trait_names:
                        alloc[tn] = attr_cat.default

    # Calculate remaining per group
    $ group_remaining = {}
    python:
        group_remaining = {}
        if attr_cat is not None and attr_cat.groups is not None:
            for gname, traits in attr_cat.groups.items():
                budget = group_budgets.get(gname, 0)
                spent = sum(alloc.get(t, attr_cat.default) - attr_cat.default for t in traits)
                group_remaining[gname] = budget - spent

    $ all_spent = all(v == 0 for v in group_remaining.values()) if group_remaining else False
    $ attr_max = 5

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Allocate Attributes" size 28 color "#c9a96e"
                        text "Click dots to add/remove. Each attribute starts at 1." size 14 color "#aaaaaa"

                        null height 10

                        if attr_cat is not None and attr_cat.groups is not None:
                            hbox:
                                spacing 20
                                xfill True

                                for gname, traits in attr_cat.groups.items():
                                    $ grp_label = gname.capitalize()
                                    $ grp_budget = group_budgets.get(gname, 0)
                                    $ grp_remain = group_remaining.get(gname, 0)

                                    frame:
                                        xsize 320
                                        background "#222238"
                                        padding (15, 15, 15, 15)
                                        vbox:
                                            spacing 8
                                            text "[grp_label] (Remaining: [grp_remain]/[grp_budget])" size 16 color "#c9a96e"
                                            null height 5

                                            for trait_name in traits:
                                                $ cur_val = alloc.get(trait_name, 1)
                                                hbox:
                                                    spacing 8
                                                    text "[trait_name]" size 14 color "#e0e0e0" min_width 150
                                                    hbox:
                                                        spacing 3
                                                        for d in range(attr_max):
                                                            $ dot_num = d + 1
                                                            if dot_num <= cur_val:
                                                                # Filled dot — click to remove down to this level
                                                                # Only allow removing above the default (1)
                                                                if dot_num > 1:
                                                                    $ new_alloc = dict(alloc)
                                                                    $ new_alloc[trait_name] = dot_num - 1
                                                                    textbutton "\u25cf":
                                                                        text_size 16
                                                                        text_color "#c9a96e"
                                                                        text_hover_color "#ff8888"
                                                                        action SetScreenVariable("alloc", new_alloc)
                                                                else:
                                                                    text "\u25cf" size 16 color "#c9a96e"
                                                            else:
                                                                # Empty dot — click to fill up to this level
                                                                $ delta_needed = dot_num - cur_val
                                                                $ can_add = (grp_remain >= delta_needed) and (dot_num <= attr_max)
                                                                if can_add:
                                                                    $ new_alloc = dict(alloc)
                                                                    $ new_alloc[trait_name] = dot_num
                                                                    textbutton "\u25cb":
                                                                        text_size 16
                                                                        text_color "#444444"
                                                                        text_hover_color "#c9a96e"
                                                                        action SetScreenVariable("alloc", new_alloc)
                                                                else:
                                                                    text "\u25cb" size 16 color "#444444"

                        null height 15

                        if all_spent:
                            $ next_result = {"action": "next"}
                            python:
                                next_result = dict(alloc)
                                next_result["action"] = "next"
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 4. ABILITY PRIORITY SCREEN (full mode)
################################################################################

screen chargen_ability_priority(state):
    modal True
    default talents_rank = state.data.get("ability_priority", {}).get("talents", 0)
    default skills_rank = state.data.get("ability_priority", {}).get("skills", 0)
    default knowledges_rank = state.data.get("ability_priority", {}).get("knowledges", 0)

    $ abil_cat = state.schema.categories.get("abilities")
    $ priorities = state.config["modes"]["full"]["ability_priorities"]
    $ pri_labels = {priorities[0]: "Primary", priorities[1]: "Secondary", priorities[2]: "Tertiary"}

    $ used_ranks = []
    python:
        used_ranks = []
        if talents_rank > 0:
            used_ranks.append(talents_rank)
        if skills_rank > 0:
            used_ranks.append(skills_rank)
        if knowledges_rank > 0:
            used_ranks.append(knowledges_rank)

    $ all_assigned = (talents_rank > 0 and skills_rank > 0 and knowledges_rank > 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_assigned, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 30, 40, 30)

                vbox:
                    spacing 20
                    xfill True

                    text "Ability Priorities" size 28 color "#c9a96e"
                    text "Assign Primary ([priorities[0]]), Secondary ([priorities[1]]), and Tertiary ([priorities[2]]) to your ability groups." size 14 color "#aaaaaa"

                    null height 10

                    hbox:
                        spacing 30
                        xfill True

                        # Talents column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Talents" size 20 color "#c9a96e" xalign 0.5
                                if abil_cat is not None and abil_cat.groups is not None:
                                    for trait_name in abil_cat.groups.get("talents", []):
                                        text "[trait_name]" size 12 color "#bbbbbb" xalign 0.5
                                null height 5
                                if talents_rank > 0:
                                    $ tal_label = pri_labels.get(talents_rank, str(talents_rank))
                                    text "[tal_label] ([talents_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == talents_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("talents_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("talents_rank", p)

                        # Skills column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Skills" size 20 color "#c9a96e" xalign 0.5
                                if abil_cat is not None and abil_cat.groups is not None:
                                    for trait_name in abil_cat.groups.get("skills", []):
                                        text "[trait_name]" size 12 color "#bbbbbb" xalign 0.5
                                null height 5
                                if skills_rank > 0:
                                    $ skl_label = pri_labels.get(skills_rank, str(skills_rank))
                                    text "[skl_label] ([skills_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == skills_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("skills_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("skills_rank", p)

                        # Knowledges column
                        frame:
                            xsize 300
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 10
                                text "Knowledges" size 20 color "#c9a96e" xalign 0.5
                                if abil_cat is not None and abil_cat.groups is not None:
                                    for trait_name in abil_cat.groups.get("knowledges", []):
                                        text "[trait_name]" size 12 color "#bbbbbb" xalign 0.5
                                null height 5
                                if knowledges_rank > 0:
                                    $ know_label = pri_labels.get(knowledges_rank, str(knowledges_rank))
                                    text "[know_label] ([knowledges_rank] dots)" size 16 color "#6a9ec9" xalign 0.5
                                null height 5
                                for p in priorities:
                                    if p == knowledges_rank:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#c9a96e" xalign 0.5 action SetScreenVariable("knowledges_rank", 0)
                                    elif p not in used_ranks:
                                        $ btn_label = pri_labels.get(p, str(p)) + " (" + str(p) + ")"
                                        textbutton "[btn_label]" text_size 13 text_color "#888888" text_hover_color "#ffffff" xalign 0.5 action SetScreenVariable("knowledges_rank", p)

                    null height 10

                    if all_assigned:
                        $ next_result = {"action": "next", "talents": talents_rank, "skills": skills_rank, "knowledges": knowledges_rank}
                        textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5


################################################################################
## 5. ABILITY ALLOCATE SCREEN (full mode)
################################################################################

screen chargen_ability_allocate(state):
    modal True

    $ abil_cat = state.schema.categories.get("abilities")
    $ priority_data = state.data.get("ability_priority", {})
    $ prev_alloc = state.data.get("ability_allocate", {})
    $ ability_max_create = state.config["modes"]["full"].get("ability_max_at_creation", 3)

    # Build group -> dot budget mapping
    $ group_budgets = {}
    python:
        group_budgets = {}
        if abil_cat is not None and abil_cat.groups is not None:
            for gname in abil_cat.groups:
                group_budgets[gname] = priority_data.get(gname, 0)

    default alloc = {}
    python:
        if not alloc:
            if prev_alloc:
                alloc = dict(prev_alloc)
            else:
                if abil_cat is not None:
                    for tn in abil_cat.trait_names:
                        alloc[tn] = 0

    # Calculate remaining per group
    $ group_remaining = {}
    python:
        group_remaining = {}
        if abil_cat is not None and abil_cat.groups is not None:
            for gname, traits in abil_cat.groups.items():
                budget = group_budgets.get(gname, 0)
                spent = sum(alloc.get(t, 0) for t in traits)
                group_remaining[gname] = budget - spent

    $ all_spent = all(v == 0 for v in group_remaining.values()) if group_remaining else False

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Allocate Abilities" size 28 color "#c9a96e"
                        $ max_label = str(ability_max_create)
                        text "Click dots to add/remove. Max [max_label] per ability during creation." size 14 color "#aaaaaa"

                        null height 10

                        if abil_cat is not None and abil_cat.groups is not None:
                            for gname, traits in abil_cat.groups.items():
                                $ grp_label = gname.capitalize()
                                $ grp_budget = group_budgets.get(gname, 0)
                                $ grp_remain = group_remaining.get(gname, 0)

                                frame:
                                    xfill True
                                    background "#222238"
                                    padding (15, 10, 15, 10)
                                    vbox:
                                        spacing 5
                                        text "[grp_label] (Remaining: [grp_remain]/[grp_budget])" size 16 color "#c9a96e"
                                        null height 3

                                        for trait_name in traits:
                                            $ cur_val = alloc.get(trait_name, 0)
                                            hbox:
                                                spacing 8
                                                text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                                hbox:
                                                    spacing 3
                                                    for d in range(5):
                                                        $ dot_num = d + 1
                                                        if dot_num <= cur_val:
                                                            if dot_num > 0:
                                                                $ new_alloc = dict(alloc)
                                                                $ new_alloc[trait_name] = dot_num - 1
                                                                textbutton "\u25cf":
                                                                    text_size 16
                                                                    text_color "#c9a96e"
                                                                    text_hover_color "#ff8888"
                                                                    action SetScreenVariable("alloc", new_alloc)
                                                        else:
                                                            $ delta_needed = dot_num - cur_val
                                                            $ can_add = (grp_remain >= delta_needed) and (dot_num <= ability_max_create)
                                                            if can_add:
                                                                $ new_alloc = dict(alloc)
                                                                $ new_alloc[trait_name] = dot_num
                                                                textbutton "\u25cb":
                                                                    text_size 16
                                                                    text_color "#444444"
                                                                    text_hover_color "#c9a96e"
                                                                    action SetScreenVariable("alloc", new_alloc)
                                                            else:
                                                                text "\u25cb" size 16 color "#444444"

                                null height 5

                        null height 15

                        if all_spent:
                            $ next_result = {"action": "next"}
                            python:
                                next_result = dict(alloc)
                                next_result["action"] = "next"
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 6. SPHERES & BACKGROUNDS SCREEN (full mode)
################################################################################

screen chargen_spheres_backgrounds(state):
    modal True

    $ sphere_cat = state.schema.categories.get("spheres")
    $ bg_cat = state.schema.categories.get("backgrounds")
    $ mode_config = state.config["modes"]["full"]
    $ sphere_budget = mode_config.get("sphere_dots", 6)
    $ bg_budget = mode_config.get("background_dots", 7)
    $ starting_arete = mode_config.get("starting_arete", 1)
    $ prev_data = state.data.get("spheres_backgrounds", {})

    # Determine affinity sphere from tradition
    $ affinity_sphere = ""
    python:
        identity = state.data.get("identity", {})
        trad_name = identity.get("tradition", "")
        for t in state.get_traditions():
            if t["name"] == trad_name or t["id"] == trad_name:
                affinity_sphere = t.get("affinity_sphere", "")
                break

    default sphere_alloc = {}
    default bg_alloc = {}
    python:
        if not sphere_alloc:
            if prev_data.get("spheres"):
                sphere_alloc = dict(prev_data["spheres"])
            else:
                if sphere_cat is not None:
                    for tn in sphere_cat.trait_names:
                        sphere_alloc[tn] = 0
        if not bg_alloc:
            if prev_data.get("backgrounds"):
                bg_alloc = dict(prev_data["backgrounds"])
            else:
                if bg_cat is not None:
                    for tn in bg_cat.trait_names:
                        bg_alloc[tn] = 0

    $ sphere_spent = sum(sphere_alloc.values())
    $ sphere_remain = sphere_budget - sphere_spent
    $ bg_spent = sum(bg_alloc.values())
    $ bg_remain = bg_budget - bg_spent
    $ all_spent = (sphere_remain == 0 and bg_remain == 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Spheres & Backgrounds" size 28 color "#c9a96e"

                        null height 5

                        # Spheres section
                        hbox:
                            spacing 30
                            xfill True

                            frame:
                                xsize 500
                                background "#222238"
                                padding (15, 15, 15, 15)
                                vbox:
                                    spacing 8
                                    text "Spheres (Remaining: [sphere_remain]/[sphere_budget])" size 18 color "#c9a96e"
                                    text "No sphere can exceed Arete ([starting_arete])." size 12 color "#888888"
                                    if len(affinity_sphere) > 0:
                                        text "Affinity Sphere: [affinity_sphere]" size 12 color "#6a9ec9"
                                    null height 5

                                    if sphere_cat is not None:
                                        for trait_name in sphere_cat.trait_names:
                                            $ cur_val = sphere_alloc.get(trait_name, 0)
                                            $ is_affinity = (trait_name == affinity_sphere)
                                            $ name_color = "#6a9ec9" if is_affinity else "#e0e0e0"
                                            hbox:
                                                spacing 8
                                                text "[trait_name]" size 14 color name_color min_width 180
                                                hbox:
                                                    spacing 3
                                                    for d in range(5):
                                                        $ dot_num = d + 1
                                                        if dot_num <= cur_val:
                                                            $ new_sa = dict(sphere_alloc)
                                                            $ new_sa[trait_name] = dot_num - 1
                                                            textbutton "\u25cf":
                                                                text_size 16
                                                                text_color "#c9a96e"
                                                                text_hover_color "#ff8888"
                                                                action SetScreenVariable("sphere_alloc", new_sa)
                                                        else:
                                                            $ delta_needed = dot_num - cur_val
                                                            $ can_add = (sphere_remain >= delta_needed) and (dot_num <= starting_arete)
                                                            if can_add:
                                                                $ new_sa = dict(sphere_alloc)
                                                                $ new_sa[trait_name] = dot_num
                                                                textbutton "\u25cb":
                                                                    text_size 16
                                                                    text_color "#444444"
                                                                    text_hover_color "#c9a96e"
                                                                    action SetScreenVariable("sphere_alloc", new_sa)
                                                            else:
                                                                text "\u25cb" size 16 color "#444444"

                            # Backgrounds section
                            frame:
                                xsize 450
                                background "#222238"
                                padding (15, 15, 15, 15)
                                vbox:
                                    spacing 8
                                    text "Backgrounds (Remaining: [bg_remain]/[bg_budget])" size 18 color "#c9a96e"
                                    null height 5

                                    if bg_cat is not None:
                                        for trait_name in bg_cat.trait_names:
                                            $ cur_val = bg_alloc.get(trait_name, 0)
                                            hbox:
                                                spacing 8
                                                text "[trait_name]" size 14 color "#e0e0e0" min_width 150
                                                hbox:
                                                    spacing 3
                                                    for d in range(5):
                                                        $ dot_num = d + 1
                                                        if dot_num <= cur_val:
                                                            $ new_ba = dict(bg_alloc)
                                                            $ new_ba[trait_name] = dot_num - 1
                                                            textbutton "\u25cf":
                                                                text_size 16
                                                                text_color "#c9a96e"
                                                                text_hover_color "#ff8888"
                                                                action SetScreenVariable("bg_alloc", new_ba)
                                                        else:
                                                            $ delta_needed = dot_num - cur_val
                                                            $ can_add = (bg_remain >= delta_needed) and (dot_num <= 5)
                                                            if can_add:
                                                                $ new_ba = dict(bg_alloc)
                                                                $ new_ba[trait_name] = dot_num
                                                                textbutton "\u25cb":
                                                                    text_size 16
                                                                    text_color "#444444"
                                                                    text_hover_color "#c9a96e"
                                                                    action SetScreenVariable("bg_alloc", new_ba)
                                                            else:
                                                                text "\u25cb" size 16 color "#444444"

                        null height 15

                        if all_spent:
                            $ next_result = {"action": "next", "spheres": dict(sphere_alloc), "backgrounds": dict(bg_alloc)}
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 7. FREEBIES SCREEN (full mode)
################################################################################

screen chargen_freebies(state):
    modal True

    $ mode_config = state.config["modes"]["full"]
    $ freebie_total = mode_config.get("freebie_points", 15)
    $ freebie_costs = mode_config.get("freebie_costs", {})
    $ available_merits = state.config.get("merits", [])
    $ available_flaws = state.config.get("flaws", [])
    $ prev_data = state.data.get("freebies", {})

    default trait_adds = {}
    default selected_merits = []
    default selected_flaws = []
    python:
        if not trait_adds and not selected_merits and not selected_flaws:
            if prev_data:
                trait_adds = dict(prev_data.get("trait_additions", {}))
                selected_merits = list(prev_data.get("merits", []))
                selected_flaws = list(prev_data.get("flaws", []))

    # Calculate spent freebies
    $ merit_cost = sum(m.get("cost", m.get("value", 0)) for m in selected_merits)
    $ flaw_refund = sum(abs(f.get("cost", f.get("value", 0))) for f in selected_flaws)
    $ trait_cost = 0
    python:
        trait_cost = 0
        for tname, dots in trait_adds.items():
            cat_name = state.schema.trait_lookup.get(tname, "")
            cat = state.schema.categories.get(cat_name)
            if cat_name == "attributes":
                trait_cost += dots * freebie_costs.get("attribute", 5)
            elif cat_name == "abilities":
                trait_cost += dots * freebie_costs.get("ability", 2)
            elif cat_name == "spheres":
                trait_cost += dots * freebie_costs.get("sphere", 7)
            elif cat_name == "backgrounds":
                trait_cost += dots * freebie_costs.get("background", 1)

    $ total_spent = trait_cost + merit_cost
    $ total_budget = freebie_total + flaw_refund
    $ remaining = total_budget - total_spent

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=True, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Freebie Points" size 28 color "#c9a96e"
                        $ budget_text = str(remaining) + " / " + str(total_budget)
                        text "Remaining: [budget_text]" size 16 color "#6a9ec9"
                        if flaw_refund > 0:
                            $ flaw_text = str(flaw_refund)
                            text "(Includes [flaw_text] from Flaws)" size 12 color "#888888"

                        null height 10

                        # Merit picker
                        text "Merits" size 20 color "#c9a96e"
                        frame:
                            xfill True
                            background "#222238"
                            padding (15, 10, 15, 10)
                            vbox:
                                spacing 5
                                for merit in available_merits:
                                    $ m_name = merit["name"]
                                    $ m_cost = merit.get("cost", 0)
                                    $ m_desc = merit.get("description", "")
                                    $ is_selected = any(sm["name"] == m_name for sm in selected_merits)
                                    if is_selected:
                                        $ new_merits = [sm for sm in selected_merits if sm["name"] != m_name]
                                        textbutton "[m_name] (Cost: [m_cost]) - [m_desc]":
                                            text_size 13
                                            text_color "#c9a96e"
                                            action SetScreenVariable("selected_merits", new_merits)
                                    else:
                                        if remaining >= m_cost:
                                            $ new_merit_entry = {"name": m_name, "type": "merit", "cost": m_cost, "value": m_cost}
                                            $ new_merits = list(selected_merits) + [new_merit_entry]
                                            textbutton "[m_name] (Cost: [m_cost]) - [m_desc]":
                                                text_size 13
                                                text_color "#888888"
                                                text_hover_color "#ffffff"
                                                action SetScreenVariable("selected_merits", new_merits)
                                        else:
                                            textbutton "[m_name] (Cost: [m_cost]) - [m_desc]":
                                                text_size 13
                                                text_color "#555555"
                                                sensitive False

                        null height 10

                        # Flaw picker
                        text "Flaws" size 20 color "#c9a96e"
                        frame:
                            xfill True
                            background "#222238"
                            padding (15, 10, 15, 10)
                            vbox:
                                spacing 5
                                for flaw in available_flaws:
                                    $ f_name = flaw["name"]
                                    $ f_cost = flaw.get("cost", 0)
                                    $ f_refund = abs(f_cost)
                                    $ f_desc = flaw.get("description", "")
                                    $ is_selected = any(sf["name"] == f_name for sf in selected_flaws)
                                    if is_selected:
                                        $ new_flaws = [sf for sf in selected_flaws if sf["name"] != f_name]
                                        textbutton "[f_name] (Refund: +[f_refund]) - [f_desc]":
                                            text_size 13
                                            text_color "#8b4545"
                                            action SetScreenVariable("selected_flaws", new_flaws)
                                    else:
                                        $ new_flaw_entry = {"name": f_name, "type": "flaw", "cost": f_cost, "value": f_cost}
                                        $ new_flaws = list(selected_flaws) + [new_flaw_entry]
                                        textbutton "[f_name] (Refund: +[f_refund]) - [f_desc]":
                                            text_size 13
                                            text_color "#888888"
                                            text_hover_color "#ffffff"
                                            action SetScreenVariable("selected_flaws", new_flaws)

                        null height 15

                        if remaining >= 0:
                            $ next_result = {"action": "next", "trait_additions": dict(trait_adds), "merits": list(selected_merits), "flaws": list(selected_flaws)}
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "You have overspent your freebie points!" size 14 color "#ff4444" bold True xalign 0.5


################################################################################
## 8. REVIEW SCREEN (all modes)
################################################################################

screen chargen_review(state):
    modal True

    $ identity = state.data.get("identity", {})
    $ char_name = identity.get("name", "Unknown")
    $ tradition = identity.get("tradition", "")
    $ essence = identity.get("essence", "")
    $ nature = identity.get("nature", "")
    $ demeanor = identity.get("demeanor", "")

    # Gather trait data depending on mode
    $ attr_data = state.data.get("attribute_allocate", state.data.get("attributes", {}))
    $ abil_data = state.data.get("ability_allocate", state.data.get("abilities", {}))
    $ sb_data = state.data.get("spheres_backgrounds", state.data.get("spheres", {}))
    $ freebie_data = state.data.get("freebies", {})
    $ template_data = state.data.get("template_pick", {})

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=False, can_back=True, show_confirm=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 12
                        xfill True

                        text "Character Review" size 28 color "#c9a96e"
                        null height 5

                        # Identity section
                        text "Identity" size 20 color "#c9a96e"
                        text "Name: [char_name]" size 14 color "#e0e0e0"
                        if len(tradition) > 0:
                            text "Tradition: [tradition]" size 14 color "#e0e0e0"
                        if len(essence) > 0:
                            text "Essence: [essence]" size 14 color "#e0e0e0"
                        if len(nature) > 0:
                            text "Nature: [nature] / Demeanor: [demeanor]" size 14 color "#e0e0e0"

                        if template_data:
                            $ tmpl_name = template_data.get("template_file", "")
                            text "Template: [tmpl_name]" size 14 color "#e0e0e0"

                        null height 10

                        # Attributes
                        if attr_data:
                            text "Attributes" size 20 color "#c9a96e"
                            $ attr_cat = state.schema.categories.get("attributes")
                            if attr_cat is not None and attr_cat.groups is not None:
                                for gname, traits in attr_cat.groups.items():
                                    $ grp_label = gname.capitalize()
                                    text "[grp_label]" size 14 color "#888888" italic True
                                    for trait_name in traits:
                                        $ val = attr_data.get(trait_name, 1)
                                        hbox:
                                            spacing 5
                                            text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                            hbox:
                                                spacing 3
                                                for d in range(5):
                                                    if d < val:
                                                        text "\u25cf" size 14 color "#c9a96e"
                                                    else:
                                                        text "\u25cb" size 14 color "#444444"

                        null height 5

                        # Abilities
                        if abil_data:
                            text "Abilities" size 20 color "#c9a96e"
                            for trait_name, val in abil_data.items():
                                if val > 0:
                                    hbox:
                                        spacing 5
                                        text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                        hbox:
                                            spacing 3
                                            for d in range(5):
                                                if d < val:
                                                    text "\u25cf" size 14 color "#c9a96e"
                                                else:
                                                    text "\u25cb" size 14 color "#444444"

                        null height 5

                        # Spheres
                        $ sphere_data = {}
                        python:
                            if isinstance(sb_data, dict):
                                sphere_data = sb_data.get("spheres", sb_data)

                        if sphere_data:
                            text "Spheres" size 20 color "#c9a96e"
                            for trait_name, val in sphere_data.items():
                                if val > 0:
                                    hbox:
                                        spacing 5
                                        text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                        hbox:
                                            spacing 3
                                            for d in range(5):
                                                if d < val:
                                                    text "\u25cf" size 14 color "#c9a96e"
                                                else:
                                                    text "\u25cb" size 14 color "#444444"

                        # Backgrounds
                        $ bg_data = {}
                        python:
                            if isinstance(sb_data, dict):
                                bg_data = sb_data.get("backgrounds", {})

                        if bg_data:
                            text "Backgrounds" size 20 color "#c9a96e"
                            for trait_name, val in bg_data.items():
                                if val > 0:
                                    hbox:
                                        spacing 5
                                        text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                        hbox:
                                            spacing 3
                                            for d in range(5):
                                                if d < val:
                                                    text "\u25cf" size 14 color "#c9a96e"
                                                else:
                                                    text "\u25cb" size 14 color "#444444"

                        # Merits & Flaws
                        $ review_merits = freebie_data.get("merits", [])
                        $ review_flaws = freebie_data.get("flaws", [])
                        if review_merits or review_flaws:
                            null height 5
                            text "Merits & Flaws" size 20 color "#c9a96e"
                            for mf in review_merits:
                                $ mf_name = mf.get("name", "")
                                text "  + [mf_name] (Merit)" size 14 color "#6a9e6a"
                            for mf in review_flaws:
                                $ mf_name = mf.get("name", "")
                                text "  - [mf_name] (Flaw)" size 14 color "#8b4545"

                        null height 20

                        # Go-back-to-step buttons
                        text "Edit Steps:" size 16 color "#888888"
                        hbox:
                            spacing 10
                            box_wrap True
                            for i, sname in enumerate(state.steps):
                                if i < len(state.steps) - 1:
                                    $ step_label = sname.replace("_", " ").title()
                                    textbutton "[step_label]":
                                        text_size 13
                                        text_color "#6a9ec9"
                                        text_hover_color "#ffffff"
                                        action Return({"action": "goto", "step": i})

                        null height 15

                        textbutton "Confirm Character":
                            text_size 20
                            text_color "#6a9e6a"
                            text_hover_color "#88cc88"
                            xalign 0.5
                            action Return({"action": "confirm"})


################################################################################
## 9. SIMPLIFIED: ATTRIBUTES SCREEN (flat allocation)
################################################################################

screen chargen_attributes(state):
    modal True

    $ attr_cat = state.schema.categories.get("attributes")
    $ mode_config = state.config["modes"]["simplified"]
    $ attr_budget = mode_config.get("attribute_dots", 15)
    $ prev_alloc = state.data.get("attributes", {})

    default alloc = {}
    python:
        if not alloc:
            if prev_alloc:
                alloc = dict(prev_alloc)
            else:
                if attr_cat is not None:
                    for tn in attr_cat.trait_names:
                        alloc[tn] = attr_cat.default

    $ total_spent = sum(alloc.get(tn, 1) - 1 for tn in (attr_cat.trait_names if attr_cat else []))
    $ remaining = attr_budget - total_spent
    $ all_spent = (remaining == 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Attributes (Simplified)" size 28 color "#c9a96e"
                        text "Allocate [attr_budget] dots across all attributes. Each starts at 1." size 14 color "#aaaaaa"
                        text "Remaining: [remaining]" size 16 color "#6a9ec9"

                        null height 10

                        if attr_cat is not None and attr_cat.groups is not None:
                            for gname, traits in attr_cat.groups.items():
                                $ grp_label = gname.capitalize()
                                frame:
                                    xfill True
                                    background "#222238"
                                    padding (15, 10, 15, 10)
                                    vbox:
                                        spacing 5
                                        text "[grp_label]" size 18 color "#c9a96e"

                                        for trait_name in traits:
                                            $ cur_val = alloc.get(trait_name, 1)
                                            hbox:
                                                spacing 8
                                                text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                                hbox:
                                                    spacing 3
                                                    for d in range(5):
                                                        $ dot_num = d + 1
                                                        if dot_num <= cur_val:
                                                            if dot_num > 1:
                                                                $ new_alloc = dict(alloc)
                                                                $ new_alloc[trait_name] = dot_num - 1
                                                                textbutton "\u25cf":
                                                                    text_size 16
                                                                    text_color "#c9a96e"
                                                                    text_hover_color "#ff8888"
                                                                    action SetScreenVariable("alloc", new_alloc)
                                                            else:
                                                                text "\u25cf" size 16 color "#c9a96e"
                                                        else:
                                                            $ delta_needed = dot_num - cur_val
                                                            $ can_add = (remaining >= delta_needed) and (dot_num <= 5)
                                                            if can_add:
                                                                $ new_alloc = dict(alloc)
                                                                $ new_alloc[trait_name] = dot_num
                                                                textbutton "\u25cb":
                                                                    text_size 16
                                                                    text_color "#444444"
                                                                    text_hover_color "#c9a96e"
                                                                    action SetScreenVariable("alloc", new_alloc)
                                                            else:
                                                                text "\u25cb" size 16 color "#444444"

                                null height 5

                        null height 15

                        if all_spent:
                            $ next_result = dict(alloc)
                            $ next_result["action"] = "next"
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 10. SIMPLIFIED: ABILITIES SCREEN (flat allocation)
################################################################################

screen chargen_abilities(state):
    modal True

    $ abil_cat = state.schema.categories.get("abilities")
    $ mode_config = state.config["modes"]["simplified"]
    $ abil_budget = mode_config.get("ability_dots", 27)
    $ prev_alloc = state.data.get("abilities", {})

    default alloc = {}
    python:
        if not alloc:
            if prev_alloc:
                alloc = dict(prev_alloc)
            else:
                if abil_cat is not None:
                    for tn in abil_cat.trait_names:
                        alloc[tn] = 0

    $ total_spent = sum(alloc.values())
    $ remaining = abil_budget - total_spent
    $ all_spent = (remaining == 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Abilities (Simplified)" size 28 color "#c9a96e"
                        text "Allocate [abil_budget] dots across all abilities." size 14 color "#aaaaaa"
                        text "Remaining: [remaining]" size 16 color "#6a9ec9"

                        null height 10

                        if abil_cat is not None and abil_cat.groups is not None:
                            for gname, traits in abil_cat.groups.items():
                                $ grp_label = gname.capitalize()
                                frame:
                                    xfill True
                                    background "#222238"
                                    padding (15, 10, 15, 10)
                                    vbox:
                                        spacing 5
                                        text "[grp_label]" size 18 color "#c9a96e"

                                        for trait_name in traits:
                                            $ cur_val = alloc.get(trait_name, 0)
                                            hbox:
                                                spacing 8
                                                text "[trait_name]" size 14 color "#e0e0e0" min_width 180
                                                hbox:
                                                    spacing 3
                                                    for d in range(5):
                                                        $ dot_num = d + 1
                                                        if dot_num <= cur_val:
                                                            $ new_alloc = dict(alloc)
                                                            $ new_alloc[trait_name] = dot_num - 1
                                                            textbutton "\u25cf":
                                                                text_size 16
                                                                text_color "#c9a96e"
                                                                text_hover_color "#ff8888"
                                                                action SetScreenVariable("alloc", new_alloc)
                                                        else:
                                                            $ delta_needed = dot_num - cur_val
                                                            $ can_add = (remaining >= delta_needed) and (dot_num <= 3)
                                                            if can_add:
                                                                $ new_alloc = dict(alloc)
                                                                $ new_alloc[trait_name] = dot_num
                                                                textbutton "\u25cb":
                                                                    text_size 16
                                                                    text_color "#444444"
                                                                    text_hover_color "#c9a96e"
                                                                    action SetScreenVariable("alloc", new_alloc)
                                                            else:
                                                                text "\u25cb" size 16 color "#444444"

                                null height 5

                        null height 15

                        if all_spent:
                            $ next_result = dict(alloc)
                            $ next_result["action"] = "next"
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 11. SIMPLIFIED: SPHERES SCREEN
################################################################################

screen chargen_spheres(state):
    modal True

    $ sphere_cat = state.schema.categories.get("spheres")
    $ mode_config = state.config["modes"]["simplified"]
    $ sphere_budget = mode_config.get("sphere_dots", 6)
    $ starting_arete = mode_config.get("starting_arete", 1)
    $ prev_alloc = state.data.get("spheres", {})

    # Determine affinity sphere from tradition
    $ affinity_sphere = ""
    python:
        identity = state.data.get("identity", {})
        trad_name = identity.get("tradition", "")
        for t in state.get_traditions():
            if t["name"] == trad_name or t["id"] == trad_name:
                affinity_sphere = t.get("affinity_sphere", "")
                break

    default alloc = {}
    python:
        if not alloc:
            if prev_alloc:
                alloc = dict(prev_alloc)
            else:
                if sphere_cat is not None:
                    for tn in sphere_cat.trait_names:
                        alloc[tn] = 0

    $ total_spent = sum(alloc.values())
    $ remaining = sphere_budget - total_spent
    $ all_spent = (remaining == 0)

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=all_spent, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Spheres (Simplified)" size 28 color "#c9a96e"
                        text "Allocate [sphere_budget] dots. No sphere can exceed Arete ([starting_arete])." size 14 color "#aaaaaa"
                        text "Remaining: [remaining]" size 16 color "#6a9ec9"
                        if len(affinity_sphere) > 0:
                            text "Affinity Sphere: [affinity_sphere]" size 14 color "#6a9ec9"

                        null height 10

                        frame:
                            xfill True
                            background "#222238"
                            padding (15, 15, 15, 15)
                            vbox:
                                spacing 8

                                if sphere_cat is not None:
                                    for trait_name in sphere_cat.trait_names:
                                        $ cur_val = alloc.get(trait_name, 0)
                                        $ is_affinity = (trait_name == affinity_sphere)
                                        $ name_color = "#6a9ec9" if is_affinity else "#e0e0e0"
                                        hbox:
                                            spacing 8
                                            text "[trait_name]" size 14 color name_color min_width 180
                                            hbox:
                                                spacing 3
                                                for d in range(5):
                                                    $ dot_num = d + 1
                                                    if dot_num <= cur_val:
                                                        $ new_alloc = dict(alloc)
                                                        $ new_alloc[trait_name] = dot_num - 1
                                                        textbutton "\u25cf":
                                                            text_size 16
                                                            text_color "#c9a96e"
                                                            text_hover_color "#ff8888"
                                                            action SetScreenVariable("alloc", new_alloc)
                                                    else:
                                                        $ delta_needed = dot_num - cur_val
                                                        $ can_add = (remaining >= delta_needed) and (dot_num <= starting_arete)
                                                        if can_add:
                                                            $ new_alloc = dict(alloc)
                                                            $ new_alloc[trait_name] = dot_num
                                                            textbutton "\u25cb":
                                                                text_size 16
                                                                text_color "#444444"
                                                                text_hover_color "#c9a96e"
                                                                action SetScreenVariable("alloc", new_alloc)
                                                        else:
                                                            text "\u25cb" size 16 color "#444444"

                        null height 15

                        if all_spent:
                            $ next_result = {"action": "next", "spheres": dict(alloc), "backgrounds": {}}
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
                        else:
                            text "Allocate all remaining dots before proceeding." size 14 color "#884444" italic True xalign 0.5


################################################################################
## 12. TEMPLATE PICK SCREEN (template mode)
################################################################################

screen chargen_template_pick(state):
    modal True

    $ traditions = state.get_traditions()
    $ prev_data = state.data.get("template_pick", {})

    default selected_tradition_id = prev_data.get("tradition", "")
    default selected_template_file = prev_data.get("template_file", "")

    # Get templates for selected tradition
    $ templates_list = []
    python:
        templates_list = []
        for t in traditions:
            if t["id"] == selected_tradition_id:
                templates_list = t.get("templates", [])
                break

    $ has_selection = len(selected_template_file) > 0

    frame:
        xfill True
        yfill True
        background "#1a1a2e"

        vbox:
            spacing 0

            use chargen_nav(state, can_next=has_selection, can_back=True)

            frame:
                xfill True
                yfill True
                background "#1a1a2eFF"
                padding (40, 20, 40, 20)

                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    xfill True
                    yfill True

                    vbox:
                        spacing 15
                        xfill True

                        text "Choose a Template" size 28 color "#c9a96e"
                        text "Select a Tradition, then pick a character template." size 14 color "#aaaaaa"

                        null height 10

                        # Tradition picker
                        text "Tradition:" size 18 color "#c9a96e"
                        frame:
                            xfill True
                            background "#222238"
                            padding (10, 10, 10, 10)
                            vbox:
                                spacing 5
                                for trad in traditions:
                                    $ trad_id = trad["id"]
                                    $ trad_name = trad["name"]
                                    $ trad_color = "#c9a96e" if selected_tradition_id == trad_id else "#888888"
                                    $ trad_templates = trad.get("templates", [])
                                    $ tmpl_count = len(trad_templates)
                                    textbutton "[trad_name] ([tmpl_count] templates)":
                                        text_size 14
                                        text_color trad_color
                                        text_hover_color "#ffffff"
                                        action [SetScreenVariable("selected_tradition_id", trad_id), SetScreenVariable("selected_template_file", "")]

                        null height 15

                        # Template picker (only if tradition is selected)
                        if len(selected_tradition_id) > 0:
                            text "Available Templates:" size 18 color "#c9a96e"
                            if templates_list:
                                frame:
                                    xfill True
                                    background "#222238"
                                    padding (15, 15, 15, 15)
                                    vbox:
                                        spacing 10
                                        for tmpl in templates_list:
                                            $ tmpl_name = tmpl.get("name", "Unknown")
                                            $ tmpl_desc = tmpl.get("description", "")
                                            $ tmpl_file = tmpl.get("file", "")
                                            $ tmpl_selected = (selected_template_file == tmpl_file)
                                            $ tmpl_color = "#c9a96e" if tmpl_selected else "#888888"

                                            vbox:
                                                spacing 2
                                                textbutton "[tmpl_name]":
                                                    text_size 16
                                                    text_color tmpl_color
                                                    text_hover_color "#ffffff"
                                                    action SetScreenVariable("selected_template_file", tmpl_file)
                                                text "  [tmpl_desc]" size 12 color "#aaaaaa"
                            else:
                                text "No templates available for this Tradition yet." size 14 color "#884444" italic True

                        null height 15

                        if has_selection:
                            $ next_result = {"action": "next", "tradition": selected_tradition_id, "template_file": selected_template_file}
                            textbutton "Next Step >>" text_size 18 text_color "#c9a96e" text_hover_color "#e0c080" action Return(next_result) xalign 0.5
