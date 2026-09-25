"""Every spoken line in THE THIRD FLOOR. id -> (style, text)."""

VO = {
    # TAPE 1 - security desk
    "D01": ("dale", "Testing... uh, okay. Okay."),
    "D02": ("dale", "Uh, this is Dale... Dale Kessler, night security at, uh, Brenner Mutual. It's November third... about two in the morning."),
    "D03": ("dale", "Mister Pruitt asked me to, um, get the lights on three on tape. For the electrician."),
    "D04": ("dale", "So... let's go see the lights."),
    # elevator / walk
    "E01": ("dale", "Third floor."),
    "E02": ("dale", "See? See, it's already doing it."),
    "W01": ("dale", "Every night, right around two, the whole... the whole floor starts doing this."),
    "W02": ("dale", "Maintenance came out twice. They say the, uh, the ballasts are fine... the wiring's fine."),
    "W03": ("dale_q", "It's not fine."),
    "C00": ("dale", "Okay. Uh, doors. For the record."),
    # end of hall
    "X01": ("dale", "And, uh... this one."),
    "X02": ("dale", "This one isn't on the... on the floor plan. I checked the binder at the desk. Nine offices on three."),
    "X03": ("dale", "This would be... ten."),
    "X04": ("dale_q", "...Hello?"),
    "X05": ("dale_q", "Building's closed. Is, is somebody in there?"),
    # TAPE 2
    "S01": ("dale", "November seventh."),
    "S02": ("dale", "Pruitt says there's no tenth door. He says I, I can't count."),
    "S03": ("dale", "So. I'm counting."),
    "S04": ("dale_q", "That's not... that's not right. This hall isn't this long."),
    "F01": ("dale_q", "Hey."),
    "F02": ("dale_yell", "Hey! Hey! This floor's closed! You, you can't be up here!"),
    "F03": ("dale_q", "Where'd... where'd he go?"),
    # TAPE 4 - desk
    "P01": ("dale_q", "November ninth."),
    "P02": ("dale_q", "I, uh, I called Pruitt. About the... about the man. He asked me what number I got to."),
    "P03": ("dale_q", "I said fourteen. And he didn't... he didn't say anything for a long time."),
    "P04": ("dale_q", "Then he said... don't go back up, Dale."),
    "P05": ("dale_q", "He wasn't in today. Nobody... nobody answers at his house."),
    "P06": ("dale_q", "And the camera on three has been showing that door open since, uh, since midnight."),
    "P07": ("dale_q", "It's my job. I have to... I have to go look."),
    # TAPE 4 - upstairs
    "G01": ("dale_q", "It's open."),
    "G02": ("dale_q", "It's, it's all the way open."),
    "G03": ("dale_q", "Okay. Okay... I'm just... I'm just gonna look."),
    "O01": ("dale_w", "There's a whole... office back here."),
    "O02": ("dale_w", "There's a... there's a TV on."),
    "V01": ("dale_w", "That's the hallway."),
    "V02": ("dale_w", "That's the door I just... I just came through. That's..."),
    # facilities memo (read aloud over the document)
    "M01": ("memo", "Brenner Mutual Insurance. Facilities notice, seventy one, dash one seventeen."),
    "M02": ("memo", "Effective immediately, the third floor is closed."),
    "M03": ("memo", "The third floor contains nine offices."),
    "M04": ("memo", "If you count more than nine, do not continue. Return to the elevator. Do not run."),
    "M05": ("memo", "Do not knock on any door that is not numbered."),
    "M06": ("memo", "If something knocks, do not answer."),
    "M07": ("memo", "Do not look at the end of the hall for longer than necessary."),
}

# Door counts: one continuous take per tape, cut into one clip per number (A01.., B01..).
# (style, clip prefix, door numbers, text)
COUNTS = {
    "COUNT1": ("dale", "A", list(range(301, 310)),
               "Three oh one… three oh two… three oh three… three oh four… three oh five… "
               "three oh six… three oh seven… three oh eight… three oh nine."),
    "COUNT2": ("dale_q", "B", list(range(301, 315)),
               "Three oh one… three oh two… three oh three… three oh four… three oh five… "
               "three oh six… three oh seven… three oh eight… three oh nine… three ten… "
               "three eleven… three twelve… three thirteen… three fourteen."),
}

# Chatterbox delivery per style: (reference voice, exaggeration, cfg_weight, temperature)
DELIVERY = {  # one reference for all of Dale, emotion kept low so voice and accent stay put
    "dale":      ("dale", 0.4, 0.5, 0.75),
    "dale_q":    ("dale", 0.45, 0.5, 0.75),
    "dale_w":    ("dale", 0.45, 0.5, 0.75),
    "dale_yell": ("dale_yell", 0.9, 0.35, 0.85),   # real shout, then voice-converted into Dale
    "memo":      ("memo", 0.3, 0.6, 0.6),
}
# loudness each style is levelled to (LUFS)
LOUDNESS = {"dale": -20, "dale_q": -21, "dale_w": -24, "dale_yell": -15, "memo": -20}
