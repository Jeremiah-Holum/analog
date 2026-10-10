"""The edit of ITEM 20 ("COULEE AFTER DARK"). Built by film/build.py when FILM=item20:
    FILM=item20 python3 film/build.py
A viewer's off-air VHS recording of a live public-access broadcast. They paused the recorder now and then,
so the time in the LIVE tag jumps between parts."""
import build as B
from build import (Segment, bed, blue_frames, card_frames, seq_frames, static_frames, still_frames, steps,
                   flicker, gate_from_schedule, SERIF, FPS)
from item20.timing import SHOT_LEN, DENNY_COUNT, count_times
from item20 import graphics as G

T = lambda h, m, s=0: h * 3600 + m * 60 + s


def seq(shot, **kw):
    return seq_frames(shot, None, 0, n=SHOT_LEN[shot], **kw)


def still(sched, shake=0.9, seed=1, **kw):
    if isinstance(sched, str):
        name = sched
        sched = lambda t: (name, 1.0)
    return still_frames(sched, None, 0, shake=shake, seed=seed, human=True, **kw)


def pause(name, seed):
    """The viewer un-pauses the VCR: a short burst of picture break-up."""
    return Segment(name, 0.5, static_frames(seed), "clean", [(0, "static", 0.35)], damage=False)


def film():
    S = []
    add = S.append
    hall = bed(0.012, 0.014, 0.006)
    phone = bed(0.014, 0.012, 0.006)
    DENNY = ("DENNY SZABO", "LIVE FROM THE BRENNER BUILDING  ·  3RD FLOOR")

    add(Segment("00_play", 3.0, blue_frames("PLAY ▶", 0.9), "clean", [(0.1, "vcr", 0.8)], bed(0.006), damage=False))
    add(Segment("01_static", 0.8, static_frames(21), "clean", [(0, "static", 0.5)], damage=False))
    add(Segment("02_evidence", 15, card_frames([
        "COULEE COUNTY SHERIFF'S DEPARTMENT",
        "EVIDENCE  ITEM 20",
        "",
        "One (1) VHS cassette. Off-air recording of",
        "Coulee Community Access, Channel 10,",
        "October 31 - November 1, 1997.",
        "",
        "Mailed to the Sheriff's Department. No return address.",
    ], 19), "card", [], bed(0.01, drone="drone_low", drone_g=0.25)))
    add(Segment("03_static", 0.6, static_frames(22), "clean", [(0, "static", 0.5)], damage=False))
    add(Segment("04_label", 3.6, card_frames(["ITEM 20", "", "LABEL: \"AFTER DARK 10/31 - DENNY LIVE ON 3!!\""], 21,
                                             typed=False, align="center"), "card", [(0, "vcr", 0.5)], bed(0.01)))
    add(pause("05_rec", 23))
    # back from the break
    add(Segment("06_bumper", 6.5, G.bumper_frames(), "card", [(0.0, "bumper", 0.9)], bed(0.008), damage=True))

    # 1:44 AM: the elevator opens on three
    c = T(1, 44, 12)
    add(Segment("10_open", SHOT_LEN["n_open"] / FPS + 1.6, seq("n_open"), "tv",
                [(0.0, "ding", 0.5), (0.4, "elev_doors", 0.7), (0.6, "D01", 1.0)] + steps(5.0, 9.0, 1.6),
                hall, post=G.overlay(c, (*DENNY, 1.5, 8.5))))
    hs = flicker(201, 0.25, "n_hall_a", "n_hall_a")
    add(Segment("11_rule", 17, still(hs, 1.0, 2), "tv", [(1.2, "D02", 1.0), (11.0, "D03", 1.0)],
                hall, post=G.overlay(c + 9, callin=True)))

    # 1:51 AM: Paul Voss, Harold's son
    add(pause("12_pause", 24))
    c = T(1, 51, 40)
    def paul_s(t):     # the far lights drop out around "He got to ten." It's standing at the far end. Barely.
        if 27.0 <= t < 27.5 or 28.1 <= t < 29.4:
            return ("n_hall_b", 1.0)
        return ("n_hall_a", 1.0)
    add(Segment("13_paul", 43.5, still(paul_s, 0.8, 3), "tv",
                [(0.8, "D04", 1.0), (5.5, "I01", 1.0), (14.0, "D05", 1.0), (18.5, "I02", 1.0), (26.5, "I03", 1.0),
                 (31.0, "hangup", 0.5), (31.2, "dialtone", 0.12), (34.2, "D06", 1.0)],
                bed(0.012, 0.014, 0.006, buzz_gate=gate_from_schedule(paul_s, "n_hall_a")),
                post=G.overlay(c, ("ON THE LINE: PAUL", "LA CROSSE", 5.0, 30.5))))

    # 1:58 AM: the count
    add(pause("14_pause", 25))
    c = T(1, 58, 3)
    g = DENNY_COUNT
    hold = 3.5
    times = count_times()
    cues = [(0.4, "D07", 1.0)]
    for k, tt in enumerate(times):
        cues.append((hold + tt - 0.2, f"C{k + 1:02d}", 1.0))
        if k + 1 >= 5 and k + 1 != 10:          # something counting with him, half a beat ahead. He never notices.
            cues.append((hold + tt - 0.75, f"E{k + 1:02d}", 0.5 + 0.04 * (k - 4)))
    cues.append((hold + times[-1] + 1.6, "E15", 0.75))
    cues += [(hold + g["dur"] - 2.5, "D10", 1.0)] + steps(hold, hold + g["dur"] - 3.0, 1.7)
    add(Segment("15_count", hold + g["dur"] + 5.5, seq("n_count", hold_first=hold), "tv", cues, hall,
                post=G.overlay(c, callin=True)))

    # 2:04 AM: Gary
    add(pause("16_pause", 26))
    c = T(2, 4, 31)
    gs = flicker(204, 0.4, "n_gary_a", "n_gary_b", quiet=[(0, 4)])
    add(Segment("17_gary", 34, still(gs, 0.7, 4), "tv",
                [(0.6, "D11", 1.0), (4.5, "G01", 1.0), (11.0, "G02", 1.0), (18.0, "G03", 1.0),
                 (24.0, "line_knock", 0.9), (27.5, "D12", 1.0), (31.0, "hangup", 0.5)],
                bed(0.012, 0.01, 0.006, buzz_gate=gate_from_schedule(gs, "n_gary_a")),
                post=G.overlay(c, ("ON THE LINE: GARY", "555-0141", 4.0, 24.0))))

    # 2:08 AM: knocking from the corner office
    c = T(2, 8, 2)
    add(Segment("18_knock", 14, still(gs, 0.7, 5), "tv",
                [(0.8, "knock_guard", 0.6), (2.6, "D13", 1.0), (6.2, "knock_guard", 0.8), (8.0, "D14", 1.0)],
                bed(0.012, 0.01, 0.006, buzz_gate=gate_from_schedule(gs, "n_gary_a")), post=G.overlay(c)))
    add(Segment("19_approach", SHOT_LEN["n_approach"] / FPS, seq("n_approach"), "tv",
                [(7.4, "D15", 1.0)] + steps(1.2, 12.0, 1.5), bed(0.012, 0.004, 0.006, "drone_low", 0.12),
                post=G.overlay(c + 14)))

    # 2:10 AM: the door. The top light goes. In the red of the EXIT sign it is right there.
    c = T(2, 10, 31)
    def door_s(t):
        if t < 4.0:
            return ("n_door_lit", 1.0)
        if t < 5.2:
            return ("n_door_lit", 1.0) if int(t * 9) % 3 == 0 else ("n_door_dark", 1.5)
        if t < 6.4:
            return ("n_door_dark", 1.5)
        return ("n_door_fig", 1.6)
    add(Segment("20_door", 11.0, still(door_s, 0.6, 6), "tv",
                [(0.5, "knock_final", 0.9), (4.0, "drop", 0.25), (6.4, "stinger_big", 0.9), (7.6, "D16", 1.0)],
                bed(0.014, 0.0, 0.008, "drone_low", 0.2), glitches=[(10.3, 0.7, 1.0)], post=G.overlay(c)))

    # 2:11 AM
    add(Segment("21_standby", 9, G.standby_frames(), "card", [(0.0, "tone", 0.25)], bed(0.006), damage=True))
    add(Segment("22_bbs", 25, G.bbs_frames(), "card", [(0.0, "bbs", 0.35)], bed(0.006), damage=True))
    add(Segment("23_static", 1.2, static_frames(27), "clean", [(0, "static", 0.7)], damage=False))
    add(Segment("24_stop", 3.0, blue_frames("STOP ■", 0.3), "clean", [(0.2, "vcr_eject", 0.6)], bed(0.004), damage=False))

    def end_card(name, lines, dur):
        return Segment(name, dur, card_frames(lines, 21, typed=False, align="center", fade=1.0, dur=dur, fontpath=SERIF),
                       "card", [], bed(0.006, drone="drone_low", drone_g=0.25), damage=False)
    add(end_card("30_end1", ["Denny Szabo was found at 6:40 AM,", "sitting in the lobby of the Brenner Mutual building.",
                             "He was unhurt."], 8))
    add(end_card("31_end2", ["He has never said what happened on the third floor."], 6))
    add(end_card("32_end3", ["Channel 10's phone log shows no calls", "put through after 1:52 AM."], 7))
    add(end_card("33_end4", ["Coulee After Dark did not return."], 5))
    add(Segment("34_title", 5.0, card_frames(["COULEE AFTER DARK"], 30, typed=False, align="center", fade=1.2, dur=5.0,
                                             fontpath=SERIF), "card", [(0.0, "knock_final", 0.5)], bed(0.004), damage=False))
    return S
