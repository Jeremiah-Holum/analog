"""Every spoken line in ITEM 15 ("SPACE AVAILABLE"). id -> (style, text). A word ending in ~ is drawn out."""

VO = {
    # lobby, the old security desk
    "L01": ("gary", "Good morning! Gary Lindqvist, Coulee Commercial Realty."),
    "L02": ("gary", "And this is the Brenner Mutual building. Four floors, forty thousand square feet, and, folks, it is priced to move."),
    "L03": ("gary", "This was the, uh~, the old security desk. Monitors stay with the building, by the way."),
    "L04": ("gary", "Somebody left one on. Ha. Okay! Let's go up."),
    "L05": ("gary", "Built in sixty-eight. Brenner Mutual was here right up until ninety-four. Moved out kind of sudden, I heard."),
    # elevator
    "E01": ("gary_q", "Now, three is closed off right now. Some kind of electrical thing. So we'll start on two."),
    "E02": ("gary", "Here we go."),
    # second floor
    "T01": ("gary", "Two! Open plan, drop ceilings, great bones."),
    "T02": ("gary", "Plenty of natural... well~, plenty of light."),
    "T03": ("gary", "You could fit, oh, forty, fifty desks in here, easy."),
    "T04": ("gary", "Alright. Let's see the rest."),
    # the elevator stops on three anyway
    "E03": ("gary_q", "Huh. Went to three anyway."),
    "E04": ("gary", "Must be that electrical thing. Well~... while we're here!"),
    "C01": ("gary", "Private offices, all down this side. Let me count 'em for you."),
    "C02": ("gary", "Even more than the listing says!"),
    "C03": ("gary", "And down at the end, the corner office. This is the one you want."),
    # the corner office
    "O01": ("gary", "Big, big space back here."),
    "O02": ("gary", "Even comes with a TV! Ha."),
    "O03": ("gary_q", "Anyway~..."),
    "O04": ("gary", "Lots of potential. Lots of potential."),
    # walking back to the elevator
    "B01": ("gary", "Okay! Back to the elevator."),
    "B02": ("gary", "Twelve offices, folks. Twelve. I'm gonna have to update that listing."),
    "B03": ("gary_q", "Huh. Light's going out down there. I'll put that on the list."),
    # the tape keeps running, 2:11 AM
    "K01": ("gary_far", "Thirteen… fourteen… fifteen… sixteen… seventeen…"),
    # sign-off at the elevator
    "Z01": ("gary", "Okay, I'm just gonna set this down here... there we go."),
    "Z02": ("gary", "So that's the Brenner building. Gary Lindqvist, Coulee Commercial. Call me any time. Five five five, oh one four one."),
    "Z03": ("gary", "Going down!"),
}

# He counts the offices out loud like a salesman, one door at a time, several seconds apart.
_WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]
for _i, _w in enumerate(_WORDS, 1):
    VO[f"G{_i:02d}"] = ("gary", _w + ("!" if _i >= 10 else "."))
COUNTS = {}

DELIVERY = {  # (reference voice, exaggeration, cfg_weight, temperature)
    "gary":   ("gary", 0.55, 0.5, 0.75),
    "gary_q": ("gary", 0.45, 0.5, 0.75),
    "gary_far": ("gary", 0.4, 0.5, 0.75),
}
LOUDNESS = {"gary": -19, "gary_q": -21, "gary_far": -34}
