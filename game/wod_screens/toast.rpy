## game/wod_screens/toast.rpy
## Brief notification overlay that fades in/out.

screen wod_toast(message, duration=2.0):
    zorder 300
    timer duration action Hide("wod_toast")

    frame:
        xalign 0.5
        yalign 0.1
        padding (20, 10, 20, 10)
        background "#1a1a2eDD"

        text message size 16 color "#c9a96e"

    on "show" action With(dissolve)
    on "hide" action With(dissolve)
