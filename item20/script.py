"""Every spoken line in ITEM 20 (COULEE AFTER DARK, Oct. 31 1997). id -> (style, text).
Voiced with Dia (film/voice_dia.py); (cues) in parentheses are performed, not spoken."""

VO = {
    # 1:44 AM, the elevator opens on three
    "D01": ("denny", "And we're back! (laughs) If you're just tuning in, I'm Denny Szabo, this is Coulee After Dark, "
                     "and we are live, on the air, from the third floor of the old Brenner Mutual building."),
    "D02": ("denny", "Now, you've heard the stories. Security guard goes missing in ninety-four. The real estate guy, "
                     "ninety-six. And there's a rule up here. One rule. Do not count the offices."),
    "D03": ("denny", "(laughs) So that's exactly what we're gonna do. Lines are open, folks. Five five five, oh one one oh."),
    # 1:51 AM, a caller
    "D04": ("denny", "Okay, we've got a caller. Marcy says, uh... Irene? Irene, you're on Coulee After Dark."),
    "I01": ("irene", "Is this... am I on? (clears throat) Young man. You need to get back in that elevator, and you need to go home."),
    "D05": ("denny", "(laughs) Ma'am, it's carpet and drop ceilings. It's an office."),
    "I02": ("irene", "My husband worked nights in that building. Nineteen sixty-eight. He counted, too."),
    "I03": ("irene", "He got to ten. ... Don't you get to ten."),
    "D06": ("denny", "Okay! Thank you, Irene. Spooky stuff. Uh, spooky stuff, folks."),
    # 1:58 AM, the count
    "D07": ("denny", "Alright. The count. Live, on the air. Here we go."),
    "C10": ("denny", "Three... three ten? Huh."),
    "D10": ("denny_q", "Marcy, how many did they... how many offices did they say? (sighs) Nine. They said nine."),
    # 2:04 AM, another caller
    "D11": ("denny_q", "We've, uh... we've got another caller. Go ahead, you're on the air."),
    "G01": ("gary_phone", "Hey, Denny! Gary Lindqvist, Coulee Commercial Realty. (laughs) Big fan of the show."),
    "G02": ("gary_phone", "Well, I see you found the rest of the offices. Fourteen! Lots of potential."),
    "G03": ("gary_phone", "Now, you're gonna want the corner office, Denny. Everybody does."),
    "D12": ("denny_q", "Marcy, who... who was that? Who put that through?"),
    # 2:08 AM, knocking from the end of the hall
    "D13": ("denny_q", "Okay. Did... did you guys hear that?"),
    "D14": ("denny_q", "It's coming from the end. The, uh... the corner office."),
    "D15": ("denny_q", "Hello? (laughs) Building's empty, folks. There's nobody up here but me."),
    "D16": ("denny_w", "...Fifteen."),
}
# the count: he reads the plaques
_N = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "", "eleven", "twelve", "thirteen", "fourteen"]
for _i, _w in enumerate(_N, 1):
    if _w:
        VO[f"C{_i:02d}"] = ("denny", f"Three oh {_w}." if _i < 10 else f"Three {_w}.")
COUNTS = {}

# Voices (voices/README.md). Denny is the take picked for "the next voice"; Gary is ITEM 15's Gary;
# Irene was auditioned from Dia seeds (film/dia_audition.py).
_PROMPT_TEXT = ("Okay, is it... yep. (clears throat) Good morning! Uh, Gary Lindqvist, Coulee Commercial Realty. "
                "And this is the Brenner Mutual building. Four floors, forty thousand square feet, and, uh... "
                "(laughs) folks, it's priced to move.")
DIA_PROMPTS = {
    "denny": ("voices/denny.wav", _PROMPT_TEXT), "denny_q": ("voices/denny.wav", _PROMPT_TEXT),
    "denny_w": ("voices/denny.wav", _PROMPT_TEXT),
    "gary_phone": ("voices/gary.wav", _PROMPT_TEXT),
    "irene": ("voices/irene.wav", VO["I01"][1]),
}
DIA_PROMPT = DIA_PROMPTS["denny"]
DIA_USE_PROMPT = "I01"     # Irene's first line is her audition take
DIA_GROUPS = {
    "COUNT_A": ["C01", "C02", "C03", "C04"],
    "COUNT_B": ["C05", "C06", "C07", "C08", "C09"],
    "COUNT_C": ["C11", "C12", "C13", "C14"],
}
DELIVERY = {}
# on-camera mic for Denny; callers come down a phone line into the broadcast
LOUDNESS = {"denny": -19, "denny_q": -21, "denny_w": -25, "gary_phone": -22, "irene": -22}
