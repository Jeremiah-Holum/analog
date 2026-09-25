"""Every spoken line in THE THIRD FLOOR. id -> (style, text)."""

VO = {
    # TAPE 1 - security desk
    "D01": ("dale", "Testing... okay."),
    "D02": ("dale", "Uh, this is Dale Kessler, night security at Brenner Mutual. It's November third... about two in the morning."),
    "D03": ("dale", "Mister Pruitt asked me to get the lights on three on tape. For the electrician."),
    "D04": ("dale", "So... let's go see the lights."),
    # elevator / walk
    "E01": ("dale", "Third floor."),
    "E02": ("dale", "See? It's already doing it."),
    "W01": ("dale", "Every night, right around two, the whole floor starts doing this."),
    "W02": ("dale", "Maintenance came out twice. They say the ballasts are fine... the wiring's fine."),
    "W03": ("dale_q", "It's not fine."),
    "C00": ("dale", "Okay. Doors. For the record."),
    # end of hall
    "X01": ("dale", "And this one."),
    "X02": ("dale", "This one isn't on the floor plan. I checked the binder at the desk. Nine offices on three."),
    "X03": ("dale", "This would be ten."),
    "X04": ("dale_q", "...Hello?"),
    "X05": ("dale_q", "Building's closed. Is... is somebody in there?"),
    # TAPE 2
    "S01": ("dale", "November seventh."),
    "S02": ("dale", "Pruitt says there's no tenth door. He says I can't count."),
    "S03": ("dale", "So. I'm counting."),
    "S04": ("dale_q", "That's not right... this hall isn't this long."),
    "F01": ("dale_q", "Hey."),
    "F02": ("dale", "Hey! Hey! This floor's closed! You can't be up here!"),
    "F03": ("dale_q", "Where'd he go?"),
    # TAPE 4 - desk
    "P01": ("dale_q", "November ninth."),
    "P02": ("dale_q", "I called Pruitt. About the man. He asked me what number I got to."),
    "P03": ("dale_q", "I said fourteen. And he didn't say anything for a long time."),
    "P04": ("dale_q", "Then he said... don't go back up, Dale."),
    "P05": ("dale_q", "He wasn't in today. Nobody answers at his house."),
    "P06": ("dale_q", "And the camera on three has been showing that door open since midnight."),
    "P07": ("dale_q", "It's my job. I have to go look."),
    # TAPE 4 - upstairs
    "G01": ("dale_q", "It's open."),
    "G02": ("dale_q", "It's all the way open."),
    "G03": ("dale_q", "Okay. Okay... I'm just gonna look."),
    "O01": ("dale_w", "There's a whole office back here."),
    "O02": ("dale_w", "There's a TV on."),
    "V01": ("dale_w", "That's the hallway."),
    "V02": ("dale_w", "That's the door I just came through. That's..."),
    # facilities memo (read aloud over the document)
    "M01": ("memo", "Brenner Mutual Insurance. Facilities notice, seventy one, dash one seventeen."),
    "M02": ("memo", "Effective immediately, the third floor is closed."),
    "M03": ("memo", "The third floor contains nine offices."),
    "M04": ("memo", "If you count more than nine, do not continue. Return to the elevator. Do not run."),
    "M05": ("memo", "Do not knock on any door that is not numbered."),
    "M06": ("memo", "If something knocks, do not answer."),
    "M07": ("memo", "Do not look at the end of the hall for longer than necessary."),
}

NUMBER_WORDS = {1: "oh one", 2: "oh two", 3: "oh three", 4: "oh four", 5: "oh five", 6: "oh six", 7: "oh seven",
                8: "oh eight", 9: "oh nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen"}
for i, w in NUMBER_WORDS.items():
    VO[f"N{i:02d}"] = ("dale" if i < 10 else "dale_q", f"Three {w}.")

# Chatterbox delivery per style: (reference voice, exaggeration, cfg_weight, temperature)
DELIVERY = {
    "dale":   ("dale", 0.55, 0.5, 0.8),
    "dale_q": ("dale", 0.7, 0.4, 0.8),
    "dale_w": ("dale", 0.85, 0.3, 0.8),
    "memo":   ("memo", 0.3, 0.6, 0.6),
}
# per-line overrides of exaggeration
EXAGGERATE = {"F02": 1.1, "F01": 0.9, "W03": 0.8, "X05": 0.85, "V02": 1.0, "S04": 0.9}
