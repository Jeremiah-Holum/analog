# Posting THE THIRD FLOOR on YouTube

- **Video:** `renders/the_third_floor_youtube.mp4`. Upload this one, not `renders/the_third_floor.mp4`
  (that's the small phone copy). It's 1440×1080, 4:3. YouTube shows it pillarboxed, which suits the VHS look.
- **Thumbnail:** `renders/thumbnails/F_floor_dark_upright.png` (others in `renders/thumbnails/`)

## Title

> THE THIRD FLOOR | Found Footage (1994)

Alternatives: *"Do not count the doors."* · *The Brenner Mutual Tapes* · *THE THIRD FLOOR [ANALOG HORROR]*

## Channel

- **Name:** VHS-C 14 (handle: @vhsc14)
- **Icon:** `renders/channel/icon_A_14.png` (options B and C in the same folder)

## Description (cryptic version, recommended)

```
COULEE COUNTY SHERIFF'S DEPARTMENT
EVIDENCE 14-A THROUGH 14-D

Four (4) VHS-C cassettes recovered from the security desk of the
Brenner Mutual Insurance building, November 11, 1994.

Nothing has been removed.

there are nine offices on the third floor.

00:00 ▮
00:30 14-A
02:30 14-B
03:46 14-C
04:29 71-117
05:14 14-D
07:03 ▮

—

This is a work of fiction. Voices are synthetic (AI text-to-speech).
Voice: LibriTTS-R (Koizumi et al., 2023), CC BY 4.0, from LibriVox recordings.
Shout: RAVDESS (Livingstone & Russo, 2018), CC BY-NC-SA 4.0.

#analoghorror #foundfootage #vhs
```

## Description (plain version)

```
In November 1994, night security officer Dale Kessler disappeared from the Brenner Mutual
Insurance building. Four VHS-C tapes were recovered from his desk.

If you count more than nine, do not continue.

00:00 Evidence
00:30 Tape 1 – Nov. 3
02:30 Tape 2 – Nov. 7
03:46 Tape 3 – Building cameras
04:29 Facilities notice
05:14 Tape 4 – Nov. 9
07:03 End

This is a work of fiction. All characters, places and events are invented.

Made with Blender, Python and FFmpeg. Voices are synthetic (AI text-to-speech).
Voice reference: LibriTTS-R (Koizumi et al., 2023), CC BY 4.0, derived from LibriVox recordings.
Shout reference: RAVDESS (Livingstone & Russo, 2018), CC BY-NC-SA 4.0.

#analoghorror #foundfootage #horror #vhs #liminalspaces
```

The chapter times are computed from the edit (`film/build.py`). YouTube only shows chapters if the
first one is `00:00` and each chapter is at least 10 seconds long, and these are.

## Tags

analog horror, found footage, vhs horror, liminal space, backrooms, office horror, short horror film,
creepypasta, 1994, security camera, lost tape, horror short

## Settings

- **Altered or synthetic content:** answer **Yes**. The voices are AI-generated, and the film is
  presented as realistic "recovered footage", which is what YouTube's disclosure rule covers. The
  label is small and doesn't hurt reach. Leaving it off when it applies can get the video flagged.
- **Audience:** "No, it's not made for kids."
- **Age restriction:** not required (no gore), but optional for a horror film.
- **Category:** Film & Animation.

## Licensing, if you monetize

The one yelled line (Tape 2, "Hey! Hey! This floor's closed!") was performed from RAVDESS, which
is **non-commercial**. Before turning on ads:

- replace that line with a real recording of your own, or
- regenerate it without the RAVDESS reference (`film/script.py` → set `F02` to style `dale`), then
  rebuild with `python3 film/build.py`.

Everything else is fine for commercial use: the LibriTTS-R voice (CC BY 4.0, credited above),
Chatterbox (MIT), Kokoro (Apache-2.0), and the renders and sound effects made for this project.

---

# ITEM 15: SPACE AVAILABLE

- **Video:** `renders/item15_youtube.mp4` (4:26). **Thumbnail:** `renders/thumbnails/item15_panel.png`
- **Title:** `ITEM 15` (alternatives: *space available*, *priced to move*, *555-0141*)

```
COULEE COUNTY SHERIFF'S DEPARTMENT
EVIDENCE ITEM 15

One (1) VHS cassette recovered from the offices of Coulee Commercial
Realty, April 2, 1996. Found in a drawer labeled "BRENNER - DO NOT SHOW".

space available.

—

This is a work of fiction. Voices are synthetic (AI text-to-speech).
Voice: LibriTTS-R (Koizumi et al., 2023), CC BY 4.0, from LibriVox recordings.
Sound effects: Freesound contributors, CC0.

#analoghorror #foundfootage #vhs
```

ITEM 15 contains no RAVDESS audio, so it's clear for monetization.
