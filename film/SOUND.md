# Sound effects

Every sound effect in the films (knocks, footsteps, elevator, tape machine, camera handling, room tone)
is a real recording from [Freesound](https://freesound.org), obtained through the
[freesound-laion-640k](https://huggingface.co/datasets/benjamin-paine/freesound-laion-640k) dataset.
All are **CC0 (public domain)**: free for any use, including commercial, with no attribution required.
They're credited here anyway.

`film/realsfx.py` cuts and processes them (splitting single knocks and steps, muffling knocks heard through
a door, softening footsteps for carpet, looping the background layers). `film/build.py` loops the three
`bed_*` recordings under every scene. Only the low drones and the stingers are still synthesized
(`film/sfx.py`); they're the score, not sound effects.

| Used as | Freesound recording | By |
|---|---|---|
| `knock_guard` | [Knocking five times](https://freesound.org/s/412856/) | SoundsForHim |
| `knock_inside, knock_final` | [Heavy Knocking](https://freesound.org/s/592999/) | JalynCatbtg |
| `step, step2, step_heavy` | [Indoor Footsteps](https://freesound.org/s/415301/) | Yin_Yang_Jake007 |
| `ding` | [Elevator Ping 01](https://freesound.org/s/459349/) | MATRIXXX_ |
| `elev_doors` | [Elevator Approach and Doors Opening](https://freesound.org/s/439420/) | maxmaxmaxmaxmaxmaxmax |
| `vcr` | [tapedeck load](https://freesound.org/s/623659/) | strangehorizon |
| `vcr` | [Sony Vintage Casette Player Button Snap 1 1](https://freesound.org/s/477684/) | Joao_Janz |
| `vcr_eject` | [Cassette Player Ejecting](https://freesound.org/s/154756/) | jpkweli |
| `handle` | [Clothes Rustling Movement 12 7](https://freesound.org/s/493338/) | Joao_Janz |
| `drop` | [Falling Object - 5](https://freesound.org/s/483660/) | SpaceJoe |
| `drag` | [Dragging a body across a concrete floor 2](https://freesound.org/s/578493/) | PostProdDog |
| `button` | [button press](https://freesound.org/s/560549/) | Zanci19 |
| `bed_fluoro` | [Fluorescent Light Hum](https://freesound.org/s/383657/) | deleted_user_7146007 |
| `bed_room` | [drone natural tunnel office building ventilation bass1](https://freesound.org/s/452222/) | kyles |
| `bed_vhs` | [HUM (71)](https://freesound.org/s/531330/) | DefySolipsis |
