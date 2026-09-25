"""The edit of ITEM 15 ("SPACE AVAILABLE"). Built by film/build.py when FILM=item15:
    FILM=item15 python3 film/build.py"""
import build as B
from build import (Segment, bed, blue_frames, card_frames, seq_frames, static_frames, still_frames, steps,
                   flicker, gate_from_schedule, SERIF, FPS)
from timing import count_walk
from item15.timing import SHOT_LEN, GARY_COUNT

DATE = "MAR. 14 1996"
T0 = 10 * 3600 + 12 * 60 + 5            # 10:12:05 AM


def seq(shot, clock, **kw):
    return seq_frames(shot, DATE, T0 + clock, n=SHOT_LEN[shot], **kw)


def still(name, clock, shake=0.9, seed=1, **kw):
    return still_frames(lambda t: (name, 1.0), DATE, T0 + clock, shake=shake, seed=seed, **kw)


def film():
    S = []
    add = S.append
    cut_in = [(0, 0.3, 0.8)]
    room = bed(0.012, 0.004, 0.008)
    hall = bed(0.012, 0.014, 0.006)

    add(Segment("00_play", 3.5, blue_frames("PLAY ▶", 0.9), "clean", [(0.1, "vcr", 0.8)], bed(0.006), damage=False))
    add(Segment("01_static", 0.8, static_frames(11), "clean", [(0, "static", 0.5)], damage=False))
    add(Segment("02_evidence", 15, card_frames([
        "COULEE COUNTY SHERIFF'S DEPARTMENT",
        "EVIDENCE  ITEM 15",
        "",
        "One (1) VHS cassette recovered from the offices",
        "of Coulee Commercial Realty on April 2, 1996.",
        "",
        "Found in a desk drawer labeled",
        "\"BRENNER - DO NOT SHOW\".",
    ], 20), "card", [], bed(0.01, drone="drone_low", drone_g=0.25)))
    add(Segment("03_static", 0.6, static_frames(12), "clean", [(0, "static", 0.5)], damage=False))
    add(Segment("04_label", 3.6, card_frames(["ITEM 15", "", "LABEL: \"BRENNER BLDG - WALKTHRU - 3/96\""], 22,
                                             typed=False, align="center"), "card", [(0, "vcr", 0.5)], bed(0.01)))

    # lobby
    add(Segment("10_lobby", 30, still("g_lobby", 0, 0.9, 2, play=True), "cam",
                [(1.0, "L01", 1.0), (4.0, "L02", 1.0), (11.5, "L05", 1.0), (19.5, "L03", 1.0), (25.5, "L04", 1.0)],
                room, glitches=[(0, 0.5, 1.0)]))
    # elevator panel
    add(Segment("11_panel", 8, still("g_panel", 26, 0.8, 3), "cam", [(0.6, "E01", 1.0)],
                bed(0.012, 0.0, 0.012, "drone_low", 0.08), glitches=cut_in))
    # second floor
    add(Segment("12_two", SHOT_LEN["g_open2"] / FPS, seq("g_open2", 36), "cam",
                [(0.1, "E02", 1.0), (0.5, "ding", 0.6), (0.8, "elev_doors", 0.7), (4.0, "T01", 1.0),
                 (8.0, "T02", 1.0), (12.0, "T03", 1.0), (16.5, "T04", 1.0)] + steps(3.4, 8.0, 1.6),
                bed(0.012, 0.016, 0.006), glitches=cut_in))
    # it stops on three anyway
    add(Segment("13_three", 9.5, seq("g_open3", 61), "cam",
                [(0.2, "ding", 0.6), (0.8, "elev_doors", 0.7), (2.4, "E03", 1.0), (4.6, "E04", 1.0)],
                hall, glitches=cut_in))
    # the count
    g = GARY_COUNT
    hold = 4.2
    times = count_walk(g["n"], g["y0"], g["speed"])
    add(Segment("14_count", hold + g["dur"], seq("g_count", 72, hold_first=hold), "cam",
                [(0.3, "C01", 1.0)] + [(hold + t - 0.25, f"G{k + 1:02d}", 1.0) for k, t in enumerate(times)]
                + [(hold + times[-1] + 1.3, "C02", 1.0), (hold + g["dur"] - 4.6, "C03", 1.0)]
                + steps(hold, hold + g["dur"] - 0.5, 1.7),
                hall, glitches=cut_in))
    # the corner office
    add(Segment("15_enter", SHOT_LEN["g_enter"] / FPS, seq("g_enter", 112, bright=1.2), "cam",
                [(5.0, "O01", 1.0)] + steps(0, 10.5, 1.5), bed(0.012, 0.008, 0.01, "drone_low", 0.12)))
    add(Segment("16_tv", 6, still("g_tv", 124, 0.9, 4), "cam", [(1.0, "O02", 1.0)],
                bed(0.012, 0.0, 0.01, "drone_low", 0.18), af=[0.9]))
    add(Segment("17_turn", SHOT_LEN["g_turn"] / FPS, seq("g_turn", 130, bright=1.2), "cam",
                [(2.2, "O03", 1.0), (4.2, "O04", 1.0)], bed(0.012, 0.006, 0.01)))
    # walking back
    back = flicker(151, 0.5, "g_back_lit", "g_back_dim", quiet=[(0, 6.5)])
    add(Segment("17b_back", 16, still_frames(back, DATE, T0 + 150, shake=1.1, seed=6), "cam",
                [(0.4, "B01", 1.0), (3.0, "B02", 1.0), (10.5, "B03", 1.0)] + steps(0, 15, 1.6),
                bed(0.012, 0.014, 0.006, buzz_gate=gate_from_schedule(back, "g_back_lit")), glitches=cut_in))
    # sign-off at the elevator
    add(Segment("18_hold", 16, still("g_hold", 190, 0.0, 5), "cam",
                [(0.0, "drop", 0.35), (0.4, "Z01", 1.0), (3.6, "Z02", 1.0), (13.2, "Z03", 1.0)],
                hall, glitches=[(0, 0.4, 0.9)]))
    add(Segment("19_close", SHOT_LEN["g_close"] / FPS, seq("g_close", 206), "cam",
                [(0.9, "elev_doors", 0.8), (1.35, "stinger_big", 0.9)], hall, glitches=[(3.6, 0.4, 1.0)]))
    # the tape keeps running
    add(Segment("19b_dark", 3.0, lambda i, t: B.Image.new("RGB", (B.W, B.H)), "cam", [], bed(0.014, 0.0, 0.012)))
    night = flicker(211, 0.35, "g_night_a", "g_night_b")
    night_t0 = 2 * 3600 + 11 * 60 + 4
    add(Segment("19c_night", 26, still_frames(night, "MAR. 15 1996", night_t0, shake=0.0, seed=7), "cam",
                [(0.0, "ding", 0.5), (0.4, "elev_doors", 0.7), (6.0, "K01", 1.0), (20.0, "knock_inside", 0.35)],
                bed(0.014, 0.006, 0.01, "drone_low", 0.2, buzz_gate=gate_from_schedule(night, "g_night_a")),
                glitches=[(0, 0.5, 1.0), (25.5, 0.5, 1.0)]))
    add(Segment("20_static", 1.2, static_frames(13), "clean", [(0, "static", 0.7)], damage=False))
    add(Segment("21_stop", 3.0, blue_frames("STOP ■", 0.3), "clean", [(0.2, "vcr", 0.6)], bed(0.004), damage=False))

    def end_card(name, lines, dur):
        return Segment(name, dur, card_frames(lines, 21, typed=False, align="center", fade=1.0, dur=dur, fontpath=SERIF),
                       "card", [], bed(0.006, drone="drone_low", drone_g=0.25), damage=False)
    add(end_card("30_end1", ["Coulee Commercial Realty has no record", "of an agent named Gary Lindqvist."], 8))
    add(end_card("31_end2", ["The telephone number given on the tape", "was disconnected in 1971."], 8))
    add(end_card("32_end3", ["The building received no offers."], 6))
    add(end_card("33_end4", ["there are nine offices on the third floor."], 5))
    add(Segment("34_title", 5.0, card_frames(["SPACE AVAILABLE"], 30, typed=False, align="center", fade=1.2, dur=5.0,
                                             fontpath=SERIF), "card", [(0.0, "knock_final", 0.5)], bed(0.004), damage=False))
    return S
